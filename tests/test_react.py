# -*- coding: utf-8 -*-
"""M3 测试：ReAct 循环 / 变量传递 / 失败自愈 / 护栏 / 停止 / checkpoint。

运行： python3 -m pytest tests/ -q
全部用注入 transport mock，不依赖 API Key 或网络。
"""
import sys
import threading
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.tools.registry import ToolSpec
from core.tools.builtins import build_registry
from core.agent.react import ReActRunner, ReactConfig
from core.agent.tool_loop import ToolTrace

CFG = {"enabled": True, "base_url": "https://api.example.com/v1", "api_key": "k", "model": "m"}


def _tc(name, args, call_id="c"):
    return {"id": call_id, "function": {"name": name,
            "arguments": __import__("json").dumps(args, ensure_ascii=False)}}


def _resp_text(text):
    return {"choices": [{"message": {"content": text, "tool_calls": []}}]}


def _resp_calls(calls, content=None):
    return {"choices": [{"message": {"content": content, "tool_calls": calls}}]}


def test_react_config_defaults():
    rc = ReactConfig()
    assert rc.max_steps == 12 and rc.max_tool_calls == 24 and rc.budget_chars > 0


# ---------- 多轮循环 ----------
def test_react_two_rounds_then_answer():
    """第 1 轮搜索、第 2 轮写作、第 3 轮给答案——至少 2 次工具调用。"""
    reg = build_registry({
        "search": lambda a: {"ok": True, "data": "竞品A价格99", "error": None},
        "write": lambda a: {"ok": True, "data": "表格已生成", "error": None},
    })
    n = {"i": 0}
    def transport(messages, tools, cfg):
        n["i"] += 1
        if n["i"] == 1:
            return _resp_calls([_tc("search", {"query": "竞品A"}, "c1")])
        if n["i"] == 2:
            return _resp_calls([_tc("write", {"prompt": "整理成表格"}, "c2")])
        return _resp_text("最终表格：竞品A 99元")

    r = ReActRunner("调研竞品", reg, CFG, transport=transport).run()
    assert r.reason == "done"
    assert len(r.traces) == 2
    assert "99" in r.reply


def test_react_variables_observable():
    """步骤2的观察里能看到步骤1的结果（变量传递的物理基础）。"""
    reg = build_registry({
        "search": lambda a: {"ok": True, "data": "SECRET_VALUE_42", "error": None},
        "write": lambda a: {"ok": True, "data": "ok", "error": None},
    })
    seen = {}
    n = {"i": 0}
    def transport(messages, tools, cfg):
        n["i"] += 1
        if n["i"] == 2:
            seen["ctx"] = "\n".join(m.get("content", "") for m in messages)
            return _resp_calls([_tc("write", {"prompt": "x"}, "c2")])
        if n["i"] == 1:
            return _resp_calls([_tc("search", {"query": "x"}, "c1")])
        return _resp_text("done")

    runner = ReActRunner("t", reg, CFG, transport=transport)
    runner.run()
    assert "SECRET_VALUE_42" in seen["ctx"]


# ---------- 失败自愈 ----------
def test_react_failure_self_heal():
    """search 失败 → 错误回填 → 模型改用 doc 工具。"""
    reg = build_registry({
        "search": lambda a: {"ok": False, "data": None, "error": "网络不可达"},
        "doc": lambda a: {"ok": True, "data": "来自文档的答案", "error": None},
    })
    n = {"i": 0}
    def transport(messages, tools, cfg):
        n["i"] += 1
        if n["i"] == 1:
            return _resp_calls([_tc("search", {"query": "x"}, "c1")])
        if n["i"] == 2:
            tool_msgs = [m for m in messages if m.get("role") == "tool"]
            assert any("网络不可达" in m.get("content", "") for m in tool_msgs)
            return _resp_calls([_tc("doc", {"query": "x"}, "c2")])
        return _resp_text("根据文档：答案是……")

    r = ReActRunner("t", reg, CFG, transport=transport).run()
    assert "根据文档" in r.reply
    assert r.traces[0]["ok"] is False and r.traces[1]["ok"] is True


# ---------- 护栏 ----------
def test_react_max_steps_guard():
    """模型一直调工具 → max_steps 触发停止。"""
    reg = build_registry({"search": lambda a: {"ok": True, "data": "x", "error": None}})
    def transport(messages, tools, cfg):
        return _resp_calls([_tc("search", {"query": "again"}, "c")])
    rc = ReactConfig(max_steps=3, max_tool_calls=100)
    r = ReActRunner("t", reg, CFG, transport=transport, react_cfg=rc).run()
    assert len(r.traces) <= 3
    assert r.reason in ("max_steps", "done")


def test_react_repeat_detection():
    """相同调用重复出现被检测为失败。"""
    reg = build_registry({"search": lambda a: {"ok": True, "data": "x", "error": None}})
    def transport(messages, tools, cfg):
        return _resp_calls([_tc("search", {"query": "same"}, "c")])
    r = ReActRunner("t", reg, CFG, transport=transport,
                    react_cfg=ReactConfig(max_steps=6)).run()
    assert any(t["ok"] is False and t.get("error") and "重复" in t["error"] for t in r.traces)


