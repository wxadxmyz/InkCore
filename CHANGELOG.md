# 更新日志

## v1.1.0 — 工具协议版（2026-11-18）

把"关键词猜工具"升级为"模型按 Schema 主动发起带参数的工具调用"，是全链路最值钱的一步。

### 新增 core 工具内核
- **Tool Registry**：新增 `core/tools/`，13 个工具统一 `{name, description, json_schema, permission, timeout, run}` 描述，统一 `{ok, data, error}` 返回契约。
- **迁移 6 个旧工具**：search / image / code / terminal / doc / write，行为不变，仅套 Schema 与契约。
- **新增 7 个工程工具**：`read_file` / `write_file` / `edit_file`（行级替换）/ `glob` / `grep` / `list_dir` / `http_fetch`，均带路径白名单护栏。
- **Function Calling 协议**：新增 OpenAI 兼容 `tools` / `tool_calls` 适配层，收敛 DeepSeek / Qwen / GLM / SiliconFlow / OpenRouter 差异；非法 JSON 单调用丢弃不崩溃。
- **观察—修正闭环**：工具结果（含错误）回填给模型，模型据真实结果作答或换工具——这是 M3 失败自愈的基础。
- **兜底与兼容**：`USE_TOOL_CALLS` 开关（`config.agent.use_tool_calls`）可一键退回旧路由；本地 1.5B 模型 / 关闭 LLM 时自动走关键词兜底，前端零改动。
- **安全护栏**：新增 `core/security/guard.py` 路径白名单，工程工具限制在应用目录与用户数据目录内（完整审批/审计留待 M5）。

### 测试与文档
- 新增 `V2 架构设计.md`（模块边界 / 接口契约 / 迁移策略）。
- 新增 `tests/test_tools.py`（30+ 用例，覆盖 Registry / 协议解析 / 护栏 / 错误回填 / Agent 兜底）。
- 全套 pytest 从 21 → 50+ 条。

### 版本
- `APP_VERSION` / `version.json` 升级至 `1.1.0`。

## v1.0.1 — 止血版（2026-11-18）

修复 v1.0.0 中三个已暴露给用户的严重缺陷，并补上工程化地基。

### 严重缺陷修复
- **搜索链接失效**：补上缺失的 `parse_qs` / `urlparse` 导入，联网搜索结果现在给出真实可点击的 URL；同时拦截 `javascript:` 等危险 scheme。
- **跑代码在安装包里失效**：`run_code()` 不再硬编码 `python3`，优先使用当前进程解释器（`sys.executable`），Windows 打包版可执行 Python 代码。
- **PDF 上传静默失败**：改用纯 Python 的 `pypdf` 提取文本，不再依赖 Windows 版没有的 poppler/`pdftotext`。
- **Agent 在本地模型下残废**：`llm_pick_tool()` / `agent_run()` 的可用性判断统一走 `_llm_usable()`，本地内置模型与 Ollama 免 Key 路径现在也能让 LLM 选工具、做结果合成（7a）。

### 工程化
- 数据落盘改原子写 + 线程锁，避免多标签并发时读到半截 JSON。
- 新增 MIT `LICENSE`。
- 新增 `tests/` 冒烟测试（20+ 用例）与 `.github/workflows/ci.yml`（语法检查 + ruff 致命错误 + pytest）。

### 版本
- `APP_VERSION` / `version.json` 升级至 `1.0.1`。
