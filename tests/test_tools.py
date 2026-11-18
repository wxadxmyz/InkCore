# -*- coding: utf-8 -*-
"""M2 测试：Tool Registry / 协议适配 / 安全护栏 / 错误契约 / Agent 兜底。

运行： python3 -m pytest tests/ -q
所有用例均为纯本地逻辑，不依赖 API Key 或外部网络（LLM 调用全部用注入 transport mock）。
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.tools.registry import Registry, ToolSpec
from core.tools.builtins import build_registry, TOOL_DEFS
from core.tools import adapter
from core.security.guard import assert_path, safe_subpath
from core.agent.tool_loop import run_agent, ToolTrace


# ---------- Registry ----------
def test_tool_defs_count():
    assert len(TOOL_DEFS) == 13


def test_tool_defs_unique_names():
    names = [d.name for d in TOOL_DEFS]
    assert len(names) == len(set(names))


def test_expected_tools_present():
    names = {d.name for d in TOOL_DEFS}
    assert {"search", "image", "code", "terminal", "doc", "write",
            "read_file", "write_file", "edit_file", "glob", "grep",
            "list_dir", "http_fetch"}.issubset(names)


def test_build_registry_skips_missing_impls():
    reg = build_registry({"grep": lambda a: {"ok": True, "data": "", "error": None}})
    assert len(reg) == 1
    assert "grep" in reg
    assert "search" not in reg


def test_registry_register_and_get():
    reg = Registry()
    reg.register(ToolSpec("t", "desc", {"type": "object", "properties": {}}))
    assert reg.get("t").description == "desc"
    assert len(reg) == 1


def test_registry_duplicate_raises():
    reg = Registry()
    reg.register(ToolSpec("t", "a", {}))
    with pytest.raises(ValueError):
        reg.register(ToolSpec("t", "b", {}))


def test_tool_spec_to_openai():
    spec = ToolSpec("grep", "搜索", {"type": "object", "properties": {"pattern": {"type": "string"}}, "required": ["pattern"]})
    o = spec.to_openai()
    assert o["type"] == "function"
    assert o["function"]["name"] == "grep"
    assert o["function"]["parameters"] == spec.parameters


def test_all_defs_have_schema_and_timeout():
    for d in TOOL_DEFS:
        assert d.parameters.get("type") == "object", d.name
        assert d.timeout > 0, d.name
        assert d.permission in ("read", "write", "execute"), d.name


# ---------- 协议适配 ----------
def test_to_openai_tools_from_specs():
    specs = [ToolSpec("a", "A", {"type": "object"}), ToolSpec("b", "B", {"type": "object"})]
    out = adapter.to_openai_tools(specs)
    assert [x["function"]["name"] for x in out] == ["a", "b"]


def test_parse_tool_calls_ok():
    msg = {"tool_calls": [{"id": "c1", "function": {"name": "grep", "arguments": '{"pattern":"x"}'}}]}
    calls = adapter.parse_tool_calls(msg)
    assert calls[0]["name"] == "grep"
    assert calls[0]["arguments"] == {"pattern": "x"}
    assert "_parse_error" not in calls[0]


def test_parse_tool_calls_fenced_json():
    msg = {"tool_calls": [{"id": "c1", "function": {"name": "grep", "arguments": '```json\n{"pattern":"y"}\n```'}}]}
    calls = adapter.parse_tool_calls(msg)
    assert calls[0]["arguments"] == {"pattern": "y"}


def test_parse_tool_calls_bad_json_discarded():
    msg = {"tool_calls": [{"id": "c1", "function": {"name": "grep", "arguments": "{bad"}}]}
    calls = adapter.parse_tool_calls(msg)
    assert len(calls) == 1
    assert "_parse_error" in calls[0]


def test_build_tool_messages_ok_and_error():
    calls = [{"id": "c1", "name": "grep"}, {"id": "c2", "name": "read_file"}]
    results = [{"ok": True, "data": "line1"}, {"ok": False, "error": "路径越界"}]
    msgs = adapter.build_tool_messages(calls, results)
    assert msgs[0]["role"] == "tool" and msgs[0]["content"] == "line1"
    assert "失败" in msgs[1]["content"] and "越界" in msgs[1]["content"]


def test_assistant_message_shape():
    m = adapter.assistant_message("hi", [{"id": "c1", "name": "grep", "arguments": {"pattern": "x"}}])
    assert m["role"] == "assistant"
    assert m["tool_calls"][0]["function"]["name"] == "grep"


def test_call_tools_llm_embedded_returns_none():
    cfg = {"enabled": True, "base_url": "embedded://local", "api_key": "", "model": "x"}
    assert adapter.call_tools_llm([], [], cfg) is None


def test_call_tools_llm_via_injected_transport():
    """注入 transport：模型发 grep 调用 → 应被解析出来。"""
    cfg = {"enabled": True, "base_url": "https://api.example.com/v1", "api_key": "k", "model": "m"}
    spec = ToolSpec("grep", "g", {"type": "object", "properties": {}})

    def fake_transport(messages, tools, c):
        assert tools and tools[0]["function"]["name"] == "grep"
        return {"choices": [{"message": {"content": None, "tool_calls": [
            {"id": "c1", "function": {"name": "grep", "arguments": '{"pattern":"parse_qs"}'}}
        ]}}]}

    r = adapter.call_tools_llm([], [spec], cfg, transport=fake_transport)
    assert r["tool_calls"][0]["name"] == "grep"
    assert r["tool_calls"][0]["arguments"] == {"pattern": "parse_qs"}


# ---------- 安全护栏 ----------
def test_assert_path_within_root(tmp_path):
    root = tmp_path / "app"
    root.mkdir()
    f = root / "a.py"
    f.write_text("x")
    assert assert_path(f, [root]) == f.resolve()


def test_assert_path_rejects_escape(tmp_path):
    root = tmp_path / "app"; root.mkdir()
    outside = tmp_path / "secret.txt"; outside.write_text("x")
    with pytest.raises(ValueError):
        assert_path(outside, [root])


def test_safe_subpath_returns_none_on_escape(tmp_path):
    root = tmp_path / "app"; root.mkdir()
    assert safe_subpath(tmp_path / "b", [root]) is None


# ---------- 工程工具（通过 app 注入的实现，走统一契约） ----------
@pytest.fixture(scope="module")
def appmod():
    import importlib
    return importlib.import_module("app")


def test_tool_read_write_edit_roundtrip(appmod, tmp_path, monkeypatch):
    monkeypatch.setattr(appmod, "_TOOL_ROOTS", [tmp_path])
    p = str(tmp_path / "note.txt")
    assert appmod.tool_write_file({"path": p, "content": "hello 墨核"})["ok"] is True
    r = appmod.tool_read_file({"path": p})
    assert r["ok"] and r["data"] == "hello 墨核"
    e = appmod.tool_edit_file({"path": p, "old": "墨核", "new": "InkCore"})
    assert e["ok"] is True
    assert "InkCore" in appmod.tool_read_file({"path": p})["data"]


def test_tool_edit_not_found(appmod, tmp_path, monkeypatch):
    monkeypatch.setattr(appmod, "_TOOL_ROOTS", [tmp_path])
    p = tmp_path / "x.txt"; p.write_text("abc")
    r = appmod.tool_edit_file({"path": str(p), "old": "ZZZ", "new": "y"})
    assert r["ok"] is False and "未找到" in r["error"]


def test_tool_grep_finds_line(appmod, tmp_path, monkeypatch):
    monkeypatch.setattr(appmod, "_TOOL_ROOTS", [tmp_path])
    f = tmp_path / "code.py"; f.write_text("a=1\nparse_qs is here\nb=2\n")
    r = appmod.tool_grep({"pattern": "parse_qs", "path": str(tmp_path)})
    assert r["ok"] and "parse_qs is here" in r["data"]


def test_tool_list_dir(appmod, tmp_path, monkeypatch):
    monkeypatch.setattr(appmod, "_TOOL_ROOTS", [tmp_path])
    (tmp_path / "f.txt").write_text("x")
    r = appmod.tool_list_dir({"path": str(tmp_path)})
    assert r["ok"] and "f.txt" in r["data"]


def test_tool_path_escape_blocked(appmod, tmp_path, monkeypatch):
    monkeypatch.setattr(appmod, "_TOOL_ROOTS", [tmp_path / "app"])
    (tmp_path / "app").mkdir(exist_ok=True)
    r = appmod.tool_read_file({"path": str(tmp_path / "outside.txt")})
    assert r["ok"] is False and "越界" in r["error"]


def test_http_fetch_rejects_non_http(appmod):
    r = appmod.tool_http_fetch({"url": "file:///etc/passwd"})
    assert r["ok"] is False


# ---------- Agent 循环：兜底与决策 ----------
def test_run_agent_fallback_when_no_llm():
    """无 LLM 时必须走关键词兜底，不崩。"""
    reg = build_registry({"write": lambda a: {"ok": True, "data": "写好了", "error": None}})
    out = run_agent("目标", ["写一段话"], registry=reg, cfg=None,
                    fallback_fn=lambda s: ("write", "写好了"))
    assert out["mode"] == "agent"
    assert out["used_llm"] is False
    assert "写好了" in out["reply"]
    assert any(t["source"] == "fallback" for t in out["tool_trace"])


def test_run_agent_tool_calls_flow():
    """模型发 grep → 执行 → 回填 → 据结果作答，全链路用注入 transport 模拟。"""
    reg = build_registry({"grep": lambda a: {"ok": True, "data": f"发现 {a['pattern']} 在 42 行", "error": None}})
    cfg = {"enabled": True, "base_url": "https://api.example.com/v1", "api_key": "k", "model": "m"}

    state = {"n": 0}

    def fake_transport(messages, tools, c):
        state["n"] += 1
        if state["n"] == 1:
            return {"choices": [{"message": {"content": None, "tool_calls": [
                {"id": "c1", "function": {"name": "grep", "arguments": '{"pattern":"parse_qs"}'}}
            ]}}]}
        # 第二次：断言工具结果已回填，然后作答
        assert any(m.get("role") == "tool" for m in messages)
        return {"choices": [{"message": {"content": "parse_qs 未导入导致 Bug", "tool_calls": []}}]}

    out = run_agent("查 parse_qs", ["读代码找 parse_qs"], registry=reg, cfg=cfg,
                    transport=fake_transport, fallback_fn=lambda s: (None, "兜底"))
    assert "parse_qs 未导入导致 Bug" in out["reply"]
    assert state["n"] == 2
    assert any(t["name"] == "grep" and t["ok"] for t in out["tool_trace"])


def test_run_agent_tool_error_backfilled():
    """工具失败时错误信息回填给模型，模型能解释。"""
    reg = build_registry({"grep": lambda a: {"ok": False, "data": None, "error": "路径越界"}})
    cfg = {"enabled": True, "base_url": "https://api.example.com/v1", "api_key": "k", "model": "m"}
    state = {"n": 0}

    def fake_transport(messages, tools, c):
        state["n"] += 1
        if state["n"] == 1:
            return {"choices": [{"message": {"content": None, "tool_calls": [
                {"id": "c1", "function": {"name": "grep", "arguments": '{"pattern":"x"}'}}
            ]}}]}
        tool_msgs = [m for m in messages if m.get("role") == "tool"]
        assert tool_msgs and "越界" in tool_msgs[0]["content"]
        return {"choices": [{"message": {"content": "工具因越界失败，我换个办法", "tool_calls": []}}]}

    out = run_agent("t", ["s"], registry=reg, cfg=cfg, transport=fake_transport)
    assert "换个办法" in out["reply"]
    assert any(t["ok"] is False for t in out["tool_trace"])


def test_tool_trace_dataclass():
    t = ToolTrace(name="grep", ok=True, source="tool_calls")
    d = t.to_dict()
    assert d["name"] == "grep" and d["ok"] is True and d["source"] == "tool_calls"