# ---------- 停止 ----------
def test_react_stop_event():
    """stop_event 置位后循环终止。"""
    reg = build_registry({"search": lambda a: {"ok": True, "data": "x", "error": None}})
    stop = threading.Event()
    def transport(messages, tools, cfg):
        stop.set()   # 第一次调用后立即请求停止
        return _resp_calls([_tc("search", {"query": "x"}, "c")])
    r = ReActRunner("t", reg, CFG, transport=transport, stop_event=stop).run()
    assert r.reason == "stopped" or r.stopped


# ---------- checkpoint ----------
def test_react_checkpoint_snapshot():
    reg = build_registry({"search": lambda a: {"ok": True, "data": "x", "error": None}})
    n = {"i": 0}
    def transport(messages, tools, cfg):
        n["i"] += 1
        return _resp_calls([_tc("search", {"query": "x"}, "c")]) if n["i"] == 1 else _resp_text("done")
    runner = ReActRunner("t", reg, CFG, transport=transport)
    runner.run()
    snap = runner.snapshot()
    assert snap["goal"] == "t"
    assert "observations" in snap and "steps_done" in snap
    assert len(snap["steps_done"]) == 1


def test_react_resume_from_checkpoint():
    """从 checkpoint 恢复时，已完成的观察被带入上下文，不重复执行。"""
    reg = build_registry({"write": lambda a: {"ok": True, "data": "y", "error": None}})
    ckpt = {"observations": [{"tool": "search", "args": {"query": "x"},
                              "ok": True, "result": "PREVIOUS_RESULT"}],
            "steps_done": [{"step": 1, "tool": "search"}]}
    seen = {}
    def transport(messages, tools, cfg):
        seen["ctx"] = "\n".join(m.get("content", "") for m in messages)
        return _resp_text("resumed answer")
    runner = ReActRunner("t2", reg, CFG, transport=transport, checkpoint=ckpt)
    r = runner.run()
    assert "PREVIOUS_RESULT" in seen["ctx"]
    assert "resumed" in r.reply


# ---------- 事件 ----------
def test_react_emits_events():
    reg = build_registry({"search": lambda a: {"ok": True, "data": "x", "error": None}})
    events = []
    n = {"i": 0}
    def transport(messages, tools, cfg):
        n["i"] += 1
        return _resp_calls([_tc("search", {"query": "x"}, "c")]) if n["i"] == 1 else _resp_text("done")
    ReActRunner("t", reg, CFG, transport=transport,
                on_event=lambda e: events.append(e["type"])).run()
    for t in ("plan_update", "tool_call", "tool_result", "done"):
        assert t in events, t


def test_react_no_llm_fallback():
    reg = build_registry({})
    r = ReActRunner("t", reg, None,
                    fallback_fn=lambda s: ("write", "本地兜底结果")).run()
    assert r.used_llm is False and "本地兜底结果" in r.reply


# ---------- app 接入 ----------
def test_agent_stream_routes_exist():
    import importlib
    app = importlib.import_module("app")
    rules = [r.rule for r in app.app.url_map.iter_rules()]
    assert "/api/agent_stream" in rules and "/api/agent/stop" in rules


def test_agent_v2_react_default(monkeypatch):
    """M3 默认启用 ReAct，返回结果含 reason/steps/checkpoint。"""
    import importlib
    app = importlib.import_module("app")
    monkeypatch.setitem(app.config["agent"], "use_react", True)
    monkeypatch.setitem(app.config["llm"], "enabled", False)  # 无 LLM → no_llm 分支
    res = app.agent_run_v2("目标", ["步骤"])
    assert "reason" in res and "checkpoint" in res
    assert res["reason"] == "no_llm"


def test_done_event_carries_reply():
    """done 事件必须携带最终 reply——前端据此渲染，避免二次执行 Agent（写操作会重复）。"""
    reg = build_registry({"search": lambda a: {"ok": True, "data": "x", "error": None}})
    events = []
    n = {"i": 0}
    def transport(messages, tools, cfg):
        n["i"] += 1
        return _resp_calls([_tc("search", {"query": "x"}, "c")]) if n["i"] == 1 else _resp_text("最终交付物")
    res = ReActRunner("t", reg, CFG, transport=transport,
                      on_event=lambda e: events.append(e)).run()
    done = [e for e in events if e["type"] == "done"]
    assert len(done) == 1
    assert done[0].get("reply") == res.reply == "最终交付物"


def test_done_event_no_llm_carries_reply():
    """无 LLM 兜底分支的 done 事件同样要带 reply。"""
    events = []
    res = ReActRunner("t", build_registry({}), None,
                      fallback_fn=lambda s: ("write", "本地兜底"),
                      on_event=lambda e: events.append(e)).run()
    done = [e for e in events if e["type"] == "done"][0]
    assert done.get("reply") == res.reply and "本地兜底" in done["reply"]
