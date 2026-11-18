# -*- coding: utf-8 -*-
"""M3 ReAct 内核：plan → act → observe → replan 循环。

与 M2 单轮（tool_loop.run_agent）的区别：
- M2：预先给定 steps，线性执行，每步最多一次「工具→作答」。
- M3：只给 goal，模型自己决定下一步调什么工具、何时结束；每轮观察回填，
      下一步可引用之前的输出（变量表）；失败自动换工具；可中断、可续跑。

设计约束：
- 不 import app.py；registry / cfg / transport / fallback 全部注入。
- 通过 on_event 回调推送 SSE 事件（plan_update / tool_call / tool_result / error / done）。
- 通过 stop_event 支持 1 秒内停止。
- checkpoint 由外部持久化（本模块产出可 JSON 化的快照）。
"""
import json
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from ..tools.adapter import (
    call_tools_llm, build_tool_messages, assistant_message,
)
from .tool_loop import ToolTrace, _execute_with_timeout, _to_text


SYSTEM_REACT = (
    "你是墨核 Agent，用 ReAct 方式完成任务：先想再动手，可用工具获取真实信息。"
    "规则：\n"
    "1. 每次可调用一个或多个工具；工具返回的是可信事实。\n"
    "2. 若某工具失败，换一个工具或改参数重试，不要直接放弃。\n"
    "3. 需要引用之前结果时，直接写进参数或最终答案。\n"
    "4. 信息足够、任务完成时，不要调用工具，直接给出最终交付物（条理清晰、可直接使用）。\n"
    "5. 不要编造工具没返回的数据。"
)


@dataclass
class ReactConfig:
    max_steps: int = 12          # 最多执行步数（工具调用轮次）
    max_tool_calls: int = 24     # 最多工具调用总数
    budget_chars: int = 60000    # 观察表总字符预算
    repeat_window: int = 3       # 检测重复调用的窗口


@dataclass
class ReactResult:
    reply: str
    traces: List[dict] = field(default_factory=list)
    steps: List[dict] = field(default_factory=list)
    stopped: bool = False
    used_llm: bool = True
    reason: str = "done"         # done | max_steps | stopped | no_llm


