# -*- coding: utf-8 -*-
"""Agent 单轮工具循环（M2）。

流程：step → 模型发 tool_calls → 执行工具 → 结果回填 → 模型据结果作答。
任何一环失败都降级到关键词兜底，保证本地模型/无 LLM 时不崩。

M3 扩展点：把 for-step 换成 while-not-done，本文件的函数签名与返回结构保持不变。
"""
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from typing import Callable, List, Optional

from ..tools.adapter import (
    call_tools_llm, build_tool_messages, assistant_message, parse_tool_calls,
)


@dataclass
class ToolTrace:
    """一次工具调用的审计记录（M5 审计日志直接复用）。"""
    name: str
    arguments: dict = field(default_factory=dict)
    ok: bool = False
    error: Optional[str] = None
    elapsed: float = 0.0
    source: str = "tool_calls"   # tool_calls | fallback

    def to_dict(self):
        return {
            "name": self.name, "arguments": self.arguments, "ok": self.ok,
            "error": self.error, "elapsed": round(self.elapsed, 3), "source": self.source,
        }


def _run_one(spec, args):
    """执行单个工具，统一吞异常成结构化错误。"""
    import time
    t0 = time.time()
    name = spec.name
    try:
        if spec.run is None:
            return {"ok": False, "data": None, "error": f"工具 {name} 无可用实现"}, time.time() - t0
        res = spec.run(args or {})
        if not isinstance(res, dict) or "ok" not in res:
            res = {"ok": True, "data": res, "error": None}
        return res, time.time() - t0
    except Exception as e:
        return {"ok": False, "data": None, "error": f"{type(e).__name__}: {e}"}, time.time() - t0


def _execute_with_timeout(spec, args, timeout):
    """带超时的工具执行。超时返回结构化错误（线程为 daemon，不阻塞主流程退出）。"""
    import time
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=1) as ex:
        fut = ex.submit(_run_one, spec, args)
        try:
            res, _ = fut.result(timeout=timeout)
            return res, time.time() - t0
        except FutureTimeout:
            return {"ok": False, "data": None, "error": f"工具 {spec.name} 执行超时（>{timeout}s）"}, time.time() - t0
        except Exception as e:
            return {"ok": False, "data": None, "error": str(e)}, time.time() - t0


def _to_text(data):
    if data is None:
        return ""
    if isinstance(data, str):
        return data
    import json
    try:
        return json.dumps(data, ensure_ascii=False)
    except Exception:
        return str(data)


def run_agent(goal, steps, *, registry, cfg, transport=None,
              fallback_fn=None, synthesize_fn=None, max_rounds=1) -> dict:
    """执行 Agent 任务，返回 {reply, mode, tool_trace}。

    registry   : Registry 实例（tool_loop 只依赖它，不依赖 app）
    cfg        : LLM 配置 dict；None/不可用 → 全程走兜底
    transport  : 可注入的 LLM transport（测试用）；None 用默认 HTTP
    fallback_fn: Callable[[step_text], (tool_name, out)]，关键词兜底
    synthesize_fn: Callable[[goal, collected], str|None]，最终合成（可选）
    max_rounds : M2 固定 1；M3 放开为多轮
    """
    traces: List[ToolTrace] = []
    collected = []   # (tool_name, step, out_text)
    steps = list(steps) if steps else [goal]
    can_llm = bool(cfg and cfg.get("enabled"))

    def _text_result(step_text):
        """兜底：关键词选工具并执行。"""
        if fallback_fn is None:
            return None
        try:
            name, out = fallback_fn(step_text)
        except Exception as e:
            return f"[兜底执行失败] {e}"
        if name:
            traces.append(ToolTrace(name=name, arguments={"_step": step_text[:200]},
                                    ok=True, source="fallback"))
        return _to_text(out)

    for step in steps:
        answer = None
        if can_llm:
            messages = [
                {"role": "system", "content":
                 "你是墨核 Agent。可用工具完成任务：优先调用 tool_calls 获取真实数据，"
                 "工具返回的结果是可信事实。拿不准时先调工具再回答，不要编造。"},
                {"role": "user", "content": f"目标：{goal}\n当前步骤：{step}"},
            ]
            r = call_tools_llm(messages, registry.specs(), cfg, transport=transport)
            if r and r.get("tool_calls"):
                calls = r["tool_calls"]
                results = []
                for call in calls:
                    if call.get("_parse_error"):
                        results.append({"ok": False, "data": None, "error": call["_parse_error"]})
                        traces.append(ToolTrace(name=call.get("name", "?"),
                                                arguments={}, ok=False,
                                                error=call["_parse_error"], source="tool_calls"))
                        continue
                    spec = registry.get(call["name"])
                    if spec is None:
                        err = f"未知工具：{call['name']}"
                        results.append({"ok": False, "data": None, "error": err})
                        traces.append(ToolTrace(name=call["name"], arguments=call["arguments"],
                                                ok=False, error=err, source="tool_calls"))
                        continue
                    res, elapsed = _execute_with_timeout(spec, call["arguments"], spec.timeout)
                    results.append(res)
                    traces.append(ToolTrace(name=spec.name, arguments=call["arguments"],
                                            ok=bool(res.get("ok")), error=res.get("error"),
                                            elapsed=elapsed, source="tool_calls"))
                    collected.append((spec.name, step, _to_text(res.get("data")) if res.get("ok") else ""))
                # 工具结果回填 → 再让模型据结果作答
                messages.append(assistant_message(r.get("text"), calls))
                messages.extend(build_tool_messages(calls, results))
                final = call_tools_llm(messages, [], cfg, transport=transport)
                if final and final.get("text") and not final.get("tool_calls"):
                    answer = final["text"]
            elif r and r.get("text") and not r.get("tool_calls"):
                # 模型判断无需工具，直接作答
                answer = r["text"]
        if answer is None:
            answer = _text_result(step)
        if answer:
            collected.append(("answer", step, answer))

    reply = ""
    if synthesize_fn and can_llm and collected:
        try:
            synth = synthesize_fn(goal, collected)
            if synth:
                reply = synth
        except Exception:
            reply = ""
    if not reply:
        # 无合成时，把各步骤答案按序拼接成可读交付物
        parts = []
        for name, step, out in collected:
            if name == "answer" and out:
                parts.append(out)
        reply = "\n\n".join(parts) if parts else "[Agent] 未能产生结果，请检查模型配置或换个说法。"

    return {
        "reply": reply,
        "mode": "agent",
        "tool_trace": [t.to_dict() for t in traces],
        "tool_calls_count": len(traces),
        "used_llm": can_llm,
    }
