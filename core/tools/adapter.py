# -*- coding: utf-8 -*-
"""tool_calls 协议适配层：把模型的结构化调用请求解析成可执行指令，
再把执行结果回填成标准 tool 消息。各家 OpenAI 兼容 API 的差异在此收敛。

设计的两条底线：
1. 任何异常都不允许冒泡到调用方——解析失败一律返回 None / 丢弃该调用，交给 tool_loop 兜底。
2. embedded:// 本地模型没有 tool_calls 通道，直接返回 None。
"""
import json
import re

try:
    import requests
except ImportError:  # 单测环境可能未装，HTTP 路径才会用到
    requests = None


# ---------- Schema ----------
def to_openai_tools(specs) -> list:
    """ToolSpec 列表 / dict 列表 -> OpenAI tools 数组。"""
    out = []
    for s in specs:
        if hasattr(s, "to_openai"):
            out.append(s.to_openai())
        elif isinstance(s, dict) and "name" in s:
            out.append({
                "type": "function",
                "function": {
                    "name": s["name"],
                    "description": s.get("description", ""),
                    "parameters": s.get("parameters", {"type": "object", "properties": {}}),
                },
            })
    return out


# ---------- 解析模型返回的 tool_calls ----------
def _coerce_args(raw) -> dict:
    """arguments 可能是 dict、JSON 字符串、或带代码围栏的字符串。"""
    if isinstance(raw, dict):
        return raw
    if raw is None:
        return {}
    if not isinstance(raw, str):
        raise ValueError("arguments 类型非法")
    s = raw.strip()
    # 容忍 ```json ... ``` 围栏
    fence = re.match(r"^```(?:json)?\s*(.*?)\s*```$", s, re.DOTALL)
    if fence:
        s = fence.group(1).strip()
    d = json.loads(s)
    if not isinstance(d, dict):
        raise ValueError("arguments 不是 JSON 对象")
    return d


def parse_tool_calls(message: dict) -> list:
    """从 assistant message 解析出 [{id,name,arguments}]。

    非法 JSON 的单个调用被丢弃并附带 _parse_error，不整体崩溃。
    """
    calls = []
    for tc in (message or {}).get("tool_calls") or []:
        try:
            fn = tc.get("function") or {}
            name = fn.get("name", "")
            call_id = tc.get("id") or ""
            if not name:
                continue
            args = _coerce_args(fn.get("arguments"))
            calls.append({"id": call_id, "name": name, "arguments": args})
        except Exception as e:
            calls.append({
                "id": (tc.get("id") if isinstance(tc, dict) else "") or "",
                "name": (tc.get("function", {}).get("name", "") if isinstance(tc, dict) else ""),
                "arguments": {},
                "_parse_error": f"参数解析失败：{e}",
            })
    return calls


# ---------- 回填 tool 消息 ----------
def build_tool_messages(calls: list, results: list) -> list:
    """calls 与 results 等长；results 元素为统一契约 {ok,data,error}。"""
    msgs = []
    for call, res in zip(calls, results):
        res = res or {}
        if res.get("ok"):
            data = res.get("data", "")
            if not isinstance(data, str):
                data = json.dumps(data, ensure_ascii=False)
            content = data[:12000]
        else:
            content = "[工具执行失败] " + str(res.get("error") or "未知错误")[:2000]
        msgs.append({
            "role": "tool",
            "tool_call_id": call.get("id", ""),
            "name": call.get("name", ""),
            "content": content,
        })
    return msgs


def assistant_message(content, calls: list) -> dict:
    """构造带 tool_calls 的 assistant 消息（回填时放进历史，保持对话合法）。"""
    tc = []
    for c in calls:
        tc.append({
            "id": c.get("id", ""),
            "type": "function",
            "function": {
                "name": c.get("name", ""),
                "arguments": json.dumps(c.get("arguments", {}), ensure_ascii=False),
            },
        })
    return {"role": "assistant", "content": content or "", "tool_calls": tc}


# ---------- 默认 HTTP transport（可注入替换以便测试） ----------
def _default_transport(messages, tools, cfg, timeout=90):
    """OpenAI 兼容 /chat/completions。返回 response dict 或 None。

    签名与注入的 transport 一致：(messages, tools, cfg)。
    """
    if requests is None:
        return None
    base = (cfg.get("base_url") or "").rstrip("/")
    if not base or base.startswith("embedded://"):
        return None  # 本地内置模型无 tool_calls 通道
    # 与 app.py 的 _auth_required 同口径：本地地址免 Key
    low = base.lower()
    local = ("ollama" in low or "localhost" in low or "127." in low or "0.0.0.0" in low)
    if not cfg.get("api_key") and not local:
        return None
    headers = {"Content-Type": "application/json"}
    if cfg.get("api_key"):
        headers["Authorization"] = f"Bearer {cfg['api_key']}"
    payload = {
        "model": cfg.get("model", "gpt-4o-mini"),
        "messages": messages,
        "temperature": cfg.get("temperature", 0.3),
    }
    if tools:  # 第二次纯文本调用时 tools 为空，不发该字段
        payload["tools"] = tools
        payload["tool_choice"] = "auto"
    try:
        r = requests.post(base + "/chat/completions", headers=headers,
                          json=payload, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def call_tools_llm(messages, specs, cfg, transport=None) -> dict | None:
    """发起一次带 tools 的 LLM 调用。

    返回 {"text": str, "tool_calls": [...]}；本地模型 / 不支持 / 失败返回 None（触发兜底）。
    transport(messages, tools, cfg) 可注入以便测试；签名与 _default_transport 一致。
    """
    if not cfg or not cfg.get("enabled"):
        return None
    if (cfg.get("base_url") or "").startswith("embedded://"):
        return None
    tools = to_openai_tools(specs or [])
    fn = transport or _default_transport
    try:
        resp = fn(messages, tools, cfg)
    except Exception:
        return None
    if not resp:
        return None
    try:
        choice = (resp.get("choices") or [{}])[0]
        msg = choice.get("message") or {}
        text = msg.get("content") or ""
        calls = parse_tool_calls(msg)
        return {"text": text, "tool_calls": calls}
    except Exception:
        return None
