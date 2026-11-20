# -*- coding: utf-8 -*-
"""v2.4 回归测试：内置模型「下载了却用不了」的三个根因修复。

1. GGUF 文件头校验：错误页/半截文件不能再被误判为「已就绪」
2. 下载成功自动切换 provider 到 embedded
3. embedded 场景忽略会话里残留的云端模型名
4. 下载完先校验再原子替换
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.py").read_text(encoding="utf-8")
LLM = (ROOT / "local_llm.py").read_text(encoding="utf-8")


def test_gguf_magic_defined():
    assert 'GGUF_MAGIC = b"GGUF"' in LLM


def test_is_valid_gguf_rejects_html():
    """校验函数：HTML 错误页（非 GGUF 头）必须判为无效。"""
    import local_llm
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".gguf", delete=False) as f:
        f.write(b"<html>error page padding padding</html>" + b"x" * 1_100_000)
        path = f.name
    try:
        assert local_llm._is_valid_gguf(path) is False, "HTML 错误页不应判为有效 GGUF"
    finally:
        import os
        os.unlink(path)


def test_is_valid_gguf_accepts_real_header():
    """校验函数：以 GGUF 魔数开头的合法头应判为有效。"""
    import local_llm
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".gguf", delete=False) as f:
        f.write(b"GGUF" + b"\x00" * 1_100_000)
        path = f.name
    try:
        assert local_llm._is_valid_gguf(path) is True
    finally:
        import os
        os.unlink(path)


def test_is_ready_uses_gguf_check():
    """is_ready 必须走 GGUF 校验，而不是只看文件大小。"""
    assert "return _is_valid_gguf(model_path(key))" in LLM


def test_download_validates_before_replace():
    """下载完成后必须先校验文件头，再原子替换到目标路径。"""
    idx_validate = LLM.find("_is_valid_gguf(part)")
    idx_replace = LLM.find("part.replace(dest)")
    assert idx_validate != -1 and idx_replace != -1
    assert idx_validate < idx_replace, "必须先校验 GGUF 再替换文件"


def test_on_downloaded_callback_registered():
    """下载成功回调必须在 app.py 注册，用于自动切换 provider。"""
    assert "set_on_downloaded" in APP
    assert "config[\"provider\"] = \"embedded\"" in APP
    assert "_on_embedded_downloaded" in APP


def test_embedded_ignores_session_cloud_model():
    """embedded 场景必须忽略会话里残留的云端模型名。"""
    assert "config.get(\"provider\") == \"embedded\"" in APP
    assert "if m in local_llm.MODELS:" in APP
    assert "is_embedded" in APP


def test_embedded_uses_registry_model():
    """get_llm_cfg 对 embedded 只接受 local_llm.MODELS 里的合法 key。"""
    import app
    # 全局配置临时切到 embedded
    orig = {k: app.config[k] for k in ("provider", "llm") if k in app.config}
    orig_conv = dict(app.conversations)
    try:
        app.config["provider"] = "embedded"
        app.config["llm"] = dict(app.config["llm"])
        app.config["llm"]["base_url"] = "embedded://local"
        app.config["llm"]["model"] = "qwen2.5-1.5b-instruct-q4_k_m"
        app.conversations["sess-v24"] = {"model": "gpt-4o-mini"}
        cfg = app.get_llm_cfg("sess-v24")
        assert cfg["model"] == "qwen2.5-1.5b-instruct-q4_k_m", \
            f"云端残留模型名未被忽略，实际 {cfg['model']}"
    finally:
        app.config.update(orig)
        app.conversations.clear()
        app.conversations.update(orig_conv)
