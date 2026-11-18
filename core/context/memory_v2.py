# -*- coding: utf-8 -*-
"""结构化记忆 v2：事实表（类型/实体/置信度/来源/时间戳）。

兼容 v1（characters/facts/world/style/projects）：migrate_v1 无损转换，
旧字段保留在 legacy 键里，随时可反向导出。
"""
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class Fact:
    """一条结构化记忆事实。"""
    type: str            # character | genre | style | world | project | brand | preference | custom
    entity: str          # 实体名，如「林墨」「仙侠」
    value: str = ""      # 附加信息
    confidence: float = 1.0
    source: str = "user" # user | inferred | import
    ts: str = field(default_factory=_now)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Fact":
        return Fact(
            type=d.get("type", "custom"),
            entity=d.get("entity", ""),
            value=d.get("value", ""),
            confidence=float(d.get("confidence", 1.0)),
            source=d.get("source", "user"),
            ts=d.get("ts") or _now(),
        )


@dataclass
class MemoryV2:
    """会话记忆容器：facts 为结构化事实，legacy 保留 v1 原始字段。"""
    facts: List[Fact] = field(default_factory=list)
    legacy: Dict[str, Any] = field(default_factory=dict)
    version: int = 2

    def add(self, fact: Fact) -> bool:
        """加入事实；同 type+entity 视为同一条，更新 value/置信度/时间戳。"""
        for f in self.facts:
            if f.type == fact.type and f.entity == fact.entity:
                if fact.value:
                    f.value = fact.value
                f.confidence = max(f.confidence, fact.confidence)
                f.source = fact.source
                f.ts = fact.ts
                return False
        self.facts.append(fact)
        return True

    def query(self, type: str = None, entity: str = None, min_confidence: float = 0.0) -> List[Fact]:
        out = self.facts
        if type:
            out = [f for f in out if f.type == type]
        if entity:
            out = [f for f in out if entity in f.entity or entity in f.value]
        out = [f for f in out if f.confidence >= min_confidence]
        return out

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "facts": [f.to_dict() for f in self.facts],
            "legacy": self.legacy,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "MemoryV2":
        if not d:
            return MemoryV2()
        facts = [Fact.from_dict(f) for f in d.get("facts", []) if isinstance(f, dict)]
        return MemoryV2(facts=facts, legacy=d.get("legacy", {}), version=2)


def migrate_v1(v1: Dict[str, Any]) -> MemoryV2:
    """把 v1 记忆（characters/facts/world/style/projects）转成 v2，无损保留 legacy。"""
    v1 = v1 or {}
    m = MemoryV2(legacy={k: v for k, v in v1.items() if k != "version"})
    for name in v1.get("characters", []) or []:
        m.add(Fact(type="character", entity=str(name), confidence=1.0, source="inferred"))
    for f in v1.get("facts", []) or []:
        s = str(f)
        if "偏好题材" in s or "题材" in s:
            m.add(Fact(type="genre", entity=s.split("：")[-1].split(":")[-1].strip() or s,
                       value=s, source="inferred"))
        else:
            m.add(Fact(type="preference", entity=s, source="inferred"))
    for w in v1.get("world", []) or []:
        m.add(Fact(type="world", entity=str(w), source="inferred"))
    if v1.get("style"):
        m.add(Fact(type="style", entity=str(v1["style"]), source="inferred"))
    for p in v1.get("projects", []) or []:
        m.add(Fact(type="project", entity=str(p), source="inferred"))
    return m


def facts_to_prompt(mem: MemoryV2, max_facts: int = 20) -> str:
    """把结构化事实渲染成可注入 system 的紧凑文本，按类型分组。"""
    if not mem.facts:
        # 兜底：v2 为空但有 legacy
        bits = []
        lg = mem.legacy
        if lg.get("characters"):
            bits.append("人物：" + "、".join(map(str, lg["characters"])))
        if lg.get("style"):
            bits.append("风格：" + str(lg["style"]))
        if lg.get("facts"):
            bits.append("设定：" + "。".join(map(str, lg["facts"])))
        return ("（已知创作设定：" + "。".join(bits) + "）\n") if bits else ""

    groups: Dict[str, List[Fact]] = {}
    for f in mem.facts[:max_facts]:
        groups.setdefault(f.type, []).append(f)
    labels = {
        "character": "人物", "genre": "题材", "style": "风格", "world": "世界观",
        "project": "项目", "brand": "品牌", "preference": "偏好", "custom": "其他",
    }
    parts = []
    for typ, fs in groups.items():
        vals = [f.entity + (f"（{f.value}）" if f.value else "") for f in fs]
        parts.append(f"{labels.get(typ, typ)}：" + "、".join(vals))
    return "（已知设定：" + "。".join(parts) + "）\n"
