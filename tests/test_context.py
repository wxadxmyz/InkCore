# -*- coding: utf-8 -*-
"""M4 上下文工程测试：token 预算 / 滚动摘要 / 结构化记忆 / 混合检索。"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.context import (
    estimate_tokens, assemble_context, summarize_history, ContextBudget,
    Fact, MemoryV2, migrate_v1, facts_to_prompt,
    RetrievalResult, char_bigram_score, bm25_score, hybrid_search, format_citations,
)


# ---------- token 预算 ----------
def test_estimate_tokens_cjk_and_ascii():
    assert estimate_tokens("") == 0
    assert estimate_tokens("你好世界") > estimate_tokens("hi")
    assert estimate_tokens("a" * 100) < 40  # 英文约 4 字符 1 token


def test_context_budget_allowance():
    b = ContextBudget(total=8192, reserve_reply=1024)
    assert b.usable == 7168
    assert sum(b.allowance(r) for r in (b.system_ratio, b.knowledge_ratio,
                                         b.history_ratio, b.summary_ratio)) <= b.usable


def test_assemble_basic_order():
    ctx = assemble_context("SYS", [{"role": "user", "content": "旧问题"},
                                   {"role": "assistant", "content": "旧回答"}], "新问题")
    assert ctx.messages[0]["role"] == "system"
    assert ctx.messages[-1] == {"role": "user", "content": "新问题"}
    assert ctx.kept_turns == 2 and ctx.dropped == 0


def test_assemble_long_history_summarizes_old():
    hist = [{"role": "user", "content": f"第{i}轮设定：主角叫角色{i}"} for i in range(30)]
    b = ContextBudget(total=1024, reserve_reply=128, history_ratio=0.3, summary_ratio=0.25)
    ctx = assemble_context("SYS", hist, "复述主角名", budget=b)
    assert ctx.dropped > 0, "超预算应压缩旧轮"
    assert ctx.summary, "应产生摘要"
    assert any(m.get("content") == ctx.summary for m in ctx.messages)
    assert ctx.total_tokens <= b.usable + 50, "不应超预算"


def test_assemble_knowledge_injected():
    ctx = assemble_context("SYS", [], "问", knowledge_text="参考文档片段 x")
    assert any("参考文档片段" in m["content"] for m in ctx.messages)


def test_summarize_history_fallback():
    hist = [{"role": "user", "content": "甲" * 100}, {"role": "assistant", "content": "乙" * 100}]
    s = summarize_history(hist)
    assert "历史对话摘要" in s and "[1]" in s


def test_summarize_history_with_llm():
    s = summarize_history([{"role": "user", "content": "abc"}], llm_fn=lambda x: "模型摘要:" + x[-3:])
    assert s == "模型摘要:abc"


# ---------- 结构化记忆 ----------
def test_fact_roundtrip():
    f = Fact(type="character", entity="林墨", value="男主", confidence=0.9, source="user")
    d = f.to_dict()
    assert Fact.from_dict(d).entity == "林墨" and d["type"] == "character"


def test_migrate_v1_lossless():
    v1 = {"characters": ["林墨", "陈风"], "facts": ["偏好题材：仙侠"],
          "style": "快节奏", "world": ["修真界"], "projects": ["小说A"], "custom_field": "保留"}
    m = migrate_v1(v1)
    types = {f.type for f in m.facts}
    assert {"character", "genre", "style", "world", "project"} <= types
    assert m.legacy["custom_field"] == "保留"


def test_memory_v2_dedup():
    m = MemoryV2()
    assert m.add(Fact(type="character", entity="林墨")) is True
    assert m.add(Fact(type="character", entity="林墨", value="男主")) is False
    assert len(m.facts) == 1 and m.facts[0].value == "男主"


def test_memory_v2_query():
    m = MemoryV2()
    m.add(Fact(type="character", entity="林墨", confidence=0.9))
    m.add(Fact(type="genre", entity="仙侠", confidence=0.5))
    assert len(m.query(type="character")) == 1
    assert len(m.query(min_confidence=0.8)) == 1


def test_facts_to_prompt_groups():
    m = MemoryV2()
    m.add(Fact(type="character", entity="林墨"))
    m.add(Fact(type="genre", entity="仙侠"))
    p = facts_to_prompt(m)
    assert "人物：林墨" in p and "题材：仙侠" in p


def test_memory_v2_roundtrip_dict():
    m = MemoryV2()
    m.add(Fact(type="style", entity="快节奏"))
    m2 = MemoryV2.from_dict(m.to_dict())
    assert m2.facts[0].entity == "快节奏" and m2.version == 2


# ---------- 混合检索 ----------
DOCS = [
    {"id": "1", "name": "合同A", "chunks": ["甲方为林墨，乙方为星辰公司，合同金额一百万。", "争议解决方式为仲裁。"]},
    {"id": "2", "name": "小说B", "chunks": ["主角叫陈风，题材是仙侠，风格快节奏。", "陈风在青云山修炼多年。"]},
]


def test_bigram_score():
    assert char_bigram_score("陈风", "主角叫陈风") > char_bigram_score("陈风", "无关内容")


def test_bm25_prefers_rare_term():
    corpus = ["苹果苹果苹果香蕉", "榴莲"]
    s = bm25_score("榴莲", corpus)
    assert s[1] > s[0]


def test_hybrid_hits_correct_doc():
    r = hybrid_search("主角陈风是什么题材", DOCS, k=2)
    assert r and r[0].doc_name == "小说B", [x.doc_name for x in r]


def test_hybrid_citation_has_source():
    r = hybrid_search("陈风", DOCS, k=1)
    cite = format_citations(r)
    assert "小说B" in cite and "片段" in cite


def test_hybrid_empty():
    assert hybrid_search("x", [], k=3) == []
    assert format_citations([]) == ""


def test_embedding_fusion():
    def fake_embed(q, chunks):
        return [10.0 if "合同" in c else 0.0 for c in chunks]
    r = hybrid_search("合同金额", DOCS, k=2, embed_score_fn=fake_embed)
    assert r[0].doc_name == "合同A"


# ---------- app 集成 ----------
def test_app_retrieve_doc_uses_citations(monkeypatch):
    import importlib
    app = importlib.import_module("app")
    monkeypatch.setattr(app, "load_docs", lambda: DOCS)
    out = app.retrieve_doc("陈风题材", k=2)
    assert "参考文档片段" in out and "小说B" in out


def test_app_memory_context_v2(monkeypatch):
    import importlib
    app = importlib.import_module("app")
    monkeypatch.setitem(app.memory, "v2test", {
        "characters": [], "facts": [], "style": "", "world": [], "projects": [],
        "__v2": {"version": 2, "facts": [
            {"type": "character", "entity": "苏九", "confidence": 1.0, "source": "user", "ts": "2026-01-01T00:00:00+00:00"}], "legacy": {}},
    })
    out = app.memory_context("v2test")
    assert "苏九" in out


def test_app_call_llm_budget(monkeypatch):
    """call_llm 组装后 messages 条数受控，且 user 在最后。"""
    import importlib
    app = importlib.import_module("app")
    captured = {}
    def fake_stream(msgs, c):
        captured["msgs"] = msgs
        return iter([])
    monkeypatch.setattr(app, "_llm_stream", fake_stream)
    cfg = {"enabled": True, "api_key": "x", "base_url": "http://x", "model": "m",
           "context_window": 512}
    hist = [{"role": "user", "content": f"旧消息{i}"} for i in range(50)]
    app.call_llm("SYS", hist, "最后问题", cfg=cfg, stream=True)
    msgs = captured["msgs"]
    assert msgs[-1]["role"] == "user" and msgs[-1]["content"] == "最后问题"
    assert msgs[0]["role"] == "system"
    # 50 轮极短消息 → 应丢弃旧轮并产生摘要（条数明显减少），总 token 不超预算
    assert any("历史对话摘要" in m["content"] for m in msgs), "旧轮应被压缩成摘要"
    assert len(msgs) < 50, f"长对话应有压缩，实际 {len(msgs)} 条"
    from core.context import estimate_tokens
    assert sum(estimate_tokens(m["content"]) for m in msgs) <= 512 + 50


def test_app_legacy_engine(monkeypatch):
    """context.engine=legacy 时退回旧 [-12:] 行为。"""
    import importlib
    app = importlib.import_module("app")
    captured = {}
    def fake_complete(msgs, c):
        captured["n"] = len(msgs)
        return "ok"
    monkeypatch.setattr(app, "_llm_complete", fake_complete)
    monkeypatch.setitem(app.config, "context", {"engine": "legacy"})
    cfg = {"enabled": True, "api_key": "x", "base_url": "http://x", "model": "m"}
    hist = [{"role": "user", "content": str(i)} for i in range(30)]
    app.call_llm("SYS", hist, "Q", cfg=cfg)
    assert captured["n"] == 14  # 1 system + 12 history + 1 user
