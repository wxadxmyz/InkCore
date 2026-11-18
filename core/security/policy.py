# -*- coding: utf-8 -*-
"""安全策略与审批决策（M5）。

把"工具有没有权限跑"集中成一处决策，供 Agent 循环与 API 调用：
  - 工具权限分级 read / write / exec / network
  - 决策：allow（直接放行）/ confirm（需用户确认）/ deny（拒绝）
策略全部走配置，可临时降级（回滚点 v1.3.0）。
"""
from dataclasses import dataclass


RISK_ORDER = {"read": 0, "write": 1, "network": 2, "exec": 3}


@dataclass
class Decision:
    action: str          # allow | confirm | deny
    risk: str
    reason: str = ""


def risk_of(permission: str) -> str:
    """把 ToolSpec.permission 映射到标准风险等级。"""
    p = (permission or "read").lower()
    if p in ("read",):
        return "read"
    if p in ("write",):
        return "write"
    if p in ("network",):
        return "network"
    if p in ("execute", "exec", "terminal", "code"):
        return "exec"
    return "exec"


def decide(permission: str, *, policy: dict = None, tool_name: str = "") -> Decision:
    """根据配置的审批策略给出决策。

    policy 形如：
      {
        "mode": "balanced",            # strict | balanced | permissive
        "auto_approve": ["read_file", "grep"],   # 这些工具无论等级都放行
        "require_confirm": ["exec", "network"],  # 这些等级必须确认
        "deny": ["terminal"],          # 黑名单工具，直接拒绝
      }
    """
    policy = policy or {}
    mode = policy.get("mode", "balanced")
    risk = risk_of(permission)
    name = tool_name

    if name in (policy.get("deny") or []):
        return Decision("deny", risk, f"工具 {name} 已被策略禁用")

    if name in (policy.get("auto_approve") or []):
        return Decision("allow", risk, f"{name} 在自动放行清单")

    if mode == "permissive":
        return Decision("allow", risk, "宽松模式：全部放行")

    if risk == "read":
        return Decision("allow", "read", "只读工具直接放行")

    require = policy.get("require_confirm")
    if require is None:
        require = ["write", "network", "exec"] if mode == "strict" else ["write", "exec"]

    if risk in require:
        return Decision("confirm", risk, f"{risk} 级操作需用户确认")

    return Decision("allow", risk, "策略允许")


def merge_policy(config_policy: dict) -> dict:
    """把用户配置与默认值合并，返回完整策略 dict。"""
    base = {
        "mode": "balanced",
        "auto_approve": ["search", "doc", "read_file", "glob", "grep",
                         "list_dir", "http_fetch", "image", "write"],
        "require_confirm": ["write", "exec", "network"],  # 按风险等级：写/执行/联网需确认，只读不打扰
        "deny": [],
        "allow_network": False,
        "allow_outside_roots": False,
    }
    if isinstance(config_policy, dict):
        base.update(config_policy)
    return base
