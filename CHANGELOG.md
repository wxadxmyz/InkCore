# 更新日志

## v2.0.0 — 生态版（2026-11-19）

里程碑 M6 收官，从"会干活的 Agent"升级为"可外接生态的平台"，版本正式跨入 2.0。

### MCP 客户端
- 新增 `core/mcp/client.py`：JSON-RPC 2.0 最小客户端，支持 stdio（本地子进程）与 Streamable-HTTP 两种传输。
- `initialize → tools/list → tools/call` 全链路；远程工具用 `mcp_<server>_<name>` 前缀转成墨核 ToolSpec，直接注册进 Agent 注册表——模型无需感知工具来自本地还是外部 Server。
- 新增 `GET /api/mcp/servers`、`POST /api/mcp/refresh`；配置写在 `config.mcp.servers`。

### Skill 包规范
- 新增 `core/skills/pack.py`：`SKILL.md`（frontmatter 元数据 + Markdown 指令 + 可选 scripts/references）。
- 纯标准库解析 YAML 风格 frontmatter，不引入 PyYAML；支持目录/zip 导入与 zip 导出，跨机器分享。
- 新增 `POST /api/skill/validate`、`/api/skill/import`、`/api/skill/export`。

### 子 Agent / 并行
- 新增 `core/agent/subagent.py`：多任务在线程池并行执行，各自独立上下文，单任务超时/失败互相隔离。
- 只把结论摘要回传主 Agent（`summarize_for_parent`），工具轨迹留在子上下文，主对话不被淹没。
- 新增 `POST /api/subagent`；配置写在 `config.subagent`。

### 验证
- py_compile / ruff 全绿；pytest **129 条全过**（新增 M6 16 条，MCP/Skill/子Agent 全用 mock，不依赖真实 Server/网络）。

## v1.4.0 — 安全版（2026-11-19）

把"敢不敢开放给外人用"的底线补齐——M5 给工具调用装上白名单、审批与审计。

### 命令安全（替换字符串黑名单）
- 新增 `core/security/shell.py`：shlex 分词 + 只读命令白名单 + 危险参数/操作符拦截；执行改为 `shell=False` 按 token 运行，杜绝 shell 注入。
- 8 类绕过全部被拦：`rm  -rf` 多空格、base64 解码执行、`cmd && rm`、`curl | sh`、路径穿越 `../`、命令替换 `$(...)`、超长命令、编码混淆。
- 内置"清理电脑/连接 B 站"等玩法改走固定的 `run_terminal_raw`（仅硬编码安全命令，仍记审计），不被白名单误伤。

### 审计日志（append-only）
- 新增 `core/security/audit.py`：每次工具/命令调用记录 时间/风险等级/参数摘要/结果/是否拦截，单行 JSONL 只追加不改写。
- 新增 `GET /api/audit?session=xxx`：按会话回放一次 Agent 运行的全部动作。

### 分级与审批
- 新增 `core/security/policy.py`：工具按 read/write/exec/network 分级，决策 allow/confirm/deny；策略全走 `config.security`，可临时降级（回滚到 v1.3.0 行为）。
- 代码执行隔离到 `~/MoHeAI/_sandbox` 临时工作区 + 20s 超时；未开鉴权时禁止绑定非 127.0.0.1（`INKCORE_HOST` 可被 `auth.enabled` 把关）。

### 验证
- py_compile / ruff 全绿；pytest **113 条全过**（新增 M5 25 条）。
- 8 条绕过样例逐条验证被拦；只读命令白名单验证不误伤。

## v1.3.0 — 上下文版（2026-11-19）

解决"聊久了失忆、文档检索不准"——M2/M3 让模型会干活，M4 让它记得住、找得准。

### Token 预算与滚动摘要
- 新增 `core/context/budget.py`：按「系统+记忆 15% / 知识 30% / 近期对话 40% / 摘要 15%」分配预算，替代粗暴的 `history[-12:]` 硬截。
- 超预算的旧对话轮次压缩成摘要（抽取式兜底，不额外调 LLM），原文不丢、关键信息保留。
- 窗口大小读 `llm.context_window`（默认 8192）；`context.engine=legacy` 可一键退回旧行为。

### 结构化记忆 v2
- 新增 `core/context/memory_v2.py`：事实带 type/entity/value/confidence/source/ts，同类去重、可按类型/实体检索。
- `memory.json` 里 `__v2` 与 v1 字段共存，旧版读 v1 照常工作——非破坏性迁移。
- 新增 `tools/migrate_memory.py`：`--dry-run` 预览 / `--reverse` 反向导出。

### 混合检索与引用
- 新增 `core/context/retrieval.py`：字符 bigram + BM25 融合，替代"数查询字符是否出现"的伪检索（长文档几乎全命中）。
- 结果带 `[文档名#片段N]` 出处标注；预留 embedding 接口（注入 `embed_score_fn` 即三路融合）。

### 验证
- py_compile / ruff 全绿；pytest **88 条全过**（M1 21 + M2 29 + M3 15 + M4 23）。
- 端到端：3 文档中只问 1 份 → 命中正确并带出处；记忆跨 20 轮保留；上下文不超窗口。

## v1.2.0 — ReAct 版（2026-11-19）

M2 让模型会调工具，M3 让模型会**自己决定调几次、失败怎么办**——从这里开始才真正像个 Agent。

### ReAct 多轮循环内核
- 新增 `core/agent/react.py`：真正的 `while` 循环，模型每轮决定「继续调工具」还是「给最终答案」，不再是 M2 的单轮线性执行。
- **失败自愈**：工具返回错误时把错误回填给模型，模型自主换工具或换思路重试。
- **步骤间变量传递**：`observations` 观察表让后续步骤能引用前面工具的结果，不再各跑各的。
- **护栏**：`max_steps=12`、总工具调用上限、重复调用检测，防止模型绕圈跑飞。
- **停止与断点**：`threading.Event` 实现 1 秒内停止（无孤儿进程）；checkpoint 落盘，中断重连跳过已完成步骤不重复执行。

### SSE 实时事件流
- 新增 `/api/agent_stream`：实时推送 `plan_update` / `tool_call` / `tool_result` / `error` / `done`。
- 新增 `/api/agent/stop`：按 run_id 停止指定运行。
- `done` 事件携带最终 reply——前端一次拿到结果，**不重复执行一次 Agent**（写操作类工具尤其重要）。

### 前端任务可视化
- Agent 面板新增「任务清单 / 工具时间线」：每步工具调用、成功/失败、耗时实时折叠展示。
- 运行按钮增加「⏹ 停止」，支持中途打断。

### 兼容与验证
- `run_agent` / `agent_run_v2` 接口保持兼容；`use_react` 开关可退回 M2 单轮，`use_tool_calls` 可退回 M1 旧路由。
- py_compile / ruff 全绿；pytest **65 条全过**（M1 21 + M2 29 + M3 15）。

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
