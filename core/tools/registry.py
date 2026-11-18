# -*- coding: utf-8 -*-
"""工具注册表：ToolSpec 定义 + Registry 容器。纯数据结构，不含任何执行逻辑。"""
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional


@dataclass
class ToolSpec:
    """一个可被模型调用的工具的完整描述。

    name        : 唯一标识（模型据此发起调用）
    description : 给模型看的自然语言描述，直接影响选对率
    parameters  : JSON Schema（OpenAI function.parameters 格式）
    permission  : read | write | execute（M5 审批依据，M2 仅记录）
    timeout     : 单次执行超时（秒），由 tool_loop 统一控制
    run         : Callable[[dict], dict]，入参是已校验的 dict，返回统一契约
    """
    name: str
    description: str
    parameters: dict
    permission: str = "read"
    timeout: int = 20
    run: Optional[Callable[[dict], dict]] = None

    def to_openai(self) -> dict:
        """转成 OpenAI 兼容的 tools 数组元素。"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class Registry:
    """工具注册表：注册 / 查询 / 汇总 Schema。"""

    def __init__(self):
        self._tools: Dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec) -> ToolSpec:
        if not spec.name or spec.name in self._tools:
            raise ValueError(f"工具名重复或为空：{spec.name}")
        self._tools[spec.name] = spec
        return spec

    def get(self, name: str) -> Optional[ToolSpec]:
        return self._tools.get(name)

    def names(self) -> List[str]:
        return list(self._tools.keys())

    def specs(self) -> List[ToolSpec]:
        return list(self._tools.values())

    def schemas(self) -> List[dict]:
        return [s.to_openai() for s in self._tools.values()]

    def describe(self) -> str:
        """给关键词兜底/提示词用的纯文本工具清单。"""
        return "\n".join(f"- {s.name}: {s.description}" for s in self._tools.values())

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        return name in self._tools
