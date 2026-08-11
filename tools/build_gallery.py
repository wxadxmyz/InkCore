# -*- coding: utf-8 -*-
"""
墨核 AI Studio · 功能画廊生成器

一次生成两份产物：
  1) docs/index.html   —— 图片走外链 shots/xxx.png，体积小，用于 GitHub Pages 部署
  2) ui_gallery.html   —— 图片内嵌 base64，单文件自包含，可离线双击打开 / 随手发给别人

用法：
    python3 tools/build_gallery.py
"""
import base64
import os
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SHOTS = ROOT / "docs" / "shots"

REPO = "wxadxmyz/InkCore"
VERSION = "v1.0.0"
REL = f"https://github.com/{REPO}/releases/latest/download"

# ---------------------------------------------------------------- 截图元数据
# (文件名, 分区key, 标题, 描述, [标签...])
SHOTS_META = [
    ("g_01_main.png", "core", "主界面 · 对话工作台",
     "左侧会话列表，中间对话流，右侧可收起的功能抽屉。输入框上方是快捷 chip，"
     "直接点「AI 生图」「联网搜索」等即可切换意图，不用再单独开面板。",
     ["三栏布局", "快捷 chip", "深色墨感"]),

    ("g_02_settings_providers.png", "model", "设置 · 多供应商模型中心",
     "弹窗式 tab 设置，一屏切换 10 家供应商。每家的 API Key 独立保存，"
     "来回切换不会互相覆盖，换回来时自动回填上次填过的 Key。",
     ["10 家供应商", "Key 独立存储", "tab 式"]),

    ("g_03_provider_siliconflow.png", "model", "免费聚合供应商 · SiliconFlow / OpenRouter",
     "新增两家聚合平台，注册即送额度，适合零成本先跑起来。"
     "模型下拉里已预置 Qwen2.5、GLM、gpt-4o-mini 等常用型号。",
     ["白嫖友好", "预置模型", "新增"]),

    ("g_04_inherit_key.png", "model", "一键继承 Key 到生图 / 视觉",
     "勾上「继承主模型 Key」，生图和视觉理解就直接复用对话模型的 Key 和 Base URL，"
     "省掉重复三遍填同一串密钥的折磨。",
     ["少填两次", "自动同步"]),

    ("g_05_settings_ollama.png", "model", "本地模型 · Ollama 管理",
     "Ollama 从独立面板挪进了设置页，作为「本地模型」tab。"
     "可刷新已装模型列表、一键切换为当前对话模型、删除不用的权重。",
     ["Ollama", "完全离线", "已归位"]),

    ("g_06_terminal_full.png", "work", "终端 · 全屏覆盖",
     "点面板右上角的最大化按钮，抽屉铺满整个聊天区。"
     "终端这类需要看长输出的场景，400px 抽屉实在不够用。",
     ["全屏", "一键还原"]),

    ("g_07_code_full.png", "work", "代码运行 · 聊天直接生成并自动全屏",
     "在对话里说「帮我写个冒泡排序并运行」，后端识别意图后直接生成代码、"
     "自动打开代码面板、自动填入、自动全屏。不用手动复制粘贴。",
     ["意图识别", "自动填入", "自动全屏"]),

    ("g_08_agent_full.png", "work", "Agent 编排 · 自动拆解任务",
     "对话中描述目标，模型自动拆成可执行步骤列表并推进。"
     "同样支持从聊天直接唤起并铺满全屏。",
     ["任务拆解", "自动唤起"]),

    ("g_14_knowledge.png", "work", "知识库 · 文档理解 (RAG)",
     "上传文档后建立本地索引，对话时自动检索相关片段作为上下文。"
     "文件不出本机，检索也在本地完成。",
     ["RAG", "本地索引", "可全屏"]),

    ("g_09_fun_list.png", "fun", "离谱玩法 · 玩法列表",
     "内置 6 个预设玩法（毒舌吐槽、废话生成器、赛博算命等）。"
     "面板同样支持全屏，长文本输出看得清。",
     ["6 个预设", "可全屏"]),

    ("g_10_fun_newform.png", "fun", "离谱玩法 · 自建与导入导出",
     "自己写 prompt 就能新建玩法，存进本地 funs.json。"
     "支持整包导出 JSON 分享给别人，也能导入别人的玩法包。",
     ["用户自建", "导入导出", "新增"]),

    ("g_12_skills.png", "fun", "技能中心",
     "把常用能力做成可点即用的卡片：文案改写、翻译、总结、表格提取等。"
     "技能只做触发，结果回落到对话流里，不额外占屏。",
     ["卡片式", "即点即用"]),

    ("g_11_memory_empty.png", "mem", "会话记忆 · 空状态引导",
     "面板没内容时不再是一片空白，改为给出说明和下一步动作提示，"
     "新用户不至于打开就懵。所有功能面板都做了这套空状态。",
     ["空状态", "新手引导"]),

    ("g_13_artifacts_strip.png", "mem", "会话产物条",
     "本次会话生成过的图片、小游戏等产物，以缩略图形式钉在输入框上方，"
     "点一下就能重新打开，不用往上翻聊天记录找。可折叠收起。",
     ["产物留痕", "一键回看", "可折叠"]),
]

