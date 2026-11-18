# -*- coding: utf-8 -*-
"""13 个内置工具的 Schema 定义与装配。

设计：Schema 是静态的（TOOL_DEFS），run 实现由 app.py 通过 impls 注入（避免 core→app 循环依赖）。
工程类工具（read_file/grep 等）的实现也放在 app.py 注入，因为在那里能复用路径根与安全配置。
"""
from .registry import ToolSpec, Registry

# ---------- Schema 静态定义 ----------
# permission: read(只读) / write(写文件) / execute(执行代码命令)
# timeout: 秒
TOOL_DEFS = [
    # —— 迁移的 6 个 ——
    ToolSpec("search", "联网搜索关键词，返回摘要与来源链接。适合查最新资料、新闻、事实。",
             {"type": "object", "properties": {
                 "query": {"type": "string", "description": "搜索关键词"}},
              "required": ["query"], "additionalProperties": False},
             "read", 20),
    ToolSpec("image", "AI 生成图片/封面。根据文字描述创作插图。",
             {"type": "object", "properties": {
                 "prompt": {"type": "string", "description": "画面描述"}},
              "required": ["prompt"], "additionalProperties": False},
             "write", 120),
    ToolSpec("code", "运行一段 Python 代码并返回输出。适合计算、数据处理、验证脚本。",
             {"type": "object", "properties": {
                 "code": {"type": "string", "description": "要执行的 Python 源码"}},
              "required": ["code"], "additionalProperties": False},
             "execute", 20),
    ToolSpec("terminal", "执行一条系统终端命令（只读优先，写操作受沙箱限制）。",
             {"type": "object", "properties": {
                 "command": {"type": "string", "description": "shell 命令"}},
              "required": ["command"], "additionalProperties": False},
             "execute", 25),
    ToolSpec("doc", "在用户上传的文档知识库里检索相关片段。适合基于文档回答。",
             {"type": "object", "properties": {
                 "query": {"type": "string", "description": "检索问题或关键词"}},
              "required": ["query"], "additionalProperties": False},
             "read", 10),
    ToolSpec("write", "按用户要求创作中文文本：小说、文章、文案、剧本、报告等。",
             {"type": "object", "properties": {
                 "prompt": {"type": "string", "description": "写作需求"}},
              "required": ["prompt"], "additionalProperties": False},
             "write", 60),
    # —— 新增的 7 个工程工具 ——
    ToolSpec("read_file", "读取一个文本文件的全部内容。路径须在允许目录内。",
             {"type": "object", "properties": {
                 "path": {"type": "string", "description": "相对或绝对文件路径"}},
              "required": ["path"], "additionalProperties": False},
             "read", 10),
    ToolSpec("write_file", "把内容写入一个文件（不存在则创建，原子写）。路径须在允许目录内。",
             {"type": "object", "properties": {
                 "path": {"type": "string", "description": "目标文件路径"},
                 "content": {"type": "string", "description": "要写入的完整内容"}},
              "required": ["path", "content"], "additionalProperties": False},
             "write", 10),
    ToolSpec("edit_file", "对文件做精确字符串替换（old→new）。适合改代码、改配置。",
             {"type": "object", "properties": {
                 "path": {"type": "string", "description": "目标文件路径"},
                 "old": {"type": "string", "description": "要被替换的原文本"},
                 "new": {"type": "string", "description": "替换后的新文本"}},
              "required": ["path", "old", "new"], "additionalProperties": False},
             "write", 10),
    ToolSpec("glob", "按通配符模式查找文件，返回匹配路径列表。如 **/*.py。",
             {"type": "object", "properties": {
                 "pattern": {"type": "string", "description": "glob 通配符，如 src/**/*.py"},
                 "root": {"type": "string", "description": "搜索根目录（可选，默认应用目录）"}},
              "required": ["pattern"], "additionalProperties": False},
             "read", 10),
    ToolSpec("grep", "在文件内容中搜索模式（默认子串，可正则），返回 文件:行号:内容。",
             {"type": "object", "properties": {
                 "pattern": {"type": "string", "description": "搜索模式"},
                 "path": {"type": "string", "description": "文件或目录路径（可选）"},
                 "regex": {"type": "boolean", "description": "是否按正则匹配（默认 false）"}},
              "required": ["pattern"], "additionalProperties": False},
             "read", 15),
    ToolSpec("list_dir", "列出目录下的条目（名称、类型、大小）。",
             {"type": "object", "properties": {
                 "path": {"type": "string", "description": "目录路径（可选，默认应用目录）"}},
              "required": [], "additionalProperties": False},
             "read", 10),
    ToolSpec("http_fetch", "抓取网页并抽取正文文本，返回可读内容。适合读取网页资料。",
             {"type": "object", "properties": {
                 "url": {"type": "string", "description": "要抓取的 http/https 网址"}},
              "required": ["url"], "additionalProperties": False},
             "read", 20),
]

STATIC_BY_NAME = {d.name: d for d in TOOL_DEFS}


def build_registry(impls: dict) -> Registry:
    """按注入的 impls 装配注册表。

    impls: {name: Callable[[dict], dict]}，name 必须在 TOOL_DEFS 中；
    未提供实现的工具不会被注册（避免模型调用一个跑不动的工具）。
    """
    reg = Registry()
    for spec in TOOL_DEFS:
        run = impls.get(spec.name)
        if run is None:
            continue
        reg.register(ToolSpec(
            name=spec.name, description=spec.description, parameters=spec.parameters,
            permission=spec.permission, timeout=spec.timeout, run=run,
        ))
    return reg
