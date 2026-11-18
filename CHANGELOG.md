# 更新日志

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