SECTIONS = [
    ("core", "核心界面", "整体布局与日常入口"),
    ("model", "模型与设置", "10 家供应商 · 本地模型 · Key 管理"),
    ("work", "工作面板 · 全屏", "终端 / 代码 / Agent / 知识库"),
    ("fun", "玩法与技能", "内置玩法 · 自建导入 · 技能卡片"),
    ("mem", "记忆与产物", "空状态引导 · 会话产物留痕"),
]

CHANGELOG = [
    ("面板宽度统一 400px", "删掉了 340/392 的分档逻辑，所有抽屉一个宽度，视觉不再跳动。"),
    ("全屏覆盖按钮", "知识库 / 终端 / 代码 / Agent / 离谱玩法 五个工作型面板支持一键铺满聊天区。"),
    ("聊天自动唤起面板", "说「写段代码并运行」，自动生成 + 自动填入 + 自动全屏，Agent 与终端同理。"),
    ("离谱玩法自建", "新建 / 删除 / 导出 JSON / 导入 JSON，玩法可以自己攒也可以互相分享。"),
    ("每供应商独立记 Key", "切换供应商不再冲掉上一家的密钥，切回来自动回填。"),
    ("新增免费聚合供应商", "SiliconFlow 与 OpenRouter，注册送额度，零成本起步。"),
    ("继承 Key 到生图 / 视觉", "一个勾选框省掉两次重复填写。"),
    ("面板空状态引导", "空面板不再是白板，给出说明与下一步提示。"),
    ("会话产物条", "生成过的图片 / 小游戏钉在输入框上方，点开即回看。"),
    ("Ollama 并入设置", "本地模型作为设置页的一个 tab，不再单占一个功能位。"),
]

STATS = [
    ("14", "功能截图"),
    ("10", "模型供应商"),
    ("5", "可全屏面板"),
    ("10", "本次改动项"),
]

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#0b0d14; --bg2:#11141f; --card:#161a26; --line:#252b3a;
  --tx:#e8eaf2; --tx2:#9aa3b8; --tx3:#6b7488;
  --ac:#7c6cff; --ac2:#33c9e6;
}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif;
  background:var(--bg);color:var(--tx);line-height:1.6;-webkit-font-smoothing:antialiased}
a{color:inherit;text-decoration:none}
.wrap{max-width:1240px;margin:0 auto;padding:0 24px}

