# 墨核 AI Studio 生态扩展（v2.0.0 / M6）

> 配套里程碑 M6「生态与扩展」。本版把墨核从单机 Agent 升级为可外接生态的平台。

## 1. MCP 客户端

MCP（Model Context Protocol）让墨核直接复用外部工具生态（文件系统、浏览器、数据库、第三方 API）。

### 配置

在 `~/MoHeAI/config.json` 的 `mcp.servers` 里添加：

```json
{
  "mcp": {
    "servers": [
      {"name": "fs", "transport": "stdio", "command": ["npx", "-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed"]},
      {"name": "remote", "transport": "http", "url": "https://your-mcp-server/mcp", "headers": {"Authorization": "Bearer xxx"}}
    ]
  }
}
```

### 使用

- `POST /api/mcp/refresh`：连接所有 Server，把工具注册进 Agent（`GET /api/mcp/servers` 可先查看工具有哪些）。
- 之后 Agent 即可按 Schema 调用 `mcp_fs_read_file` 这类工具，与本地工具一视同仁。
- 远程工具统一按 `read` 权限接入，细粒度鉴权由 MCP Server 侧负责；连接失败会写审计日志，不影响本地工具。

## 2. Skill 包（SKILL.md）

一个 Skill 包是可分享的能力单元：

```
my-skill/
  SKILL.md          # 必需
  scripts/          # 可选脚本
  references/       # 可选参考资料
```

`SKILL.md` 格式：

```markdown
---
name: 起名器
description: 为人物生成有韵味的名字
version: 1.2.0
author: 你
tags: 创作, 命名
permission: read
---

请为人物起 3 个名字，风格清冷。
每行一个名字。
```

- `POST /api/skill/validate` 传 `{"text": "..."}` 校验格式。
- `POST /api/skill/import` 上传 `.zip` 安装。
- `POST /api/skill/export` 传 `{"id": "skill_xxx"}` 导出 `.zip` 分享给别人。

## 3. 子 Agent / 并行

长任务可拆给多个子 Agent 并行处理，每个子任务独立上下文，只回传结论：

```json
POST /api/subagent
{
  "goals": [
    {"goal": "调研 A 竞品并总结", "context": "背景..."},
    {"goal": "调研 B 竞品并总结"}
  ]
}
```

返回 `results`（每个子任务的状态/结论/耗时）与 `summary`（拼好的结论摘要）。单个子任务超时或失败不会拖垮其他任务；参数在 `config.subagent` 调整（默认 3 并发、单任务 120s）。

## 4. SSE 事件协议（定稿）

`/api/agent_stream` 的事件类型：`meta` / `plan_update` / `tool_call` / `tool_result` / `token` / `error` / `done`。`done` 事件携带最终 `reply`，前端无需二次请求。

## 5. 版本与回滚

- 2.0 为破坏性版本，建议保留 `v1.4.0` 维护分支 3 个月。
- M1–M5 的回滚开关（如 `context.engine=legacy`、工具调用关键词兜底）继续保留，作为存量用户的安全网，未在 2.0 中冒进删除。
