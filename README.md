<div align="center">

# 墨核 AI Studio (InkCore)

**一个装在自己电脑里的全能 AI 助手**

对话 · 写作 · 生图 · 联网 · 跑代码 · Agent 编排 · 本地离线模型

[![Release](https://img.shields.io/github/v/release/wxadxmyz/InkCore?label=下载&color=7c6cff)](https://github.com/wxadxmyz/InkCore/releases/latest)
[![Platform](https://img.shields.io/badge/平台-Windows%2010%2F11-0078d4)](https://github.com/wxadxmyz/InkCore/releases/latest)
[![Python](https://img.shields.io/badge/Python-3.11+-3776ab)](https://www.python.org/)
[![Gallery](https://img.shields.io/badge/功能画廊-在线预览-33c9e6)](https://wxadxmyz.github.io/InkCore/)

[**⬇ 下载安装版**](https://github.com/wxadxmyz/InkCore/releases/latest/download/InkCore-Setup.exe) ·
[**📦 免安装 ZIP**](https://github.com/wxadxmyz/InkCore/releases/latest/download/InkCore-win.zip) ·
[**🐍 源码 ZIP**](https://github.com/wxadxmyz/InkCore/releases/latest/download/InkCore-src.zip) ·
[**🖼 功能画廊**](https://wxadxmyz.github.io/InkCore/)

</div>

---

## 这是什么

墨核 AI Studio 是一款 **Windows 桌面端 AI 助手**，以对话为主入口，把日常最常用的 AI 能力收进一个窗口里：写文章、写小说、生成图片、联网查资料、读文档、跑 Python、让 Agent 自动拆解任务、甚至直接连本地模型完全离线跑。

它和网页版 AI 工具最大的区别在三点：

| | 墨核 AI Studio | 常见网页 AI |
|---|---|---|
| **数据归属** | API Key、对话、文档、笔记全部存本机 `~/MoHeAI/`，不上传任何服务器 | 存在服务商云端 |
| **模型选择** | 10 家供应商任选，也可用 Ollama 或内置离线模型，随时切换 | 绑定单一厂商 |
| **能力边界** | 能真实执行终端命令、运行 Python、读写本地文件 | 只能聊天 |

未配置任何 API Key 时，内置模板引擎也能开箱即用；想完全离线，选「本地内置模型」自动下载 1.1GB 量化权重即可。

---

## 快速开始

### 方式一：安装版（推荐）

1. 下载 [**InkCore-Setup.exe**](https://github.com/wxadxmyz/InkCore/releases/latest/download/InkCore-Setup.exe)
2. 双击运行，一路下一步
3. 桌面出现「墨核 AI Studio」图标，双击启动
4. 首次进入到设置里填一个模型 API Key（推荐先用免费的 SiliconFlow）

> Windows 可能提示「未知发布者」，点 **更多信息 → 仍要运行**。这是未做代码签名的正常提示，不是病毒。

### 方式二：免安装绿色版

下载 [**InkCore-win.zip**](https://github.com/wxadxmyz/InkCore/releases/latest/download/InkCore-win.zip) → 解压到任意目录（路径别带中文最稳）→ 双击 `InkCore.exe`。不写注册表，删目录即卸载，适合放 U 盘。

### 方式三：源码运行（开发者）

```bash
git clone https://github.com/wxadxmyz/InkCore.git
cd InkCore
pip install -r requirements.txt

python desktop_app.py     # 原生桌面窗口
# 或
python app.py             # 纯网页版，浏览器访问 http://127.0.0.1:7860
```

---

## 界面总览

三栏布局，所有功能都在一屏之内：

```
┌──────────┬────────────────────────────┬──────────────┐
│  会话列表  │        对话主区域            │   功能抽屉    │
│  ────────  │                            │  (400px)     │
│  搜索      │   多标签页 · 流式输出         │  写作助手     │
│  分组      │   代码块一键复制              │  AI 生图     │
│  重命名    │   数学公式渲染                │  提示词       │
│  删除      │                            │  记忆库       │
│  ────────  │   ┌──────────────────┐     │  知识库       │
│  功能导航   │   │ 会话产物条 (缩略图) │     │  技能        │
│           │   ├──────────────────┤     │  终端 ⛶      │
│           │   │ 快捷 chip 入口     │     │  代码运行 ⛶   │
│           │   ├──────────────────┤     │  Agent ⛶     │
│           │   │ 输入框 🎤 📷 ⬇    │     │  离谱玩法 ⛶   │
│           │   └──────────────────┘     │  设置        │
└──────────┴────────────────────────────┴──────────────┘
                                          ⛶ = 支持全屏覆盖
```

📸 **完整界面截图请看 [在线功能画廊](https://wxadxmyz.github.io/InkCore/)**（14 张实拍图，可点击放大）

---

## 核心功能

### 💬 对话即入口 —— 说人话就行

不用记命令，直接描述需求，后端自动识别意图并路由到对应能力：

| 你想做的 | 直接说一句话 |
|---|---|
| 写短篇 / 小说 | `写一段仙侠短篇，主角叫苏无尘` |
| 漫剧 / 短剧 / 剧本 | `来一个 3 分钟都市短剧脚本` |
| 公众号 / 干货文章 | `帮我写一篇公众号文章：如何高效阅读` |
| 产品文案 | `写一段产品文案：为新款耳机带货` |
| AI 生图 | `画一张赛博朋克小说封面` |
| 生图提示词 | `给我一个古风少女的生图提示词` |
| 联网搜索 | `搜索今天 AI 领域的最新资讯` |
| 翻译 | `把这段英文翻译成中文` |
| 视觉理解 | 点输入框 📷 发送一张图片 |
| 查看记忆 | `记忆`（看已记住的主角名 / 题材 / 风格） |
| **跑代码** | `写一段 Python 并运行` → **自动生成 + 自动填入 + 自动全屏** |
| **执行命令** | `打开终端，执行 ls -la` → **自动唤起终端并全屏** |
| **Agent 任务** | `帮我调研一下竞品并整理成表格` → **自动拆步骤并全屏推进** |
| 角色扮演 | 技能面板新建人设型技能，说「退出角色扮演」结束 |
| 语音输入 | 点输入框 🎤 用麦克风口述 |
| 导出 | 点右上角「⬇ 导出」选 Word / Markdown / PDF / 公众号 HTML |

输入框上方还有 **快捷 chip**：全能助手 / 联网搜索 / 写小说 / 写文章 / AI 生图 / 翻译，点一下就发。

### ✍️ 写作与创作

- **小说 / 剧本**：短篇、长篇、漫剧、短剧、脚本，结构化模板生成，主角名与题材自动进记忆库
- **文章写作**：公众号文章、干货文、随笔、文案，标题 / 正文 / CTA 一应俱全
- **续写与改写**：基于上下文续写、口语化改写、网感润色
- **记忆库**：对话中提到的主角名、题材、风格自动捕获，解决长篇创作丢稿与人设漂移
- **独立 Markdown 编辑器**：顶栏「📝 编辑器」进入 `/md` 全屏写作工作台（详见下文）

### 🎨 AI 生图

- 中文提示词直出，无需背英文咒语
- 配置绘图模型（`gpt-image-1` / `dall-e-3` 等）后出真实 PNG，未配置自动回退 SVG 封面
- 按题材自动配色
- 生成结果自动进 **会话产物条**，随时点开回看

### 🌐 联网与多模态

- **联网搜索**：内置 DuckDuckGo 检索，结果注入上下文后由 LLM 汇总
- **知识库 (RAG)**：上传 PDF / Word / TXT / MD / CSV，本地字符级召回，**无需向量库**。普通聊天说「总结这份合同」会自动参考文档
- **视觉理解**：发送图片由多模态模型识别描述

### 🛠 开发者能力

| 能力 | 说明 |
|---|---|
| **终端** | 真实执行系统命令，危险命令黑名单拦截 + 可选只读沙箱 |
| **代码运行** | Python 真实执行，限时 20 秒 |
| **Agent 编排** | 定义目标 + 多步骤，服务端按 搜索 / 生图 / 代码 / 终端 / 文档 / 写作 工具真实编排 |
| **技能系统** | 创建提示词型 / 人设型技能，按触发词自动路由 |
| **技能市场** | 一键添加精选技能，支持导入 / 导出 JSON、从链接导入社区技能 |

这三个面板（终端 / 代码 / Agent）都支持 **一键全屏覆盖聊天区**，看长输出不再挤在 400px 抽屉里。

### 🎮 离谱玩法（可自建 · 可分享）

内置 6 个开箱即用的小玩法：

| 玩法 | 干什么 |
|---|---|
| 清理电脑 | 只读扫描磁盘占用（不删数据） |
| 搓游戏 | 现场生成可玩 HTML 小游戏，对话内一键打开 |
| 连外部站 | 终端 curl 探活 |
| 下载软件 | 调用终端拉取文件 |
| 讲笑话 | 随机轻松一下 |
| emoji 剧情 | 创意小玩法 |

**v1.0.0 新增**：可以自己写 prompt **新建玩法**，存进本地 `funs.json`；支持 **整包导出 JSON** 分享给别人，也能 **导入** 别人的玩法包。玩法面板同样支持全屏。

---

## 模型支持

### 10 家供应商，随时切换

| 供应商 | 预置模型 | 说明 |
|---|---|---|
| **SiliconFlow** | Qwen2.5-7B、DeepSeek-V3、DeepSeek-R1 等 | 🆓 免费聚合平台，注册送额度，**新手首选** |
| **OpenRouter** | gpt-4o-mini、Claude 3.5 Sonnet、Gemini 2.0 Flash 等 | 🆓 免费聚合平台，一个 Key 通吃多家 |
| **OpenAI** | gpt-4o-mini、gpt-4o、o1、o1-mini、o3-mini | 官方接口 |
| **DeepSeek** | deepseek-chat、deepseek-reasoner、deepseek-coder | 性价比高 |
| **通义千问** | qwen-plus、qwen-turbo、qwen-max、qwen-coder-plus | 阿里云 |
| **Moonshot** | moonshot-v1-8k / 32k / 128k | 长上下文 |
| **智谱 GLM** | glm-4-flash、glm-4、glm-4-plus、glm-4-air | glm-4-flash 免费 |
| **Ollama** | llama3、qwen2.5、deepseek-r1 | 本机 Ollama，完全离线 |
| **本地内置模型** | Qwen2.5-1.5B-Instruct Q4 | **免 Ollama、零 Key、纯离线** |
| **自定义** | 任意 OpenAI 兼容接口 | 填自己的 Base URL |

### Key 管理（v1.0.0 改进）

- **每家供应商独立记 Key** —— 切到 DeepSeek 再切回 OpenAI，两边的 Key 都还在，不会互相覆盖
- **一键继承 Key** —— 勾上「继承主模型 Key」，生图和视觉模型直接复用对话模型的 Key 与 Base URL，省掉重复填三遍
- **按会话选模型** —— 对话头部的模型选择器可为**当前这一个对话**单独指定模型，覆盖全局设置

### 本地内置模型（离线 · 免 Ollama）

设置 → 供应商选「**本地内置模型(离线·免Ollama)**」并启用：

- 内置 `llama-cpp-python` 推理引擎，进程内加载，**不额外占端口、不起第二个服务**
- 首次自动下载量化权重（默认 `Qwen2.5-1.5B-Instruct Q4`，约 1.1GB；另有 0.5B 低内存备选约 0.4GB）
- 下载完成后**完全离线、零 API Key**，断网也能聊
- 权重不打进安装包，所以安装包只有几十 MB

> 后端把 `embedded://local` 视为零 Key 本地推理端点，`_llm_stream` / `_llm_complete` 统一分流：内置模型走 `local_llm.stream`，其余走 OpenAI 兼容 HTTP。流式 / 停止 / 编辑 / 导出 / 多标签全部原样可用；`llama_cpp` 缺失时输出可读错误而非崩溃。

### Ollama 管理（v1.0.0 归位）

Ollama 从独立面板挪进了 **设置 → 本地模型** tab，可以：刷新已装模型列表、一键切换为当前对话模型、拉取新模型、删除不用的权重。

---

## 📝 Markdown 编辑器

顶栏「📝 编辑器」打开独立全屏写作工作台（`/md`），与主程序深度打通：

| 能力 | 说明 |
|---|---|
| **双栏实时预览** | 左写右预览，自研解析器，支持标题 / 加粗 / 斜体 / 删除线 / 列表 / 引用 / 代码块 / 表格 / 分隔线 |
| **公式与高亮** | 集成 KaTeX 数学公式（`$…$` / `$$…$$`）与 highlight.js 代码高亮 |
| **多布局** | 双栏 / 仅编辑 / 仅预览 三种模式切换 |
| **AI 加工** | 选中文字 → ✨润色 / 📌总结 / 🌐翻译 / ➡️续写 / 📝扩充，复用对话侧大模型 |
| **笔记沉淀** | 存入 `~/.MoHeAI/notes/*.md`，防抖自动保存，可重开 / 删除 |
| **对话导入** | 一键把历史会话转成 Markdown 草稿继续写 |
| **七格式导出** | md / txt / html / docx / xlsx / pdf / png 长图 |

> 编辑器 UI 与解析器均为**自研**，仅复用 MIT 许可的 KaTeX / highlight.js / html2canvas 与 python-docx / openpyxl / reportlab，可放心闭源分发。

---

## 其他特性

### 会话与对话体验

- **多标签页**：同时开多个对话，互不干扰
- **会话管理**：搜索、分组、重命名、删除
- **流式输出 + 停止生成**：SSE 实时流，随时点停
- **编辑 + 重新生成**：改掉自己说过的话，重新生成分支
- **一键重发**：每条用户消息旁的 ⟲
- **代码块一键复制**：悬浮右上角「复制」按钮
- **文本朗读 (TTS)**：调用系统语音合成念出回复
- **深色 / 浅色主题**：跟随喜好切换
- **会话产物条**（v1.0.0 新增）：本轮生成的图片、小游戏以缩略图钉在输入框上方，点一下重新打开，可折叠

### 多用户与数据

- **多用户隔离**：顶栏切换 / 新建用户，记忆、会话、技能、知识库完全隔离（`~/MoHeAI/profiles/<用户名>/`）
- **数据备份 / 恢复**：一键导出全部数据，换机器直接还原
- **多格式导出**：Word (.docx) / Markdown (.md) / PDF (.pdf) / 公众号 HTML / XMind

### 桌面集成

- **系统托盘**：常驻托盘，右键菜单可 新建对话 / 显示 / 隐藏 / 打开配置目录 / 退出
- **全局热键**：默认 `Ctrl+Alt+M` 呼出窗口，可在设置里自定义录制
- **语音输入**：Web Speech API 中文口语转文字
- **自动更新**：设置页填更新清单地址，点「检查更新」比对版本

### 安全

- 终端与代码本地执行，内置**危险命令黑名单**（`rm -rf /`、`mkfs`、`dd`、格式化等）+ **时长限制**
- 可开启**只读沙箱**，禁用 `rm/cp/mv/dd` 等写操作
- API Key 仅存本机 `~/MoHeAI/config.json`，不上传任何服务器
- 笔记、文档、对话全部留在本地

---

## v1.0.0 更新内容

| # | 改动 | 说明 |
|---|---|---|
| 1 | **面板宽度统一 400px** | 删掉 340 / 392 的分档逻辑，所有抽屉一个宽度，视觉不再跳动 |
| 2 | **全屏覆盖按钮** | 知识库 / 终端 / 代码 / Agent / 离谱玩法 五个工作型面板可一键铺满聊天区 |
| 3 | **聊天自动唤起面板** | 说「写段代码并运行」自动生成 + 自动填入 + 自动全屏，Agent 与终端同理 |
| 4 | **离谱玩法自建** | 新建 / 删除 / 导出 JSON / 导入 JSON，玩法可以自己攒也可以互相分享 |
| 5 | **每供应商独立记 Key** | 切换供应商不再冲掉上一家的密钥，切回来自动回填 |
| 6 | **新增免费聚合供应商** | SiliconFlow 与 OpenRouter，注册送额度，零成本起步 |
| 7 | **继承 Key 到生图 / 视觉** | 一个勾选框省掉两次重复填写 |
| 8 | **面板空状态引导** | 空面板不再是白板，给出说明与下一步提示 |
| 9 | **会话产物条** | 生成过的图片 / 小游戏钉在输入框上方，点开即回看 |
| 10 | **Ollama 并入设置** | 本地模型作为设置页的一个 tab，不再单占一个功能位 |

---

## 项目结构

```
app.py                后端 (Flask)：意图路由 + 写作引擎 + 终端/代码 + Skill/记忆
                      + LLM/绘图/视觉 + 联网搜索 + RAG + Agent 编排 + 多格式导出
                      + 多用户 + 技能市场 + 玩法 CRUD + 会话产物 + Markdown 后端
local_llm.py          本地内置模型：登记表、自动下载、懒加载、流式生成、优雅降级
desktop_app.py        桌面启动器：Flask 后台线程 + pywebview 窗口 + 托盘 + 全局热键
static/
  index.html          单页主界面
  app.js              前端逻辑（流式渲染、面板、全屏、产物条、设置）
  style.css           样式（400px 面板、全屏动画、产物条）
  md/                 独立 Markdown 编辑器（editor.html / md.css / md.js）
  vendor/             第三方库（KaTeX / highlight.js / html2canvas）
  icon.png / icon.ico 应用图标
docs/                 GitHub Pages 功能画廊（index.html + shots/）
tools/build_gallery.py 画廊生成器（同时产出 docs/ 与 ui_gallery.html）
build.spec            PyInstaller 打包配置（单文件 exe）
build_windows.bat     Windows 一键打包脚本
installer.iss         Inno Setup 安装包脚本
.github/workflows/
  build.yml           打 tag 自动构建 exe / 安装包 / ZIP 并发布 Release
  pages.yml           推 main 自动部署画廊到 GitHub Pages
version.json          自动更新清单
requirements.txt      依赖清单
~/MoHeAI/             用户数据（配置、各 profile 的记忆/会话/技能/知识库/产物/笔记）
```

---

## API 接口一览

后端提供 45+ 个 REST 接口，主要分组：

| 分组 | 接口 |
|---|---|
| 对话 | `/api/chat`、`/api/chat_stream`(SSE)、`/api/conversations`、`/api/conversations/model` |
| 配置 | `/api/config`、`/api/profiles`、`/api/version`、`/api/check_update` |
| 能力 | `/api/image`、`/api/vision`、`/api/search`、`/api/code`、`/api/terminal`、`/api/agent` |
| 知识库 | `/api/docs`、`/api/memory` |
| 技能 | `/api/skills`、`/api/skills/gallery`、`/api/skills/import`、`/api/skills/export`、`/api/skills/import_url` |
| 玩法 | `/api/funs`、`/api/funs/import`、`/api/funs/export` |
| 产物 | `/api/artifacts`、`/output/<path>` |
| 本地模型 | `/api/embedded/status`、`/api/embedded/download`、`/api/ollama/{check,models,pull,use,delete}` |
| 导出 | `/api/export/{md,pdf,docx,wechat,xmind}` |
| 编辑器 | `/md`、`/api/md/status`、`/api/md/ai`、`/api/md/export`、`/api/notes` |
| 备份 | `/api/backup`、`/api/restore` |

---

## 自行打包

### Windows 本机打包

```bat
pip install -r requirements.txt
pyinstaller build.spec
```

产物 `dist\InkCore.exe`（单文件，双击即用，原生窗口无浏览器）。
再用 Inno Setup Compiler 编译 `installer.iss`，得到 `installer\InkCore_Setup_1.0.0.exe`。

或直接双击 `build_windows.bat` 一步到位。

### GitHub Actions 自动打包

推一个 tag 就行：

```bash
git tag v1.0.0
git push --tags
```

Actions 会在 Windows 云机器上自动完成：装依赖 → PyInstaller 打包 exe → InnoSetup 生成安装包 → 压缩绿色版 ZIP → 压缩源码 ZIP → 创建 Release 并上传四个产物。

发布后这些链接永久有效：

```
https://github.com/wxadxmyz/InkCore/releases/latest/download/InkCore-Setup.exe
https://github.com/wxadxmyz/InkCore/releases/latest/download/InkCore-win.zip
https://github.com/wxadxmyz/InkCore/releases/latest/download/InkCore-src.zip
```

### 部署功能画廊

仓库 Settings → Pages → Source 选 **GitHub Actions**，推 main 分支即自动部署到
`https://wxadxmyz.github.io/InkCore/`。

重新生成画廊（换了截图之后）：

```bash
python3 tools/build_gallery.py
```

会同时更新 `docs/index.html`（Pages 用，外链图片）和 `ui_gallery.html`（离线单文件，base64 内嵌）。

### 代码签名（可选）

未签名 exe 在 Win10/11 会被 SmartScreen 拦截。购买代码签名证书后：

```bat
signtool sign /fd SHA256 /td SHA256 /tr http://timestamp.digicert.com /a dist\InkCore.exe
signtool sign /fd SHA256 /td SHA256 /tr http://timestamp.digicert.com /a installer\InkCore_Setup_1.0.0.exe
```

`build.yml` 里已预留签名步骤，取消注释并配置 `CERT_BASE64` / `CERT_PASSWORD` Secrets 即可。

---

## 常见问题

**Q：一定要 API Key 吗？**
不要。未配置时内置模板引擎可用；想要真 AI 又不想花钱，选 SiliconFlow 或 OpenRouter（注册送额度），或者用「本地内置模型」完全离线。

**Q：数据会上传吗？**
不会。所有配置、对话、文档、笔记都在本机 `~/MoHeAI/`。只有你主动调用云端模型时，对话内容才会发给你选的那家供应商。

**Q：Windows 提示"未知发布者"？**
未做代码签名的正常提示。点「更多信息 → 仍要运行」。介意的话可以自行购买证书签名。

**Q：本地内置模型下载很慢？**
权重从 HuggingFace 拉取，国内可能慢。可以改用 Ollama，或先用免费云端供应商。

**Q：终端功能安全吗？**
内置危险命令黑名单 + 执行时长限制，还可在设置里开启「只读沙箱」禁用一切写操作。

**Q：能在 macOS / Linux 上跑吗？**
源码方式可以（`python app.py` 或 `python desktop_app.py`）。预编译的 exe 和安装包只针对 Windows。

---

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | Python 3.11 + Flask + waitress（生产 WSGI，支持并发 SSE） |
| 桌面壳 | pywebview（Windows 调用系统 Edge WebView2）+ pystray + keyboard |
| 前端 | 原生 JS（无框架）+ CSS 变量主题 |
| 本地推理 | llama-cpp-python（进程内加载 GGUF） |
| 文档处理 | python-docx / openpyxl / reportlab / pdfminer / BeautifulSoup |
| 打包 | PyInstaller（单文件 exe）+ Inno Setup 6（安装包） |
| CI/CD | GitHub Actions（自动构建 + Release + Pages） |

---

## 许可与合规

- Markdown 编辑器 UI 与解析器均为自研，未复制任何上游编辑器源码
- 第三方依赖均为 MIT / BSD / Apache 等宽松许可（KaTeX、highlight.js、html2canvas、python-docx、openpyxl、reportlab）
- 可放心用于闭源分发

---

<div align="center">

**墨核 AI Studio v1.0.0**

[功能画廊](https://wxadxmyz.github.io/InkCore/) ·
[下载最新版](https://github.com/wxadxmyz/InkCore/releases/latest) ·
[提交问题](https://github.com/wxadxmyz/InkCore/issues)

</div>