/* ---------- hero ---------- */
.hero{position:relative;overflow:hidden;padding:72px 0 56px;text-align:center;
  background:radial-gradient(1000px 420px at 50% -80px,rgba(124,108,255,.22),transparent 70%),
             linear-gradient(180deg,#141826,var(--bg))}
.badge{display:inline-block;font-size:12px;letter-spacing:.08em;color:var(--ac2);
  border:1px solid rgba(51,201,230,.35);background:rgba(51,201,230,.08);
  padding:5px 14px;border-radius:999px;margin-bottom:18px}
.hero h1{font-size:40px;font-weight:800;letter-spacing:-.5px;margin-bottom:14px;
  background:linear-gradient(96deg,#fff 20%,#a9c6ff 60%,#7c6cff);
  -webkit-background-clip:text;background-clip:text;color:transparent}
.hero p{color:var(--tx2);font-size:16px;max-width:640px;margin:0 auto}
.btns{display:flex;gap:12px;justify-content:center;flex-wrap:wrap;margin-top:30px}
.btn{display:inline-flex;align-items:center;gap:9px;padding:13px 26px;border-radius:12px;
  font-weight:700;font-size:15px;transition:.18s;border:1px solid transparent}
.btn-main{background:linear-gradient(135deg,var(--ac),var(--ac2));color:#fff;
  box-shadow:0 8px 26px rgba(124,108,255,.34)}
.btn-main:hover{transform:translateY(-2px);box-shadow:0 12px 32px rgba(124,108,255,.46)}
.btn-sec{background:rgba(255,255,255,.05);border-color:var(--line);color:var(--tx)}
.btn-sec:hover{background:rgba(255,255,255,.1);border-color:#39415a}
.btn small{display:block;font-weight:400;font-size:11.5px;opacity:.8;margin-top:1px}
.tip{margin-top:16px;font-size:12.5px;color:var(--tx3)}

/* ---------- stats ---------- */
.stats{display:flex;justify-content:center;gap:56px;flex-wrap:wrap;margin-top:44px;
  padding-top:32px;border-top:1px solid rgba(255,255,255,.06)}
.stat b{display:block;font-size:30px;font-weight:800;
  background:linear-gradient(135deg,#fff,#9ec5ff);-webkit-background-clip:text;background-clip:text;color:transparent}
.stat span{font-size:12.5px;color:var(--tx3)}

/* ---------- nav ---------- */
.nav{position:sticky;top:0;z-index:40;background:rgba(11,13,20,.86);
  backdrop-filter:blur(14px);border-bottom:1px solid var(--line)}
.nav-in{display:flex;gap:6px;overflow-x:auto;padding:12px 24px;max-width:1240px;margin:0 auto}
.nav a{white-space:nowrap;font-size:13.5px;color:var(--tx2);padding:7px 15px;border-radius:9px;transition:.15s}
.nav a:hover{color:var(--tx);background:rgba(255,255,255,.06)}

/* ---------- section ---------- */
section{padding:56px 0 8px;scroll-margin-top:60px}
.sec-h{display:flex;align-items:baseline;gap:14px;margin-bottom:26px;flex-wrap:wrap}
.sec-h h2{font-size:23px;font-weight:750}
.sec-h em{font-style:normal;font-size:13px;color:var(--tx3)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(430px,1fr));gap:22px}

figure{background:var(--card);border:1px solid var(--line);border-radius:15px;overflow:hidden;
  transition:.2s;display:flex;flex-direction:column}
figure:hover{border-color:#3c4358;transform:translateY(-3px);box-shadow:0 14px 34px rgba(0,0,0,.42)}
.shot{position:relative;cursor:zoom-in;background:#0a0c12;line-height:0}
.shot img{width:100%;display:block}
.shot::after{content:'点击放大';position:absolute;right:10px;bottom:10px;font-size:11px;
  background:rgba(0,0,0,.62);color:#fff;padding:4px 10px;border-radius:6px;opacity:0;transition:.18s;line-height:1.4}
figure:hover .shot::after{opacity:1}
figcaption{padding:15px 17px 17px;flex:1;display:flex;flex-direction:column}
figcaption b{font-size:15px;font-weight:700;display:block;margin-bottom:7px}
figcaption p{font-size:13.2px;color:var(--tx2);line-height:1.68;flex:1}
.tags{display:flex;gap:6px;flex-wrap:wrap;margin-top:12px}
.tag{font-size:11px;color:#a9b4cc;background:rgba(124,108,255,.11);
  border:1px solid rgba(124,108,255,.24);padding:3px 9px;border-radius:6px}

/* ---------- changelog ---------- */
.log{background:var(--bg2);border:1px solid var(--line);border-radius:15px;padding:30px 32px;margin-top:14px}
.log ol{list-style:none;counter-reset:n}
.log li{counter-increment:n;padding:13px 0 13px 44px;position:relative;border-bottom:1px dashed rgba(255,255,255,.07)}
.log li:last-child{border-bottom:none}
.log li::before{content:counter(n);position:absolute;left:0;top:14px;width:26px;height:26px;
  display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;color:#fff;
  background:linear-gradient(135deg,var(--ac),var(--ac2));border-radius:8px}
.log b{font-size:14.5px;display:block;margin-bottom:3px}
.log span{font-size:13px;color:var(--tx2)}

/* ---------- install ---------- */
.cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:18px}
.col{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:24px}
.col h3{font-size:16px;margin-bottom:12px;display:flex;align-items:center;gap:8px}
.col ol,.col ul{padding-left:19px;font-size:13.4px;color:var(--tx2)}
.col li{margin:7px 0}
code{background:rgba(255,255,255,.07);border:1px solid var(--line);padding:2px 7px;
  border-radius:5px;font-family:'SF Mono',Consolas,monospace;font-size:12.4px;color:#a9c6ff}
pre{background:#0a0c12;border:1px solid var(--line);border-radius:10px;padding:14px 16px;
  overflow-x:auto;margin-top:10px}
pre code{background:none;border:none;padding:0;color:#c3cde0;font-size:12.5px;line-height:1.75}

footer{text-align:center;color:var(--tx3);font-size:12.5px;padding:60px 24px 46px;
  margin-top:56px;border-top:1px solid var(--line)}
footer a{color:var(--ac2)}

/* ---------- lightbox ---------- */
#lb{position:fixed;inset:0;z-index:99;background:rgba(5,6,10,.95);display:none;
  align-items:center;justify-content:center;padding:36px}
#lb.on{display:flex}
#lb img{max-width:100%;max-height:100%;border-radius:9px;box-shadow:0 24px 70px rgba(0,0,0,.7)}
#lb .x{position:absolute;top:20px;right:26px;font-size:30px;color:#fff;cursor:pointer;
  opacity:.65;line-height:1;background:none;border:none}
#lb .x:hover{opacity:1}
#lb .ar{position:absolute;top:50%;transform:translateY(-50%);font-size:34px;color:#fff;
  cursor:pointer;opacity:.5;padding:22px 16px;background:none;border:none;user-select:none}
#lb .ar:hover{opacity:1}
#lb .prev{left:12px}#lb .next{right:12px}
#lb .cap{position:absolute;bottom:20px;left:0;right:0;text-align:center;color:#c8cee0;font-size:13.5px}

@media(max-width:860px){
  .hero h1{font-size:29px}
  .grid{grid-template-columns:1fr}
  .stats{gap:32px}
  .wrap{padding:0 16px}
}
"""

JS = """
(function(){
  var imgs=[].slice.call(document.querySelectorAll('.shot img'));
  var lb=document.getElementById('lb'), big=document.getElementById('lbimg'),
      cap=document.getElementById('lbcap'), i=0;
  function show(n){
    if(n<0)n=imgs.length-1; if(n>=imgs.length)n=0; i=n;
    big.src=imgs[i].src; cap.textContent=(i+1)+' / '+imgs.length+'  ·  '+imgs[i].alt;
  }
  imgs.forEach(function(im,n){
    im.parentNode.addEventListener('click',function(){ show(n); lb.classList.add('on'); });
  });
  function close(){ lb.classList.remove('on'); big.src=''; }
  document.getElementById('lbx').onclick=close;
  document.getElementById('lbp').onclick=function(e){e.stopPropagation();show(i-1);};
  document.getElementById('lbn').onclick=function(e){e.stopPropagation();show(i+1);};
  lb.addEventListener('click',function(e){ if(e.target===lb) close(); });
  document.addEventListener('keydown',function(e){
    if(!lb.classList.contains('on'))return;
    if(e.key==='Escape')close();
    if(e.key==='ArrowLeft')show(i-1);
    if(e.key==='ArrowRight')show(i+1);
  });
})();
"""


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;"))


def img_src(fn, embed):
    if not embed:
        return "shots/" + fn
    data = (SHOTS / fn).read_bytes()
    return "data:image/png;base64," + base64.b64encode(data).decode()


def build(embed):
    parts = []
    A = parts.append

    A('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">')
    A('<meta name="viewport" content="width=device-width,initial-scale=1">')
    A('<title>墨核 AI Studio (InkCore) · 功能画廊</title>')
    A('<meta name="description" content="墨核 AI Studio 桌面端 AI 助手 —— '
      '对话 / 生图 / 代码运行 / Agent 编排 / 本地模型，数据全部留在本机。">')
    A(f'<style>{CSS}</style></head><body>')

    # hero
    A('<div class="hero"><div class="wrap">')
    A(f'<div class="badge">{VERSION} · Windows 桌面端</div>')
    A('<h1>墨核 AI Studio · 功能画廊</h1>')
    A('<p>一个装在本机的全能 AI 助手：写作、生图、跑代码、Agent 编排、'
      '本地模型全都有。API Key 和对话数据只存在你自己电脑上，不上传任何服务器。</p>')
    A('<div class="btns">')
    A(f'<a class="btn btn-main" href="{REL}/InkCore-Setup.exe">⬇ 下载安装版'
      '<small>推荐 · 双击安装即可用</small></a>')
    A(f'<a class="btn btn-sec" href="{REL}/InkCore-win.zip">📦 免安装 ZIP'
      '<small>解压即用 · 绿色版</small></a>')
    A(f'<a class="btn btn-sec" href="{REL}/InkCore-src.zip">🐍 源码 ZIP'
      '<small>自己跑 Python</small></a>')
    A('</div>')
    A(f'<div class="tip">全部下载走 GitHub Releases · '
      f'<a href="https://github.com/{REPO}" style="color:var(--ac2)">github.com/{REPO}</a>'
      ' · 首次启用本地模型会自动拉取约 1.1GB 权重</div>')
    A('<div class="stats">')
    for n, t in STATS:
        A(f'<div class="stat"><b>{n}</b><span>{t}</span></div>')
    A('</div></div></div>')

    # nav
    A('<div class="nav"><div class="nav-in">')
    for key, name, _ in SECTIONS:
        A(f'<a href="#{key}">{name}</a>')
    A('<a href="#log">本次更新</a><a href="#install">安装方式</a>')
    A('</div></div>')

    A('<div class="wrap">')

    # sections
    for key, name, desc in SECTIONS:
        items = [s for s in SHOTS_META if s[1] == key]
        if not items:
            continue
        A(f'<section id="{key}"><div class="sec-h"><h2>{name}</h2><em>{esc(desc)}</em></div>')
        A('<div class="grid">')
        for fn, _k, title, body, tags in items:
            src = img_src(fn, embed)
            A('<figure>')
            A(f'<div class="shot"><img src="{src}" alt="{esc(title)}" loading="lazy"></div>')
            A(f'<figcaption><b>{esc(title)}</b><p>{esc(body)}</p><div class="tags">')
            for t in tags:
                A(f'<span class="tag">{esc(t)}</span>')
            A('</div></figcaption></figure>')
        A('</div></section>')

    # changelog
    A('<section id="log"><div class="sec-h"><h2>本次更新</h2>'
      f'<em>{VERSION} · 共 {len(CHANGELOG)} 项改动</em></div>')
    A('<div class="log"><ol>')
    for t, d in CHANGELOG:
        A(f'<li><b>{esc(t)}</b><span>{esc(d)}</span></li>')
    A('</ol></div></section>')

    # install
    A('<section id="install"><div class="sec-h"><h2>安装方式</h2>'
      '<em>三选一，推荐第一种</em></div><div class="cols">')

    A('<div class="col"><h3>① 安装版 exe</h3><ol>'
      f'<li>点上方「下载安装版」，拿到 <code>InkCore-Setup.exe</code></li>'
      '<li>双击运行，一路下一步</li>'
      '<li>桌面出现「墨核 AI Studio」图标，双击启动</li>'
      '<li>首次进入先到设置里填一个模型 API Key</li>'
      '</ol><p style="font-size:12.5px;color:var(--tx3);margin-top:12px">'
      'Windows 可能提示「未知发布者」，点「更多信息 → 仍要运行」即可（未做代码签名）。</p></div>')

    A('<div class="col"><h3>② 免安装 ZIP</h3><ol>'
      f'<li>下载 <code>InkCore-win.zip</code></li>'
      '<li>解压到任意目录（路径别带中文最稳）</li>'
      '<li>双击里面的 <code>InkCore.exe</code></li>'
      '</ol><p style="font-size:12.5px;color:var(--tx3);margin-top:12px">'
      '不写注册表，删目录即卸载。适合放 U 盘或公司电脑。</p></div>')

    A('<div class="col"><h3>③ 源码运行</h3>'
      '<p style="font-size:13.4px;color:var(--tx2)">需要 Python 3.11+：</p>'
      '<pre><code>git clone https://github.com/' + REPO + '.git\n'
      'cd InkCore\n'
      'pip install -r requirements.txt\n'
      'python desktop_app.py</code></pre>'
      '<p style="font-size:12.5px;color:var(--tx3);margin-top:10px">'
      '只想开网页版就跑 <code>python app.py</code>，浏览器访问 '
      '<code>http://127.0.0.1:7860</code>。</p></div>')

    A('</div></section>')

    A('</div>')  # wrap

    A(f'<footer>墨核 AI Studio (InkCore) {VERSION} · '
      f'<a href="https://github.com/{REPO}">GitHub 仓库</a> · '
      f'<a href="https://github.com/{REPO}/releases">全部版本</a><br>'
      '本页由 tools/build_gallery.py 自动生成 · 所有截图取自真实运行界面</footer>')

    # lightbox
    A('<div id="lb"><button class="x" id="lbx">&times;</button>'
      '<button class="ar prev" id="lbp">&#8249;</button>'
      '<img id="lbimg" alt=""><button class="ar next" id="lbn">&#8250;</button>'
      '<div class="cap" id="lbcap"></div></div>')

    A(f'<script>{JS}</script></body></html>')
    return "".join(parts)


def main():
    n = len(SHOTS_META)
    missing = [s[0] for s in SHOTS_META if not (SHOTS / s[0]).exists()]
    if missing:
        raise SystemExit("缺少截图: " + ", ".join(missing))

    pages = ROOT / "docs" / "index.html"
    pages.write_text(build(embed=False), encoding="utf-8")
    print(f"[1/2] docs/index.html        {pages.stat().st_size/1024:8.1f} KB  (外链图片 · GitHub Pages 用)")

    single = ROOT / "ui_gallery.html"
    single.write_text(build(embed=True), encoding="utf-8")
    print(f"[2/2] ui_gallery.html        {single.stat().st_size/1024/1024:8.2f} MB  (内嵌 base64 · 离线单文件)")
    print(f"共嵌入 {n} 张截图，分 {len(SECTIONS)} 个分区。")


if __name__ == "__main__":
    main()
