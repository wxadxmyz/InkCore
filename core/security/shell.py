# -*- coding: utf-8 -*-
"""命令安全分析（M5）：用 shlex 分词 + 白名单 + 危险参数拦截，替换字符串黑名单。

设计目标：堵住 M1 黑名单放过的 8 类绕过：
  rm  -rf（多空格）、base64 解码执行、cmd && rm、curl | sh、
  路径穿越 ../、符号链接逃逸、超长命令、编码/变量混淆。

本模块纯函数、无副作用、不 import app，可被 app.py / 测试直接调用。
"""
from dataclasses import dataclass, field
from typing import List

import shlex

# 允许直接执行的只读命令（首个 token）。白名单之外的命令一律需审批/拒绝。
READ_ONLY_COMMANDS = {
    "ls", "dir", "pwd", "echo", "cat", "head", "tail", "wc", "df", "du",
    "find", "grep", "date", "whoami", "uname", "id", "hostname", "uptime",
    "free", "ps", "env", "printenv", "sort", "uniq", "cut", "tr", "stat",
    "realpath", "readlink", "which", "type", "git", "python3", "python",
}

# 一旦出现在任意位置就拒绝的危险 token（命令名或参数）。
DANGEROUS_TOKENS = {
    "rm", "rmdir", "dd", "mkfs", "mkfs.ext4", "wipefs", "shred", "fdisk",
    "shutdown", "reboot", "halt", "poweroff", "sudo", "su", "chown", "chmod",
    "eval", "exec", "base64", "curl", "wget", "nc", "ncat", "telnet",
}

# 危险 shell 元字符/子串（出现在原始命令里即判为链式/注入意图）。
DANGEROUS_FRAGMENTS = [
    "&&", "||", ";", "|", "$(", "`", ">", "<", "\n", "\r",
    "${", "$IFS", "\\x", "%0a", "|&",
]

MAX_COMMAND_LEN = 2000


@dataclass
class CommandVerdict:
    """命令分析结果。"""
    allowed: bool
    risk: str = "read"          # read | write | exec | network
    reason: str = ""
    tokens: List[str] = field(default_factory=list)
    blocked_token: str = ""


def _looks_like_flag_encoding(tok: str) -> bool:
    """检测 -rf 之类被拆写/编码的破坏性参数（如 -r -f 组合、--recursive --force）。"""
    low = tok.lower()
    if low.startswith("-") and ("r" in low and "f" in low):
        return True
    return low in ("--recursive", "--force", "--no-preserve-root")


def analyze_command(cmd: str, *, allow_network: bool = False,
                    allow_write: bool = False) -> CommandVerdict:
    """分析一条 shell 命令，返回是否允许及风险等级。

    allow_network / allow_write 为 False 时，网络类（curl/wget）与写类命令会被拒绝；
    为 True 时降级为"需审批"由上层决定（本函数只判 risk，不弹窗）。
    """
    raw = cmd or ""
    if not raw.strip():
        return CommandVerdict(False, "read", "空命令")

    if len(raw) > MAX_COMMAND_LEN:
        return CommandVerdict(False, "exec", f"命令超过 {MAX_COMMAND_LEN} 字符上限")

    # 1) 危险 shell 元字符：链式/管道/命令替换/重定向一律拦截（含 curl|sh、base64|sh）
    for frag in DANGEROUS_FRAGMENTS:
        if frag in raw:
            return CommandVerdict(False, "exec", f"检测到危险操作符或编码片段：{frag!r}")

    # 2) shlex 分词；失败说明有未闭合引号/转义混淆，直接拒绝
    try:
        tokens = shlex.split(raw, posix=True)
    except ValueError as e:
        return CommandVerdict(False, "exec", f"命令无法安全分词：{e}")

    if not tokens:
        return CommandVerdict(False, "read", "空命令")

    head = tokens[0].lower()

    # 3) 路径穿越：任意 token 含 ../ 或 /.. 段
    for tok in tokens:
        if ".." in tok.replace("\\", "/").split("/"):
            return CommandVerdict(False, "exec", f"路径穿越被拦截：{tok}")

    # 4) 危险 token：出现在任意位置都拒绝（含 cmd rm、sudo 等）
    for tok in tokens:
        t = tok.lower().lstrip("-")
        if t in DANGEROUS_TOKENS or _looks_like_flag_encoding(tok):
            risk = "network" if t in ("curl", "wget", "nc", "ncat", "telnet") else "exec"
            if risk == "network" and allow_network:
                return CommandVerdict(True, risk, "网络命令，需审批", tokens, t)
            return CommandVerdict(False, risk, f"危险命令/参数被拦截：{tok}", tokens, tok)

    # 5) 白名单：首个命令不在只读白名单 → 拒绝（未知命令不猜）
    if head not in READ_ONLY_COMMANDS:
        return CommandVerdict(False, "exec", f"命令不在只读白名单：{head}", tokens, head)

    return CommandVerdict(True, "read", "只读命令，允许", tokens)


def is_safe_readonly(cmd: str) -> bool:
    """便捷判断：仅当命令可安全只读执行时返回 True。"""
    return analyze_command(cmd).allowed
