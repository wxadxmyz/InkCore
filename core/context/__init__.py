# -*- coding: utf-8 -*-
"""context 上下文工程：token 预算、滚动摘要、结构化记忆、混合检索。

设计原则：不依赖 app.py，纯数据结构 + 算法，便于单测；app 侧负责持久化与注入。
"""
from .budget import (
    assemble_context,
    estimate_tokens,
    summarize_history,
    ContextBudget,
)
from .memory_v2 import (
    Fact,
    MemoryV2,
    migrate_v1,
    facts_to_prompt,
)
from .retrieval import (
    RetrievalResult,
    bm25_score,
    char_bigram_score,
    hybrid_search,
    format_citations,
)

__all__ = [
    "assemble_context", "estimate_tokens", "summarize_history", "ContextBudget",
    "Fact", "MemoryV2", "migrate_v1", "facts_to_prompt",
    "RetrievalResult", "bm25_score", "char_bigram_score", "hybrid_search", "format_citations",
]