class ReActRunner:
    """一次可中断、可观测、可恢复的 ReAct 运行。"""

    def __init__(self, goal, registry, cfg, *, transport=None, fallback_fn=None,
                 synthesize_fn=None, react_cfg=None, on_event=None,
                 stop_event=None, checkpoint=None):
        self.goal = goal
        self.registry = registry
        self.cfg = cfg
        self.transport = transport
        self.fallback_fn = fallback_fn
        self.synthesize_fn = synthesize_fn
        self.rc = react_cfg or ReactConfig()
        self.on_event = on_event or (lambda ev: None)
        self.stop_event = stop_event or threading.Event()
        self.can_llm = bool(cfg and cfg.get("enabled"))
        # 恢复：从 checkpoint 载入已完成的步骤/观察/调用记录
        self.observations: List[dict] = checkpoint.get("observations", []) if checkpoint else []
        self.traces: List[ToolTrace] = []
        self.steps_done: List[dict] = checkpoint.get("steps_done", []) if checkpoint else []
        self._seen_calls: List[str] = []

    # ---------- 事件 ----------
    def _emit(self, typ, **kw):
        try:
            self.on_event({"type": typ, **kw})
        except Exception:
            pass

    # ---------- 观察表 → 变量上下文 ----------
    def _context_text(self):
        """把已积累的观察压缩成一段可引用的上下文（带预算上限）。"""
        if not self.observations:
            return ""
        lines = ["以下是已完成步骤的可信观察结果，后续步骤可引用："]
        total = 0
        kept = []
        for o in reversed(self.observations):
            seg = f"[{o['tool']}] {str(o['result'])[:1200]}"
            if total + len(seg) > self.rc.budget_chars:
                break
            kept.append(seg)
            total += len(seg)
        return "\n".join(lines + list(reversed(kept)))

    # ---------- 重复调用检测 ----------
    def _is_repeat(self, name, args):
        key = f"{name}:{json.dumps(args, ensure_ascii=False, sort_keys=True)}"
        recent = self._seen_calls[-self.rc.repeat_window:]
        self._seen_calls.append(key)
        return recent.count(key) >= 2   # 窗口内出现 2 次以上视为重复

    # ---------- 执行单个工具 ----------
    def _call_tool(self, name, args):
        spec = self.registry.get(name)
        if spec is None:
            return {"ok": False, "data": None, "error": f"未知工具：{name}"}, 0.0
        if self._is_repeat(name, args):
            return {"ok": False, "data": None, "error": f"检测到重复调用 {name}，请换工具或改参数"}, 0.0
        res, elapsed = _execute_with_timeout(spec, args, spec.timeout)
        return res, elapsed

    # ---------- 兜底（无 LLM / 不支持 tool_calls） ----------
    def _fallback_step(self, step_text):
        if self.fallback_fn is None:
            return None
        try:
            name, out = self.fallback_fn(step_text)
        except Exception as e:
            return f"[兜底失败] {e}"
        return _to_text(out)

    # ---------- 主循环 ----------
    def run(self) -> ReactResult:
        if not self.can_llm:
            # 无 LLM：用预置步骤（若有）走关键词兜底，行为对齐 M2
            answer = self._fallback_step(self.goal)
            final_reply = answer or "[Agent] 未配置模型且无可用步骤。"
            self._emit("done", reason="no_llm", tool_calls=0, reply=final_reply)
            return ReactResult(reply=final_reply,
                               used_llm=False, reason="no_llm")

        messages = [
            {"role": "system", "content": SYSTEM_REACT},
            {"role": "user", "content": f"目标：{self.goal}"},
        ]
        final_answer = None
        reason = "done"

        for step_idx in range(self.rc.max_steps):
            if self.stop_event.is_set():
                reason = "stopped"
                break
            self._emit("plan_update", step=step_idx + 1, max_steps=self.rc.max_steps,
                       goal=self.goal)

            # 注入当前观察上下文（作为新的 user 消息，不篡改历史）
            ctx = self._context_text()
            turn_messages = list(messages)
            if ctx:
                turn_messages.append({"role": "user", "content": ctx})

            r = call_tools_llm(turn_messages, self.registry.specs(), self.cfg,
                               transport=self.transport)

            if r is None or not r.get("tool_calls"):
                # 无工具调用：模型给出最终答案（或不可用 → 兜底）
                if r and r.get("text"):
                    final_answer = r["text"]
                    break
                final = self._fallback_step(self.goal)
                final_answer = final or "[Agent] 模型未返回可用结果。"
                reason = "fallback"
                break

            calls = r["tool_calls"]
            if len(self.traces) + len(calls) > self.rc.max_tool_calls:
                reason = "max_steps"
                break

            # 执行本轮所有工具调用
            results = []
            messages.append(assistant_message(r.get("text"), calls))
            for call in calls:
                if self.stop_event.is_set():
                    reason = "stopped"
                    break
                if call.get("_parse_error"):
                    res = {"ok": False, "data": None, "error": call["_parse_error"]}
                    elapsed = 0.0
                    name, args = call.get("name", "?"), {}
                else:
                    name, args = call["name"], call["arguments"]
                    self._emit("tool_call", name=name, arguments=args)
                    res, elapsed = self._call_tool(name, args)
                results.append(res)
                t = ToolTrace(name=name, arguments=args, ok=bool(res.get("ok")),
                              error=res.get("error"), elapsed=elapsed, source="tool_calls")
                self.traces.append(t)
                self._emit("tool_result", name=name, ok=bool(res.get("ok")),
                           error=res.get("error"), data=_to_text(res.get("data"))[:2000])
                self.observations.append({
                    "tool": name,
                    "args": args,
                    "ok": bool(res.get("ok")),
                    "result": _to_text(res.get("data")) if res.get("ok") else f"失败：{res.get('error')}",
                })
                self.steps_done.append({
                    "step": step_idx + 1, "tool": name, "arguments": args,
                    "ok": bool(res.get("ok")), "result": _to_text(res.get("data"))[:2000],
                })
            if reason == "stopped":
                break

            # 结果（含错误）回填，让模型决定下一步或自愈
            messages.extend(build_tool_messages(calls, results))

        else:
            reason = "max_steps"

        # 到达步数上限仍没答案：让模型基于观察做一次总结
        if final_answer is None and self.observations:
            final = call_tools_llm(
                messages + [{"role": "user", "content": "已达到步数上限，请基于已有结果给出最终交付物。"}],
                [], self.cfg, transport=self.transport,
            )
            if final and final.get("text"):
                final_answer = final["text"]

        if self.synthesize_fn and final_answer:
            try:
                synth = self.synthesize_fn(self.goal, [(t.name, self.goal, _to_text(t.arguments)) for t in self.traces])
                if synth:
                    final_answer = synth
            except Exception:
                pass

        final_reply = final_answer or "[Agent] 未能产生结果，请检查模型配置或换个说法。"
        self._emit("done", reason=reason, tool_calls=len(self.traces), reply=final_reply)
        return ReactResult(
            reply=final_reply,
            traces=[t.to_dict() for t in self.traces],
            steps=self.steps_done,
            stopped=(reason == "stopped"),
            used_llm=True,
            reason=reason,
        )

    # ---------- checkpoint 快照 ----------
    def snapshot(self):
        """产出可 JSON 化的快照，供中断后续跑（跳过已完成步骤）。"""
        return {
            "goal": self.goal,
            "observations": self.observations,
            "steps_done": self.steps_done,
            "trace_count": len(self.traces),
        }
