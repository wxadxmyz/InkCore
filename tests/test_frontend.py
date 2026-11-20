# -*- coding: utf-8 -*-
"""v2.2 前端改版与 M6 前端入口的回归测试。

覆盖：
1. index.html：三个新入口存在、图标统一、emoji 清除
2. app.js：新面板函数与 API 调用存在、图标库补齐
3. style.css：新版覆盖样式生效
4. 后端：MCP 服务器增删 API、子 Agent API、技能包 API 的错误契约
"""
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
JS = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "static" / "style.css").read_text(encoding="utf-8")


# ---------- 前端结构 ----------
def test_nav_has_mcp_subagent_skillpack_entries():
    for panel in ("mcp", "subagent", "skillpack"):
        assert f'data-panel="{panel}"' in HTML, f"侧栏缺少 {panel} 入口"


def test_nav_entries_are_grouped():
    # v2.5：1:1 还原预览，侧栏四组（创作/智能体与工具/系统 扩展）+ v2.5.1 新增专业版组
    assert HTML.count('class="nav-list"') == 4, "功能导航应分为四组（创作/智能体与工具/系统/专业版）"
    for group in ("创作", "智能体与工具"):
        assert f'<div class="side-title">{group}</div>' in HTML
    assert '<div class="side-title">系统 <small>扩展</small></div>' in HTML
    assert '<div class="side-title">专业版 <small>垂直场景</small></div>' in HTML


def test_new_entries_have_badge():
    assert HTML.count('class="nav-new"') == 4, "三个新入口+专业版入口都应有「新」角标"


def test_topbar_simplified():
    # v2.5：1:1 还原预览——设置带文字、编辑器为图标按钮、新对话为主按钮
    assert 'class="ghost-btn" id="settingsBtn"' in HTML
    assert 'class="ghost-btn icon-only" onclick="location.href=' in HTML
    assert 'class="ghost-btn primary" id="newChatBtn"' in HTML
    # 旧版把「编辑器」写成 emoji 文字，已换成 SVG 图标
    assert "📝 编辑器" not in HTML


def test_no_emoji_in_static_html():
    """静态页面不应残留彩色 emoji（图标统一走线性 SVG）。"""
    emoji = re.findall(r"[\U0001F300-\U0001FAFF☀-➿]", HTML)
    assert not emoji, f"仍残留 emoji: {emoji}"


def test_icon_library_has_new_icons():
    for name in ("plug", "bolt", "package"):
        assert f"{name}:" in JS, f"图标库缺少 {name}"


def test_panel_functions_exist():
    for fn in ("renderMcp", "renderSubagent", "renderSkillPack",
               "loadMcpServers", "loadSkillPacks", "runSubagent",
               "validateSkillPack", "importSkillPack", "exportSkillPack"):
        assert f"function {fn}" in JS, f"缺少函数 {fn}"


def test_panels_registered_in_registry():
    assert "mcp: renderMcp" in JS
    assert "subagent: renderSubagent" in JS
    assert "skillpack: renderSkillPack" in JS


def test_frontend_calls_m6_apis():
    """前端必须真实调用 M6 的后端 API（这是本次修复的核心）。"""
    for api in ("/api/mcp/servers", "/api/mcp/refresh",
                "/api/subagent", "/api/skill/validate",
                "/api/skill/import", "/api/skill/export"):
        assert api in JS, f"前端未调用 {api}"


def test_two_skill_systems_merged():
    """两套 skill 系统打通：技能面板可跳转技能包，技能包面板可导出。"""
    assert "openPanel('skillpack')" in JS, "技能面板缺少跳转技能包入口"
    assert "exportSkillPack('${s.id}')" in JS, "技能卡片缺少导出技能包按钮"
    # 技能包面板读取的是同一份 skills.json
    assert 'fetch("/api/skills")' in JS


def test_css_v22_overrides_present():
    for token in (".nav-list", ".nav-new", ".srv-row", ".sub-task",
                  ".pack-row", ".empty-hint", ".ghost-btn.icon-only",
                  ".brand-ver"):
        assert token in CSS, f"样式缺少 {token}"


def test_welcome_cards_simplified():
    """欢迎区大卡片收敛为紧凑胶囊（去掉 small 副标题）。"""
    assert "<small>我能帮你做哪些事？</small>" not in HTML


# ---------- 后端 API ----------
@pytest.fixture()
def client():
    import app as appmod
    appmod.app.config["TESTING"] = True
    with appmod.app.test_client() as c:
        yield c


def test_mcp_server_list_api(client):
    r = client.get("/api/mcp/servers")
    d = r.get_json()
    assert d["ok"] is True
    assert isinstance(d["servers"], list)


def test_mcp_server_add_requires_name(client):
    r = client.post("/api/mcp/servers", json={"name": "", "transport": "stdio"})
    assert r.status_code == 400
    assert r.get_json()["ok"] is False


def test_mcp_server_add_rejects_bad_transport(client):
    r = client.post("/api/mcp/servers", json={"name": "x", "transport": "ftp"})
    assert r.status_code == 400


def test_mcp_server_add_rejects_http_without_url(client):
    r = client.post("/api/mcp/servers", json={"name": "x", "transport": "http", "url": "notaurl"})
    assert r.status_code == 400


def test_mcp_server_add_and_delete(client):
    import app as appmod
    before = len(appmod.config.get("mcp", {}).get("servers", []))
    r = client.post("/api/mcp/servers", json={
        "name": "unit-test-server", "transport": "http", "url": "http://127.0.0.1:9/mcp"})
    assert r.status_code == 200
    assert r.get_json()["ok"] is True
    # 清理：删除刚加的
    r2 = client.delete("/api/mcp/servers?name=unit-test-server")
    assert r2.status_code == 200
    after = len(appmod.config.get("mcp", {}).get("servers", []))
    assert after == before


def test_subagent_requires_goals(client):
    r = client.post("/api/subagent", json={"goals": []})
    assert r.status_code == 400
    assert r.get_json()["ok"] is False


def test_skill_validate_rejects_bad_text(client):
    r = client.post("/api/skill/validate", json={"text": "随便一段没有 frontmatter 的文字"})
    d = r.get_json()
    assert d["ok"] is False


def test_skill_validate_accepts_wellformed(client):
    text = "---\nname: demo-skill\ndescription: 演示技能\nversion: 1.0.0\n---\n\n这是一个演示技能。"
    r = client.post("/api/skill/validate", json={"text": text})
    d = r.get_json()
    assert d["ok"] is True
    assert d["data"]["name"] == "demo-skill"


def test_skill_import_requires_file(client):
    r = client.post("/api/skill/import", data={}, content_type="multipart/form-data")
    assert r.status_code == 400
    assert r.get_json()["ok"] is False
