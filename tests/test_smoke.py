# -*- coding: utf-8 -*-
"""M1 冒烟测试：验证 P0 修复点不回退。

运行： python3 -m pytest tests/ -q
注意：这些测试不依赖任何 API Key 或外部网络。
"""
import os
import sys
import json
import importlib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


@pytest.fixture(scope="module")
def appmod():
    """导入 app 模块一次；所有用例共享其进程内状态。"""
    return importlib.import_module("app")


# ---------- 模块基础 ----------
def test_module_imports(appmod):
    assert hasattr(appmod, "app")
    assert hasattr(appmod, "route")


def test_version_is_1_1_0(appmod):
    assert appmod.APP_VERSION == "1.1.0"


# ---------- D1：parse_qs / urlparse ----------
def test_url_parse_helpers_imported(appmod):
    assert callable(appmod.parse_qs)
    assert callable(appmod.urlparse)


def test_web_search_decodes_uddg(appmod, monkeypatch):
    """命中 uddg 编码链接时应解码为真实 http URL。"""
    class FakeResp:
        text = ('<div class="result"><a class="result__a" '
                'href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com%2Fpage'
                '&rut=abc">Example</a>'
                '<a class="result__snippet">snippet</a></div>')
    monkeypatch.setattr(appmod.requests, "post", lambda *a, **k: FakeResp())
    out = appmod.web_search("test", n=1)
    assert out["sources"][0]["url"] == "https://example.com/page"


def test_web_search_rejects_dangerous_scheme(appmod, monkeypatch):
    """uddg 解码出 javascript: 等危险 scheme 时不应作为结果 URL。"""
    class FakeResp:
        text = ('<div class="result"><a class="result__a" '
                'href="//duckduckgo.com/l/?uddg=javascript%3Aalert(1)">Bad</a></div>')
    monkeypatch.setattr(appmod.requests, "post", lambda *a, **k: FakeResp())
    out = appmod.web_search("test", n=1)
    assert not out["sources"][0]["url"].startswith("javascript:")


def test_web_search_returns_sources_key(appmod, monkeypatch):
    class FakeResp:
        text = "<html></html>"
    monkeypatch.setattr(appmod.requests, "post", lambda *a, **k: FakeResp())
    out = appmod.web_search("nothing", n=3)
    assert "snippet" in out and "sources" in out
    assert out["sources"] == []


# ---------- D2：Python 解释器选择 ----------
def test_python_executable_exists(appmod):
    exe = appmod._python_executable()
    assert exe
    assert os.path.basename(exe).lower().startswith(("python", "pypy")) or os.path.isfile(exe)


def test_run_code_uses_selected_interpreter(appmod, monkeypatch):
    """run_code 应调用 _python_executable() 返回的解释器而不是硬编码 python3。"""
    called = {}

    class FakeProc:
        stdout = "2\n"
        stderr = ""
        returncode = 0

    def fake_run(cmd, **kw):
        called["cmd"] = cmd
        return FakeProc()

    monkeypatch.setattr(appmod.subprocess, "run", fake_run)
    out = appmod.run_code("print(1+1)")
    assert "2" in out
    assert called["cmd"][0] == appmod._python_executable()


# ---------- D3：PDF 纯 Python 解析 ----------
def test_extract_text_pdf_without_poppler(appmod, tmp_path, monkeypatch):
    """无 pdftotext 时优先走纯 Python（pypdf）路径提取文本。"""
    import pypdf

    class FakePage:
        def extract_text(self):
            return "墨核 PDF 正文"

    class FakeReader:
        def __init__(self, path):
            self.pages = [FakePage()]

    monkeypatch.setattr(pypdf, "PdfReader", FakeReader)

    def fail_pdftotext(*a, **k):
        raise AssertionError("不应调用外部 pdftotext")

    monkeypatch.setattr(appmod.subprocess, "run", fail_pdftotext)
    pdf = tmp_path / "sample.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")
    assert appmod.extract_text(pdf, ".pdf") == "墨核 PDF 正文"


def test_extract_text_txt(appmod, tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("hello 墨核", encoding="utf-8")
    assert appmod.extract_text(f, ".txt") == "hello 墨核"


def test_extract_text_unsupported(appmod, tmp_path):
    f = tmp_path / "a.bin"
    f.write_bytes(b"\x00")
    assert appmod.extract_text(f, ".bin") is None


# ---------- 7a：免 Key 判定统一 ----------
def test_llm_usable_local_embedded(appmod):
    cfg = {"enabled": True, "base_url": "embedded://local", "api_key": ""}
    assert appmod._llm_usable(cfg) is True


def test_llm_usable_ollama(appmod):
    cfg = {"enabled": True, "base_url": "http://localhost:11434/v1", "api_key": ""}
    assert appmod._llm_usable(cfg) is True


def test_llm_not_usable_remote_without_key(appmod):
    cfg = {"enabled": True, "base_url": "https://api.openai.com/v1", "api_key": ""}
    assert appmod._llm_usable(cfg) is False


def test_llm_not_usable_when_disabled(appmod):
    cfg = {"enabled": False, "base_url": "embedded://local", "api_key": ""}
    assert appmod._llm_usable(cfg) is False


def test_llm_pick_tool_enabled_for_local_model(appmod, monkeypatch):
    """本地免 Key 模型下 llm_pick_tool 不应直接返回 None。"""
    monkeypatch.setitem(appmod.config["llm"], "enabled", True)
    monkeypatch.setitem(appmod.config["llm"], "base_url", "embedded://local")
    monkeypatch.setitem(appmod.config["llm"], "api_key", "")
    monkeypatch.setattr(appmod, "call_llm",
                        lambda *a, **k: '{"tool":"search"}')
    assert appmod.llm_pick_tool("搜索最新 AI 资讯") == "search"


def test_agent_run_uses_llm_when_local(appmod, monkeypatch):
    """本地模型下 agent_run 应走 LLM 合成而非跳过。"""
    monkeypatch.setitem(appmod.config["llm"], "enabled", True)
    monkeypatch.setitem(appmod.config["llm"], "base_url", "embedded://local")
    monkeypatch.setitem(appmod.config["llm"], "api_key", "")
    monkeypatch.setattr(appmod, "call_api",
                        lambda *a, **k: "合成结论：已完成调研。")
    out = appmod.agent_run("调研竞品", ["搜索竞品资料"])
    assert "智能合成结果" in out


# ---------- 数据写盘 / 安全 ----------
def test_atomic_save_roundtrip(appmod, tmp_path):
    p = tmp_path / "nested" / "data.json"
    appmod._save(p, {"k": "墨核", "n": 1})
    assert json.loads(p.read_text(encoding="utf-8")) == {"k": "墨核", "n": 1}
    assert not (tmp_path / "nested" / "data.json.tmp").exists()


def test_atomic_save_concurrent(appmod, tmp_path):
    import threading
    p = tmp_path / "concurrent.json"

    def writer(n):
        for i in range(20):
            appmod._save(p, {"writer": n, "i": i})

    threads = [threading.Thread(target=writer, args=(i,)) for i in range(5)]
    for t in threads: t.start()
    for t in threads: t.join()
    data = json.loads(p.read_text(encoding="utf-8"))  # 未损坏
    assert data["writer"] in range(5)


def test_dangerous_command_blocked(appmod):
    assert appmod.is_dangerous("rm -rf /") is not None
    assert appmod.is_dangerous("ls -la") is None


def test_readonly_mode_blocks_write(appmod):
    assert appmod._readonly_blocked("rm file.txt") is True
    assert appmod._readonly_blocked("ls -la") is False
