# -*- coding: utf-8 -*-
"""路径安全护栏（M2 最小实现，M5 扩展审批与审计）。

核心：任何工程工具的路径参数都必须落在允许根目录内，杜绝 ../ 逃逸与绝对路径乱读写。
"""
import os
from pathlib import Path


def _resolve(p) -> Path:
    return Path(os.path.expanduser(str(p))).resolve()


def assert_path(path, roots):
    """把 path 规范化后限制在 roots 内，返回解析后的 Path；越界抛 ValueError。

    roots: 可迭代的 Path/str，例如 [APP_DIR, DATA_HOME]。
    """
    if path is None or not str(path).strip():
        raise ValueError("路径不能为空")
    target = _resolve(path)
    allowed = [_resolve(r) for r in roots]
    for root in allowed:
        try:
            target.relative_to(root)
            return target
        except ValueError:
            continue
    raise ValueError(f"路径越界：{path} 不在允许的目录内")


def safe_subpath(path, roots):
    """assert_path 的布尔版：越界返回 None，方便工具直接转结构化错误。"""
    try:
        return assert_path(path, roots)
    except ValueError:
        return None
