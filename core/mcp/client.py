# -*- coding: utf-8 -*-
"""MCP 客户端（M6）：让墨核复用外部 MCP Server 的工具生态。

MCP = Model Context Protocol，JSON-RPC 2.0。本模块实现最小可用客户端：
  - StdioTransport：启动本地子进程，stdin/stdout 交换换行分隔的 JSON-RPC。
  - HttpTransport：向 Streamable-HTTP MCP 端点 POST JSON-RPC。
  - McpClient：initialize → tools/list → tools/call，并把远程工具转成墨核 ToolSpec。

设计约束（与 V2 架构一致）：
  - 纯 Python、不 import app、依赖注入；异常一律吞成结构化错误契约 {ok,data,error}。
  - 工具实现闭包调用 call_tool，可直接注册进现有 Registry，模型无需感知工具来自本地还是远程。
"""
import json
import subprocess
import threading
import uuid
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

try:
    import requests
except ImportError:  # 允许纯 stdio 场景无 requests
    requests = None

from ..tools.registry import ToolSpec


class McpError(Exception):
    pass


class StdioTransport:
    """通过子进程的 stdin/stdout 进行 JSON-RPC 通信（每行一条消息）。"""

    def __init__(self, command: List[str], *, cwd=None, env=None, timeout=20):
        if not command:
            raise McpError("stdio transport 需要 command")
        self.command = command
        self.cwd = cwd
        self.env = env
        self.timeout = timeout
        self._proc = None
        self._lock = threading.Lock()
        self._buf = b""

    def start(self):
        if self._proc and self._proc.poll() is None:
            return
        import os
        e = dict(os.environ)
        if self.env:
            e.update(self.env)
        self._proc = subprocess.Popen(
            self.command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, cwd=self.cwd, env=e, bufsize=0,
        )

    def send(self, payload: dict) -> dict:
        self.start()
        if not self._proc or self._proc.poll() is not None:
            raise McpError("MCP 子进程已退出")
        line = (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")
        with self._lock:
            self._proc.stdin.write(line)
            self._proc.stdin.flush()
            # 逐行读，跳过非 JSON 行（有些 server 会往 stdout 打日志）
            while True:
                raw = self._proc.stdout.readline()
                if raw == b"":
                    raise McpError("MCP 子进程关闭了 stdout")
                text = raw.decode("utf-8", "replace").strip()
                if not text:
                    continue
                try:
                    msg = json.loads(text)
                except Exception:
                    continue
                if "id" in payload and msg.get("id") == payload["id"]:
                    return msg

    def close(self):
        if self._proc:
            try:
                self._proc.terminate()
            except Exception:
                pass
            self._proc = None


class HttpTransport:
    """Streamable-HTTP MCP：POST JSON-RPC 到单个端点。"""

    def __init__(self, url: str, *, headers=None, timeout=20):
        if requests is None:
            raise McpError("HttpTransport 需要 requests")
        self.url = url
        self.headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
        if headers:
            self.headers.update(headers)
        self.timeout = timeout

    def send(self, payload: dict) -> dict:
        r = requests.post(self.url, json=payload, headers=self.headers, timeout=self.timeout)
        r.raise_for_status()
        text = r.text.strip()
        # Streamable HTTP 可能返回 SSE；取第一条 data: 里的 JSON
        if text.startswith("event:") or "\ndata:" in text or text.startswith("data:"):
            for line in text.splitlines():
                if line.startswith("data:"):
                    return json.loads(line[5:].strip())
            raise McpError("SSE 响应中未找到 data 帧")
        return json.loads(text)

    def close(self):
        pass


@dataclass
class McpTool:
    name: str
    description: str
    input_schema: dict
    server_name: str = ""


class McpClient:
    """一个 MCP Server 的客户端会话。"""

    def __init__(self, transport, *, name="mcp"):
        self.transport = transport
        self.name = name
        self._id = 0
        self.initialized = False

    def _next_id(self):
        self._id += 1
        return self._id

    def _request(self, method: str, params: dict = None) -> dict:
        msg = {"jsonrpc": "2.0", "id": self._next_id(), "method": method}
        if params is not None:
            msg["params"] = params
        resp = self.transport.send(msg)
        if "error" in resp:
            raise McpError(f"{method} 失败：{resp['error']}")
        return resp.get("result", {})

    def initialize(self):
        result = self._request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "InkCore", "version": "2.0.0"},
        })
        self.initialized = True
        # 通知服务器初始化完成（stdio 下 fire-and-forget，忽略响应）
        try:
            self.transport.send({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
        except Exception:
            pass
        return result

    def list_tools(self) -> List[McpTool]:
        if not self.initialized:
            self.initialize()
        data = self._request("tools/list", {})
        tools = []
        for t in data.get("tools", []):
            tools.append(McpTool(
                name=t.get("name", ""),
                description=t.get("description", ""),
                input_schema=t.get("inputSchema") or {"type": "object", "properties": {}},
                server_name=self.name,
            ))
        return tools

    def call_tool(self, name: str, arguments: dict = None) -> dict:
        """统一契约：{ok, data, error}。"""
        try:
            result = self._request("tools/call", {"name": name, "arguments": arguments or {}})
            # MCP 内容块： [{type:text, text:...}] → 拼成文本
            parts = []
            for c in result.get("content", []):
                if isinstance(c, dict) and c.get("type") == "text":
                    parts.append(c.get("text", ""))
            text = "\n".join(parts) if parts else result
            return {"ok": not result.get("isError", False), "data": text,
                    "error": None if not result.get("isError") else str(text)[:500]}
        except Exception as e:
            return {"ok": False, "data": None, "error": f"{type(e).__name__}: {e}"}

    def close(self):
        try:
            self.transport.close()
        except Exception:
            pass


def client_from_config(cfg: dict) -> McpClient:
    """按配置构造客户端。

    cfg: {"name": "...", "transport": "stdio"|"http", "command": [...], "url": "...",
          "cwd": "...", "env": {...}, "headers": {...}, "timeout": 20}
    """
    kind = cfg.get("transport", "stdio")
    name = cfg.get("name", "mcp")
    timeout = cfg.get("timeout", 20)
    if kind == "stdio":
        tr = StdioTransport(cfg.get("command") or [], cwd=cfg.get("cwd"),
                            env=cfg.get("env"), timeout=timeout)
    elif kind == "http":
        tr = HttpTransport(cfg.get("url") or "", headers=cfg.get("headers"), timeout=timeout)
    else:
        raise McpError(f"未知 MCP transport：{kind}")
    return McpClient(tr, name=name)


def to_tool_specs(client: McpClient) -> List[ToolSpec]:
    """把远程 MCP 工具转成墨核 ToolSpec，run 闭包调用 call_tool。"""
    specs = []
    for tool in client.list_tools():
        # 加前缀避免与本地工具重名
        full_name = f"mcp_{client.name}_{tool.name}"
        specs.append(ToolSpec(
            name=full_name,
            description=f"[MCP:{client.name}] {tool.description}",
            parameters=tool.input_schema,
            permission="read",  # 远程工具统一按只读接入；细粒度权限由 server 侧负责
            timeout=30,
            run=(lambda args, _c=client, _n=tool.name: _c.call_tool(_n, args)),
        ))
    return specs
