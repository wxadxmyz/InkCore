# -*- coding: utf-8 -*-
"""append-only 审计日志（M5）。

记录每一次工具/命令调用：时间、工具名、风险等级、参数摘要、结果、是否被拦。
只追加不改写，单行 JSON（JSONL），便于逐行回放一次 Agent 运行的全部动作。
"""
import json
import os
import threading
import time
from pathlib import Path

_LOCK = threading.Lock()


class AuditLog:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, *, tool: str, risk: str = "read", arguments=None,
               ok: bool = True, error: str = "", blocked: bool = False,
               session_id: str = "", extra=None) -> dict:
        entry = {
            "ts": round(time.time(), 3),
            "iso": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()),
            "session": session_id or "",
            "tool": tool,
            "risk": risk,
            "arguments": _summarize(arguments),
            "ok": bool(ok),
            "error": str(error)[:500],
            "blocked": bool(blocked),
        }
        if extra:
            entry["extra"] = extra
        line = json.dumps(entry, ensure_ascii=False)
        with _LOCK:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        return entry

    def replay(self, session_id: str = ""):
        """按顺序回放（可选按 session 过滤）。文件不存在返回空列表。"""
        if not self.path.exists():
            return []
        out = []
        with _LOCK:
            for line in self.path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    e = json.loads(line)
                except Exception:
                    continue
                if session_id and e.get("session") != session_id:
                    continue
                out.append(e)
        return out

    def clear(self):
        """仅供测试/用户主动清空；正常路径不会调用。"""
        with _LOCK:
            self.path.write_text("", encoding="utf-8")


def _summarize(arguments, max_len=600):
    """把参数压成短字符串，避免审计日志过大或写入密钥全文。"""
    if arguments is None:
        return ""
    try:
        text = json.dumps(arguments, ensure_ascii=False)
    except Exception:
        text = str(arguments)
    if len(text) > max_len:
        return text[:max_len] + "…"
    return text
