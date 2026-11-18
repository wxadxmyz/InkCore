# -*- coding: utf-8 -*-
"""Token 预算与滚动摘要。

替换 app.py 里粗暴的 history[-12:] 硬截：按优先级组装上下文，
超预算时把最旧的历史压缩成摘要（原文另存），保证关键信息不丢、不超模型窗口。
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable


def estimate_tokens(text: str) -> int:
    """粗略 token 估算：中文按 1 字≈1.5 token，英文/数字按 4 字符≈1 token。

    宁可高估也不低估，避免触发模型 400 context length 错误。
    """
    if not text:
        return 0
    cjk = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
    other = len(text) - cjk
    return int(cjk * 1.5 + other / 4) + 1


@dataclass
class ContextBudget:
    """上下文预算，单位 token。总预算 = 模型窗口 - 回复预留。"""
    total: int = 8192
    reserve_reply: int = 1024
    system_ratio: float = 0.15      # 系统提示 + 记忆/事实
    knowledge_ratio: float = 0.30   # RAG 检索结果
    history_ratio: float = 0.40     # 近期对话
    summary_ratio: float = 0.15     # 历史摘要

    @property
    def usable(self) -> int:
        return max(512, self.total - self.reserve_reply)

    def allowance(self, ratio: float) -> int:
        return int(self.usable * ratio)


@dataclass
class AssembledContext:
    messages: List[Dict[str, str]] = field(default_factory=list)
    summary: str = ""
    dropped: int = 0               # 被压缩进摘要的轮数
    kept_turns: int = 0
    total_tokens: int = 0


def _fit_text(text: str, budget: int) -> str:
    """把文本裁到预算内（按 token 估算），从尾部截断并标注。"""
    if not text or estimate_tokens(text) <= budget:
        return text
    lo, hi = 0, len(text)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if estimate_tokens(text[:mid]) <= budget:
            lo = mid
        else:
            hi = mid - 1
    return text[:lo] + "\n…[已截断]"


def summarize_history(history: List[Dict[str, str]], llm_fn: Optional[Callable[[str], str]] = None) -> str:
    """把历史压缩成摘要。优先用注入的 llm_fn，否则用抽取式兜底。

    llm_fn: 接收待摘要文本、返回摘要字符串；调用方注入真实 LLM。
    """
    if not history:
        return ""
    raw = "\n".join(f"{h.get('role','?')}: {h.get('content','')}" for h in history)
    if llm_fn:
        try:
            s = llm_fn(raw)
            if s and not s.startswith("[LLM"):
                return s.strip()
        except Exception:
            pass
    # 抽取式兜底：保留每轮前 60 字 + 轮数标记，尽量留住设定类信息
    lines = []
    for i, h in enumerate(history):
        c = (h.get("content") or "").strip().replace("\n", " ")
        if c:
            lines.append(f"[{i+1}] {h.get('role','?')}: {c[:60]}")
    return "（历史对话摘要）\n" + "\n".join(lines[-20:])


def assemble_context(
    system: str,
    history: List[Dict[str, str]],
    user: str,
    *,
    memory_text: str = "",
    knowledge_text: str = "",
    budget: ContextBudget = None,
    llm_fn: Optional[Callable[[str], str]] = None,
) -> AssembledContext:
    """按预算组装 messages：system(+记忆) → 知识 → 摘要 → 近期历史 → user。

    history 按轮从新到旧纳入，超出历史预算的旧轮压缩成摘要放最前。
    返回值含完整 messages 与诊断字段（dropped/kept_turns/total_tokens）。
    """
    budget = budget or ContextBudget()
    out = AssembledContext()

    # 1) system + 记忆（高优先级，先占位）
    sys_full = system + ("\n" + memory_text if memory_text else "")
    sys_budget = budget.allowance(budget.system_ratio)
    sys_fit = _fit_text(sys_full, sys_budget)
    out.messages.append({"role": "system", "content": sys_fit})

    # 2) 知识（RAG）
    if knowledge_text:
        kb = _fit_text(knowledge_text, budget.allowance(budget.knowledge_ratio))
        if kb:
            out.messages.append({"role": "system", "content": kb})

    # 3) 历史：从新到旧塞入，超预算的压缩成摘要
    hist_budget = budget.allowance(budget.history_ratio)
    kept_reversed: List[Dict[str, str]] = []
    used = 0
    dropped_turns: List[Dict[str, str]] = []
    for h in reversed(history or []):
        c = h.get("content", "")
        t = estimate_tokens(str(c))
        if used + t <= hist_budget:
            kept_reversed.append({"role": h.get("role"), "content": c})
            used += t
        else:
            dropped_turns.append(h)
    out.messages.extend(reversed(kept_reversed))
    out.kept_turns = len(kept_reversed)

    # 4) 被丢弃的历史 → 摘要（放历史前）
    if dropped_turns:
        summary = summarize_history(list(reversed(dropped_turns)), llm_fn=llm_fn)
        summary = _fit_text(summary, budget.allowance(budget.summary_ratio))
        if summary:
            out.summary = summary
            # 插到 system 之后、知识之前的位置（知识已 append，这里插到 index 1）
            insert_at = 2 if len(out.messages) > 1 else 1
            out.messages.insert(insert_at, {"role": "system", "content": summary})
        out.dropped = len(dropped_turns)

    # 5) 当前 user
    out.messages.append({"role": "user", "content": user})
    out.total_tokens = sum(estimate_tokens(m["content"]) for m in out.messages)
    return out
