# -*- coding: utf-8 -*-
"""Skill 包规范（M6）：SKILL.md = frontmatter 元数据 + Markdown 指令 + 可选脚本。

目录结构（一个 skill 包）：
    my-skill/
      SKILL.md          # 必需：--- frontmatter --- + 正文指令
      scripts/          # 可选：辅助脚本（被指令引用）
      references/       # 可选：参考资料

frontmatter 字段：
    name        : 技能名（必需）
    description : 一句话描述（必需）
    version     : 版本，默认 1.0.0
    author      : 作者，可选
    tags        : 逗号分隔标签，可选
    permission  : read/write/exec，默认 read

纯标准库实现，不依赖 PyYAML；导入导出为 .zip，跨机器可用。
"""
import io
import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

_FRONT = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.S)


@dataclass
class SkillPack:
    name: str
    description: str
    instructions: str
    version: str = "1.0.0"
    author: str = ""
    tags: List[str] = field(default_factory=list)
    permission: str = "read"
    files: Dict[str, str] = field(default_factory=dict)   # 相对路径 → 文本（scripts/references）

    def to_dict(self):
        return {
            "name": self.name, "description": self.description,
            "instructions": self.instructions, "version": self.version,
            "author": self.author, "tags": self.tags,
            "permission": self.permission, "files": list(self.files.keys()),
        }

    def to_prompt(self) -> str:
        """转成注入系统提示词的指令文本。"""
        head = f"# 技能：{self.name}\n{self.description}\n\n"
        return head + self.instructions.strip()


def _parse_scalar(v: str):
    v = v.strip()
    if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
        return v[1:-1]
    if v.lower() in ("true", "false"):
        return v.lower() == "true"
    return v


def parse_skill_md(text: str) -> SkillPack:
    """解析 SKILL.md 文本；缺 frontmatter 或必需字段抛 ValueError。"""
    m = _FRONT.match(text)
    if not m:
        raise ValueError("SKILL.md 缺少 --- frontmatter --- 头")
    meta = {}
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        meta[k.strip()] = _parse_scalar(v)
    name = str(meta.get("name", "")).strip()
    desc = str(meta.get("description", "")).strip()
    if not name or not desc:
        raise ValueError("SKILL.md 必须含 name 与 description")
    tags_raw = meta.get("tags", "")
    tags = [t.strip() for t in re.split(r"[,\uFF0C]", str(tags_raw)) if t.strip()]
    return SkillPack(
        name=name, description=desc, instructions=m.group(2).strip(),
        version=str(meta.get("version", "1.0.0")),
        author=str(meta.get("author", "")),
        tags=tags,
        permission=str(meta.get("permission", "read")),
    )


def load_skill_dir(path) -> SkillPack:
    """从目录加载 skill 包（读取 SKILL.md + scripts/ references/）。"""
    root = Path(path)
    skill_md = root / "SKILL.md"
    if not skill_md.is_file():
        raise ValueError(f"未找到 {skill_md}")
    pack = parse_skill_md(skill_md.read_text(encoding="utf-8"))
    for sub in ("scripts", "references"):
        d = root / sub
        if d.is_dir():
            for f in d.rglob("*"):
                if f.is_file():
                    pack.files[str(f.relative_to(root))] = f.read_text(encoding="utf-8", errors="replace")
    return pack


def load_skill_zip(path_or_bytes) -> SkillPack:
    """从 .zip 导入 skill 包。"""
    buf = io.BytesIO(path_or_bytes) if isinstance(path_or_bytes, (bytes, bytearray)) else open(path_or_bytes, "rb")
    with zipfile.ZipFile(buf) as z:
        names = z.namelist()
        skill_md = next((n for n in names if n.lower().endswith("skill.md")), None)
        if not skill_md:
            raise ValueError("zip 内未找到 SKILL.md")
        pack = parse_skill_md(z.read(skill_md).decode("utf-8"))
        for n in names:
            low = n.lower()
            if (low.startswith("scripts/") or low.startswith("references/")) and not n.endswith("/"):
                pack.files[n] = z.read(n).decode("utf-8", "replace")
    return pack


def export_skill_zip(pack: SkillPack, dest) -> Path:
    """把一个 SkillPack 导出成 .zip（跨机器可导入）。"""
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as z:
        front = (
            "---\n"
            f"name: {pack.name}\n"
            f"description: {pack.description}\n"
            f"version: {pack.version}\n"
            f"author: {pack.author}\n"
            f"tags: {','.join(pack.tags)}\n"
            f"permission: {pack.permission}\n"
            "---\n\n"
            + pack.instructions.strip() + "\n"
        )
        z.writestr("SKILL.md", front)
        for rel, content in pack.files.items():
            z.writestr(rel, content)
    return dest


def validate_skill_md(text: str) -> dict:
    """校验并返回 {ok, data, error}。"""
    try:
        pack = parse_skill_md(text)
        return {"ok": True, "data": pack.to_dict(), "error": None}
    except Exception as e:
        return {"ok": False, "data": None, "error": str(e)}
