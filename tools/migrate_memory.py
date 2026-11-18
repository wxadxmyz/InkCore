#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""记忆 v1 → v2 迁移脚本（M4 交付物）。

用法：
    python tools/migrate_memory.py                 # 迁移所有 profile（就地，保留 legacy）
    python tools/migrate_memory.py --dry-run       # 只预览，不写盘
    python tools/migrate_memory.py --reverse       # 从 v2 反向导出 v1 字段到 stdout

设计：v2 的 __v2 键与 v1 字段共存，旧版墨核读 v1 字段照常工作，
新版优先用 __v2 的结构化事实——因此迁移是非破坏性的，可随时回退。
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from core.context.memory_v2 import migrate_v1, MemoryV2  # noqa: E402


def profiles_home() -> Path:
    import os
    return Path(os.path.expanduser("~")) / "MoHeAI" / "profiles"


def migrate(dry_run: bool = False) -> int:
    home = profiles_home()
    if not home.exists():
        print(f"无 profile 目录：{home}")
        return 0
    n = 0
    for mf in sorted(home.glob("*/memory.json")):
        data = json.loads(mf.read_text(encoding="utf-8"))
        changed = False
        for sid, mem in data.items():
            if not isinstance(mem, dict) or "__v2" in mem:
                continue
            v2 = migrate_v1(mem)
            mem["__v2"] = v2.to_dict()
            changed = True
            n += 1
            print(f"  {mf.parent.name}/{sid}: 迁移 {len(v2.facts)} 条事实")
        if changed and not dry_run:
            mf.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{'[预览] ' if dry_run else ''}共迁移 {n} 个会话记忆")
    return n


def reverse() -> int:
    """把 v2 结构化事实反向导出成 v1 字段，打印到 stdout（不写盘）。"""
    home = profiles_home()
    if not home.exists():
        print(f"无 profile 目录：{home}")
        return 0
    n = 0
    for mf in sorted(home.glob("*/memory.json")):
        data = json.loads(mf.read_text(encoding="utf-8"))
        for sid, mem in data.items():
            if not isinstance(mem, dict) or "__v2" not in mem:
                continue
            v2 = MemoryV2.from_dict(mem["__v2"])
            v1 = {
                "characters": [f.entity for f in v2.query(type="character")],
                "facts": [f.value or f.entity for f in v2.query(type="genre")] +
                         [f.entity for f in v2.query(type="preference")],
                "world": [f.entity for f in v2.query(type="world")],
                "style": next((f.entity for f in v2.query(type="style")), ""),
                "projects": [f.entity for f in v2.query(type="project")],
            }
            print(f"# {mf.parent.name}/{sid}")
            print(json.dumps(v1, ensure_ascii=False, indent=2))
            n += 1
    print(f"共导出 {n} 个会话记忆（未写盘）")
    return n


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="墨核记忆 v1 <-> v2 迁移")
    ap.add_argument("--dry-run", action="store_true", help="只预览不写盘")
    ap.add_argument("--reverse", action="store_true", help="从 v2 反向导出 v1 到 stdout")
    args = ap.parse_args()
    if args.reverse:
        reverse()
    else:
        migrate(dry_run=args.dry_run)
