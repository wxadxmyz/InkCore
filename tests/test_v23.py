# -*- coding: utf-8 -*-
"""v2.3 修复与 A 方案重设计的回归测试。

覆盖 12 项：
1. logo 不再被去白底算法误伤（完整熊猫）
2. 内置模型 downloading 状态复位
3. llama_available 探测结果写回 _status
4. 下载源：镜像优先 + 官方兜底
5. build.spec 收集 llama 原生动态库
6. 图标与文字对齐（父按钮 flex）
7. 发送/停止按钮图标用 .ic 包裹
8. 顶部标签栏已移除
9. 对话头像已移除
10. 输入框有添加文件按钮
11. A 方案暖调墨灰配色
12. 下载状态展示源/速度/大小
"""
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
JS = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "static" / "style.css").read_text(encoding="utf-8")
SPEC = (ROOT / "build.spec").read_text(encoding="utf-8")


# ---------- 1) logo ----------
def test_icon_is_not_white_removed():
    """icon.png 必须保留完整熊猫：不能是"白底抠空"版本。"""
    from PIL import Image
    im = Image.open(ROOT / "static" / "icon.png").convert("RGBA")
    assert im.size == (1024, 1024)
    # 圆形裁切后，透明像素占比应在合理区间（抠空版会异常高/低）
    px = list(im.getdata())
    transparent = sum(1 for p in px if p[3] < 10) / len(px)
    assert 0.05 < transparent < 0.30, f"透明像素占比异常: {transparent:.2%}"
    # 中心区域（熊猫脸）应有大量不透明像素 —— 说明没被误抠
    w, h = im.size
    center = im.crop((w // 4, h // 4, w * 3 // 4, h * 3 // 4)).convert("RGBA")
    cpx = list(center.getdata())
    opaque = sum(1 for p in cpx if p[3] > 200) / len(cpx)
    assert opaque > 0.55, f"中心区域不透明像素仅 {opaque:.0%}，熊猫脸可能被误抠"


def test_ico_has_multiple_sizes():
    from PIL import Image
    ico = Image.open(ROOT / "static" / "icon.ico")
    assert len(ico.ico.sizes()) >= 5


# ---------- 2/3/4) 内置模型 ----------
def test_download_state_resets_on_failure():
    """下载失败后 downloading 必须复位为 False（修永久「下载中」）。"""
    import local_llm
    local_llm._set(downloading=True, progress=0.5, error=None)
    # 模拟一次必然失败的下载（无效 URL）
    orig = local_llm.MODELS["qwen2.5-1.5b-instruct-q4_k_m"].copy()
    local_llm.MODELS["qwen2.5-1.5b-instruct-q4_k_m"]["url"] = "http://127.0.0.1:9/nope.gguf"
    try:
        ok = local_llm.download("qwen2.5-1.5b-instruct-q4_k_m")
        assert ok is False
        st = local_llm.get_status()
        assert st["downloading"] is False, "失败后 downloading 未复位"
        assert st["error"], "失败后应有 error"
        assert st["progress"] == 0.0
    finally:
        local_llm.MODELS["qwen2.5-1.5b-instruct-q4_k_m"].update(orig)
        local_llm._set(downloading=False, error=None, progress=0.0, speed=0,
                       downloaded_bytes=0, source="", attempts=[])


def test_llama_available_is_cached():
    """llama_available 探测结果必须写回 _status，避免每次调用都重新 import。"""
    import local_llm
    local_llm._set(llama_available=None)
    s1 = local_llm.get_status()
    assert s1["llama_available"] in (True, False)
    # 第二次调用后 _status 里应已有值（不再是 None）
    assert local_llm._status["llama_available"] is not None


def test_mirror_url_conversion():
    import local_llm
    assert local_llm._mirror_url("https://huggingface.co/a/b.gguf") == \
        "https://hf-mirror.com/a/b.gguf"
    assert local_llm._mirror_url("https://example.com/x") == "https://example.com/x"


def test_download_uses_mirror_first():
    """下载顺序：先国内镜像，失败再官方源。"""
    import local_llm
    tried = []

    def fake_download(url, part, total_guess, progress_cb=None, timeout=30):
        tried.append(url)
        raise RuntimeError("mock fail")

    orig = local_llm._download_from
    local_llm._download_from = fake_download
    try:
        local_llm.download("qwen2.5-1.5b-instruct-q4_k_m")
    finally:
        local_llm._download_from = orig
        local_llm._set(downloading=False, error=None, progress=0.0, speed=0,
                       downloaded_bytes=0, source="", attempts=[])
    assert len(tried) == 2, f"应尝试两个源，实际 {len(tried)}"
    assert tried[0].startswith("https://hf-mirror.com/"), "第一个源应是国内镜像"
    assert tried[1].startswith("https://huggingface.co/"), "第二个源应是官方源"


def test_start_download_resets_state_on_exception():
    """后台线程内异常也必须复位 downloading（否则永久「下载中」）。"""
    import local_llm
    orig = local_llm.download
    local_llm.download = lambda key=None, progress_cb=None: (_ for _ in ()).throw(RuntimeError("boom"))
    try:
        assert local_llm.start_download("qwen2.5-1.5b-instruct-q4_k_m") is True
        import time
        for _ in range(50):
            if local_llm._status.get("error"):
                break
            time.sleep(0.05)
        assert local_llm._status["downloading"] is False
        assert local_llm._status["error"]
    finally:
        local_llm.download = orig
        local_llm._set(downloading=False, error=None, progress=0.0, speed=0,
                       downloaded_bytes=0, source="", attempts=[])


# ---------- 5) 打包 ----------
def test_build_spec_collects_llama_binaries():
    assert "collect_dynamic_libs('llama_cpp')" in SPEC
    assert "binaries=_llama_binaries" in SPEC


def test_ci_installs_llama_tolerantly():
    yml = (ROOT / ".github" / "workflows" / "build.yml").read_text(encoding="utf-8")
    assert "llama-cpp-python" in yml
    assert "continue-on-error: true" in yml, "llama 安装失败不应阻断构建"


# ---------- 6) 图标对齐 ----------
def test_icon_alignment_css():
    """含图标的按钮必须 flex 居中，避免图标与文字基线错位。"""
    assert ".ic{" in CSS
    assert "vertical-align:middle" in CSS
    for sel in (".ghost-btn,.pchip,.chip,.btn",):
        assert sel in CSS
    assert "align-items:center;gap:7px" in CSS


# ---------- 7) 发送按钮 ----------
def test_send_button_uses_ic_wrapper():
    """停止/发送态都必须用 <i class="ic"> 包裹，否则图标取不到白色样式。"""
    assert 'b.innerHTML=`<i class="ic">${svg("stop")}</i>`' in JS
    assert 'b.innerHTML=`<i class="ic">${svg("send")}</i>`' in JS
    assert "b.innerHTML=svg(" not in JS, "仍存在裸 SVG 注入（会丢颜色）"
    assert "#sendBtn .ic" in CSS
    assert "#sendBtn.stopping .ic" in CSS


# ---------- 8) 标签栏 ----------
def test_tab_bar_removed():
    """顶部标签栏已移除（与侧栏会话列表功能重复）。"""
    assert 'class="tab-bar"' not in HTML
    assert 'id="tabBar"' not in HTML
    # JS 侧不再创建标签栏 DOM
    assert 'bar.className="tab-bar"' not in JS
    assert 'className="tab-close"' not in JS
    # CSS 兜底隐藏
    assert ".tab-bar{display:none !important}" in CSS


def test_new_chat_button_still_works():
    """删掉标签栏后，「新对话」仍能开新会话。"""
    assert "$(\"#newChatBtn\").onclick=()=>newTab();" in JS
    assert "function newTab()" in JS


# ---------- 9) 头像 ----------
def test_avatars_removed():
    """对话头像已去掉（不再显示「你」/「墨」方块）。"""
    assert 'av.textContent = role==="user"?"你":"墨"' not in JS
    assert '<div class="avatar">墨</div>' not in JS
    assert '<div class="avatar">源</div>' not in JS
    assert ".avatar-hidden{display:none !important}" in CSS


# ---------- 10) 附件按钮 ----------
def test_attach_button_present():
    assert 'id="attachBtn"' in HTML
    assert 'id="attachInput"' in HTML
    assert "function handleAttach(file)" in JS
    assert '$(function' not in JS  # sanity
    assert '$("#attachBtn").onclick' in JS
    assert '$("#attachInput").onchange' in JS
    assert "attach:" in JS, "图标库缺少 attach"


def test_attach_routes_by_type():
    """图片走视觉理解，文档入知识库。"""
    assert "sendVision(file)" in JS
    assert "uploadDoc(file)" in JS
    assert "_DOC_EXT" in JS


# ---------- 11) A 方案配色 ----------
def test_warm_ink_palette():
    assert "--bg:#16151a" in CSS, "底色应为墨灰暖调"
    assert "--accent:#8b7cf6" in CSS, "强调色应为单一墨紫"
    # 青色主色已移除（仅保留为状态色）
    assert "--accent-2:#8b7cf6" in CSS


def test_a_scheme_removes_strokes():
    """A 方案：卡片去描边，靠背景层级区分。"""
    assert ".pcard{background:var(--surface-2);border:none" in CSS
    assert ".wcard{flex-direction:row" in CSS


# ---------- 12) 下载状态展示 ----------
def test_download_status_shows_source_speed_size():
    assert "_fmtSize" in JS
    assert "_fmtSpeed" in JS
    assert "国内镜像" in JS
    assert "官方源" in JS
    assert "s.downloaded_bytes" in JS
    assert "s.speed" in JS
