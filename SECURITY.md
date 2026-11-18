# 墨核 AI Studio 安全说明（v1.4.0 / M5）

> 配套里程碑 M5「安全门控」。目标：让软件"敢开放远程访问"的底线能力就绪。
> 设计原则：**默认安全、策略可降级、全程可审计**。

## 1. 命令执行：从字符串黑名单到白名单

旧版用 `BLOCKLIST` 字符串匹配，容易被 `rm  -rf`（多空格）、`base64 -d | bash`、`cmd && rm` 等绕过。v1.4.0 主路径改为：

1. **危险操作符拦截**：`&&`、`||`、`;`、`|`、`$(...)`、反引号、`>`/`<`、换行、`\x`、`%0a` 等一律拒绝。
2. **shlex 分词**：失败（未闭合引号/转义混淆）直接拒绝。
3. **路径穿越检查**：任意 token 含 `../` / `/..` 段拒绝。
4. **危险 token 拦截**：`rm/dd/mkfs/sudo/curl/base64/...` 出现在任意位置拒绝。
5. **只读白名单**：仅 `ls/pwd/cat/df/du/grep/git/...` 等只读命令放行。
6. **shell=False 执行**：白名单命令按 token 列表直接执行，不做二次 shell 解释。

内置玩法（清理预览、连接 B 站）用的是**硬编码固定命令**，走 `run_terminal_raw`，不接受任何用户输入拼接，仍记审计。

## 2. 代码执行隔离

- 用户/Agent 提交的 Python 代码写到 `~/MoHeAI/_sandbox/`，`cwd` 指向该目录，执行完即删——相对路径的读写被限定在此工作区。
- 单轮超时 20 秒；每次调用写入审计日志。

## 3. 工具分级与审批

每个工具有 `permission` 等级：`read` / `write` / `exec` / `network`。决策由 `config.security` 控制：

| 字段 | 默认 | 含义 |
|---|---|---|
| `mode` | `balanced` | `strict` / `balanced` / `permissive`；permissive 全放行（回滚用） |
| `auto_approve` | 只读+创作类工具 | 名单内工具直接放行 |
| `require_confirm` | `["write","exec","network"]` | 这些**风险等级**需用户确认 |
| `deny` | `[]` | 名单内工具直接禁用 |
| `allow_network` | `false` | 是否允许联网类命令（联网仍需审批） |
| `allow_outside_roots` | `false` | 是否允许访问白名单目录之外的路径 |
| `bind_loopback_only` | `true` | 未开鉴权时禁止绑定非回环地址 |

> 说明：桌面端当前为本地单机运行，审批策略以配置与审计落地；弹窗式交互属后续 PWA/远程场景，需先有鉴权（见第 5 节）。

## 4. 审计日志

- 位置：`~/MoHeAI/audit.jsonl`，单行 JSON、append-only。
- 每条记录：`ts`、`iso`、`session`、`tool`、`risk`、`arguments`（摘要，避免写全文密钥）、`ok`、`error`、`blocked`。
- 回放：`GET /api/audit`（全部，最近 500 条）或 `GET /api/audit?session=<id>`（单次 Agent 运行）。
- 典型的"一次 Agent 运行"复盘：前端把会话 id 带上，即可按时间顺序看到每一次工具调用与拦截。

## 5. 远程访问前置

- 服务默认只绑定 `127.0.0.1`。
- 若通过 `INKCORE_HOST=0.0.0.0` 要求绑定非回环地址，必须先在设置里开启 `auth.enabled=true`，否则自动回退到 `127.0.0.1` 并打印告警。
- 生产远程访问建议叠加 HTTPS 或 Tailscale，不要裸奔公网。

## 6. 回滚

所有策略走 `config.security`，把 `mode` 改成 `permissive`、`require_confirm` 清空即可临时退回 v1.3.0 行为；代码层保留 `v1.3.0` tag 作为回滚点。
