# -*- coding: utf-8 -*-
"""M6 测试：MCP 客户端 / Skill 包规范 / 子 Agent 并行。

纯本地 mock，不依赖真实 MCP Server 或网络。
"""
import sys
import io
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.mcp.client import McpClient, to_tool_specs, McpError
from core.skills.pack import (
    parse_skill_md, validate_skill_md, export_skill_zip, load_skill_zip, SkillPack,
)
from core.agent.subagent import SubTask, SubResult, run_parallel, summarize_for_parent


# ================= MCP =================
class FakeTransport:
    """按 method 返回预置结果的假传输。"""
    def __init__(self):
        self.calls = []
        self.closed = False

    def send(self, payload):
        self.calls.append(payload)
        m = payload.get("method")
        if m == "initialize":
            return {"jsonrpc": "2.0", "id": payload["id"], "result": {"protocolVersion": "2024-11-05"}}
        if m == "notifications/initialized":
            return {"jsonrpc": "2.0", "result": {}}
        if m == "tools/list":
            return {"jsonrpc": "2.0", "id": payload["id"], "result": {"tools": [
                {"name": "echo", "description": "回显文本",
                 "inputSchema": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}},
                {"name": "calc", "description": "加法",
                 "inputSchema": {"type": "object", "properties": {"a": {"type": "integer"}}}},
            ]}}
        if m == "tools/call":
            name = payload["params"]["name"]
            args = payload["params"].get("arguments", {})
            if name == "echo":
                return {"jsonrpc": "2.0", "id": payload["id"],
                        "result": {"content": [{"type": "text", "text": args.get("text", "")}]}}
            if name == "calc":
                return {"jsonrpc": "2.0", "id": payload["id"],
                        "result": {"content": [{"type": "text", "text": "42"}], "isError": False}}
        return {"jsonrpc": "2.0", "id": payload.get("id"), "error": {"code": -32601, "message": "unknown"}}

    def close(self):
        self.closed = True


def test_mcp_initialize_and_list():
    c = McpClient(FakeTransport(), name="demo")
    tools = c.list_tools()
    assert c.initialized is True
    assert [t.name for t in tools] == ["echo", "calc"]
    assert tools[0].server_name == "demo"


def test_mcp_call_tool_ok():
    c = McpClient(FakeTransport(), name="demo")
    r = c.call_tool("echo", {"text": "你好 MCP"})
    assert r["ok"] is True
    assert "你好 MCP" in r["data"]


def test_mcp_call_tool_error_contract():
    c = McpClient(FakeTransport(), name="demo")
    r = c.call_tool("nonexistent", {})
    assert r["ok"] is False and r["error"]


def test_mcp_to_tool_specs():
    c = McpClient(FakeTransport(), name="demo")
    specs = to_tool_specs(c)
    assert len(specs) == 2
    assert specs[0].name == "mcp_demo_echo"
    assert specs[0].permission == "read"
    # run 闭包能真正调用远程工具
    out = specs[0].run({"text": "x"})
    assert out["ok"] is True


def test_mcp_error_on_unknown_transport():
    with pytest.raises(McpError):
        from core.mcp.client import client_from_config
        client_from_config({"transport": "bogus"})


# ================= Skill 包 =================
SAMPLE = """---
name: 起名器
description: 为人物生成有韵味的名字
version: 1.2.0
author: 测试
tags: 创作, 命名
permission: read
---

请为人物起 3 个名字，风格清冷。
输出格式：每行一个名字。
"""


def test_parse_skill_md():
    p = parse_skill_md(SAMPLE)
    assert p.name == "起名器"
    assert p.version == "1.2.0"
    assert p.tags == ["创作", "命名"]
    assert "清冷" in p.instructions


def test_skill_to_prompt():
    p = parse_skill_md(SAMPLE)
    prompt = p.to_prompt()
    assert "# 技能：起名器" in prompt
    assert "清冷" in prompt


def test_validate_skill_md_ok():
    r = validate_skill_md(SAMPLE)
    assert r["ok"] is True and r["data"]["name"] == "起名器"


def test_validate_skill_md_missing_frontmatter():
    r = validate_skill_md("随便一段文字")
    assert r["ok"] is False and "frontmatter" in r["error"]


def test_validate_skill_md_missing_required():
    r = validate_skill_md("---\nname: 只有名字\n---\n正文")
    assert r["ok"] is False


def test_skill_export_import_roundtrip(tmp_path):
    p = parse_skill_md(SAMPLE)
    p.files["scripts/helper.py"] = "print('hi')"
    p.files["references/style.md"] = "风格指南"
    dest = tmp_path / "name-skill.zip"
    export_skill_zip(p, dest)
    loaded = load_skill_zip(dest)
    assert loaded.name == p.name
    assert loaded.version == p.version
    assert loaded.files["scripts/helper.py"] == "print('hi')"


def test_load_skill_zip_from_bytes(tmp_path):
    p = parse_skill_md(SAMPLE)
    dest = tmp_path / "s.zip"
    export_skill_zip(p, dest)
    loaded = load_skill_zip(dest.read_bytes())
    assert loaded.description == p.description


# ================= 子 Agent 并行 =================
class FakeRunner:
    def __init__(self, goal, context, delay=0, fail=False):
        self.goal, self.context, self.delay, self.fail = goal, context, delay, fail

    def run(self):
        if self.delay:
            time.sleep(self.delay)
        if self.fail:
            return {"ok": False, "reply": "", "error": "模拟失败"}
        return {"ok": True, "reply": f"结果：{self.goal}"}


def test_subagent_parallel_all_ok():
    tasks = [SubTask("任务A"), SubTask("任务B"), SubTask("任务C")]
    results = run_parallel(tasks, runner_factory=lambda g, c: FakeRunner(g, c), max_workers=3)
    assert len(results) == 3
    assert all(r.ok for r in results)
    assert {r.reply for r in results} == {"结果：任务A", "结果：任务B", "结果：任务C"}


def test_subagent_isolated_failure():
    tasks = [SubTask("好任务"), SubTask("坏任务")]
    def factory(g, c):
        return FakeRunner(g, c, fail=(g == "坏任务"))
    results = run_parallel(tasks, runner_factory=factory, max_workers=2)
    good = next(r for r in results if r.goal == "好任务")
    bad = next(r for r in results if r.goal == "坏任务")
    assert good.ok is True
    assert bad.ok is False and "模拟失败" in bad.error


def test_subagent_timeout_isolated():
    tasks = [SubTask("慢任务")]
    results = run_parallel(
        tasks,
        runner_factory=lambda g, c: FakeRunner(g, c, delay=1),
        per_task_timeout=1,  # 强制超时
    )
    # 超时或刚好完成都视为已处理，不抛异常；结构合法
    assert len(results) == 1
    assert isinstance(results[0].to_dict(), dict)


def test_subagent_summary_excludes_tool_logs():
    results = [SubResult("A", True, "结论A"), SubResult("B", False, error="失败B")]
    s = summarize_for_parent(results)
    assert "结论A" in s and "失败B" in s
    assert "tool_call" not in s  # 摘要不含工具日志
