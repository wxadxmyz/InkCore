# -*- coding: utf-8 -*-
"""混合检索：字符 bigram + BM25，替代 app.py 里「数查询字符是否出现」的伪检索。

中文无空格分词，用字符 bigram 兼顾词序；BM25 抑制高频片段、突出稀有词。
可选 embedding 通过注入 score_fn 参与融合（app 侧决定是否接本地模型）。
"""
import math
import re
from dataclasses import dataclass
from typing import Dict, List, Sequence, Callable, Optional, Tuple


@dataclass
class RetrievalResult:
    doc_name: str
    chunk: str
    score: float
    chunk_index: int = 0
    doc_id: str = ""

    def citation(self, max_len: int = 200) -> str:
        snippet = self.chunk[:max_len].replace("\n", " ")
        return f"[{self.doc_name}#片段{self.chunk_index + 1}] {snippet}"


def _bigrams(text: str) -> List[str]:
    """中文字符 bigram + 英文单词，统一小写。"""
    text = text.lower()
    grams = []
    # 汉字 bigram
    han = re.findall(r"[\u4e00-\u9fff]+", text)
    for seg in han:
        if len(seg) == 1:
            grams.append(seg)
        else:
            grams.extend(seg[i:i + 2] for i in range(len(seg) - 1))
    # 英文/数字词
    grams.extend(re.findall(r"[a-z0-9]+", text))
    return grams


def char_bigram_score(query: str, chunk: str) -> float:
    """bigram 覆盖率：查询 bigram 在片段中的命中比例（带轻微长度归一）。"""
    qg = set(_bigrams(query))
    if not qg:
        return 0.0
    cg = _bigrams(chunk)
    if not cg:
        return 0.0
    cg_set = set(cg)
    hit = sum(1 for g in qg if g in cg_set)
    return hit / len(qg) * (1.0 + 0.05 * min(len(cg), 50) / 50)


def bm25_score(query: str, corpus: Sequence[str], k1: float = 1.5, b: float = 0.75) -> List[float]:
    """标准 BM25：对 corpus 每个文档返回查询相关性分数。"""
    if not corpus:
        return []
    tokenized = [_bigrams(d) for d in corpus]
    avgdl = sum(len(t) for t in tokenized) / len(tokenized) if tokenized else 0
    df: Dict[str, int] = {}
    for toks in tokenized:
        for g in set(toks):
            df[g] = df.get(g, 0) + 1
    n = len(corpus)
    qg = _bigrams(query)
    scores = []
    for toks in tokenized:
        dl = len(toks) or 1
        tf: Dict[str, int] = {}
        for g in toks:
            tf[g] = tf.get(g, 0) + 1
        s = 0.0
        for g in qg:
            if g not in tf:
                continue
            idf = math.log(1 + (n - df.get(g, 0) + 0.5) / (df.get(g, 0) + 0.5))
            s += idf * (tf[g] * (k1 + 1)) / (tf[g] + k1 * (1 - b + b * dl / (avgdl or 1)))
        scores.append(s)
    return scores


def hybrid_search(
    query: str,
    docs: Sequence[Dict],
    *,
    k: int = 3,
    alpha: float = 0.5,
    embed_score_fn: Optional[Callable[[str, List[str]], List[float]]] = None,
    min_score: float = 0.01,
) -> List[RetrievalResult]:
    """在 docs（每个含 name/id/chunks）的片段级做混合检索，返回 Top-k 带出处结果。

    alpha: bigram 权重（1-alpha 给 BM25）；embed_score_fn 存在时三路融合。
    """
    flat: List[Tuple[str, str, int, str]] = []  # (doc_name, chunk, idx, doc_id)
    for doc in docs:
        name = doc.get("name", "未命名")
        doc_id = doc.get("id", "")
        for i, ch in enumerate(doc.get("chunks", []) or []):
            flat.append((name, ch, i, doc_id))
    if not flat:
        return []

    chunks = [f[1] for f in flat]
    bigram = [char_bigram_score(query, c) for c in chunks]
    try:
        bm25 = bm25_score(query, chunks)
    except Exception:
        bm25 = [0.0] * len(chunks)
    # 各路归一化到 0~1
    def norm(xs: List[float]) -> List[float]:
        mx = max(xs) if xs else 0
        return [x / mx for x in xs] if mx > 0 else [0.0] * len(xs)

    nb, nbm = norm(bigram), norm(bm25)
    ne = [0.0] * len(chunks)
    if embed_score_fn:
        try:
            ne = norm(embed_score_fn(query, chunks))
        except Exception:
            ne = [0.0] * len(chunks)

    combined = []
    for i, (name, ch, idx, did) in enumerate(flat):
        if ne == [0.0] * len(chunks):
            s = alpha * nb[i] + (1 - alpha) * nbm[i]
        else:
            s = 0.4 * nb[i] + 0.3 * nbm[i] + 0.3 * ne[i]
        if s >= min_score:
            combined.append(RetrievalResult(doc_name=name, chunk=ch, score=round(s, 4),
                                            chunk_index=idx, doc_id=did))
    combined.sort(key=lambda r: r.score, reverse=True)
    return combined[:k]


def format_citations(results: Sequence[RetrievalResult], max_len: int = 200) -> str:
    """把检索结果渲染成带出处标注的上下文文本。"""
    if not results:
        return ""
    lines = [r.citation(max_len) for r in results]
    return "（参考文档片段，标注出处）\n" + "\n".join(lines)
