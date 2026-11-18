# -*- coding: utf-8 -*-
"""子 Agent / 并行（M6）：长任务拆到独立上下文，主对话不被工具输出淹没。

一个子任务 = 一个独立目标 + 一份独立的 Registry/LLM 配置；在线程池里跑 ReActRunner，
只把最终 reply（可选截断）回传主 Agent，工具轨迹留在子上下文内部。

设计约束：
  - 子任务通过 callable factory 注入 runner（避免 core 强绑定具体 LLM transport）。
  - 单任务超时、异常都吞成结构化结果；一个子任务失败不影响其他。
  - 不 import app。
"""
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from dataclasses import dataclass, field
from typing import Callable, List, Optional


@dataclass
class SubTask:
    goal: str
    context: str = ""          # 传给子任务的背景（主 Agent 只摘要传入）


@dataclass
class SubResult:
    goal: str
    ok: bool
    reply: str = ""
    error: str = ""
    elapsed: float = 0.0

    def to_dict(self):
        return {"goal": self.goal, "ok": self.ok, "reply": self.reply,
                "error": self.error, "elapsed": round(self.elapsed, 3)}


def run_parallel(tasks: List[SubTask], *, runner_factory: Callable,
                 max_workers: int = 3, per_task_timeout: int = 120,
                 reply_chars: int = 4000) -> List[SubResult]:
    """并行执行子任务。

    runner_factory: Callable[[goal, context], obj]，返回带 .run() 的对象，
                    .run() 返回 dict（含 reply）或 str。由外部注入（app 侧构造 ReActRunner）。
    """
    import time
    if not tasks:
        return []
    max_workers = max(1, min(max_workers, len(tasks)))
    results: List[SubResult] = [None] * len(tasks)

    def _run_one(idx, task):
        t0 = time.time()
        try:
            runner = runner_factory(task.goal, task.context)
            out = runner.run() if hasattr(runner, "run") else runner
            if isinstance(out, dict):
                reply = str(out.get("reply", ""))
                err = str(out.get("error", "")) if not out.get("ok", True) else ""
            else:
                reply, err = str(out), ""
            return SubResult(goal=task.goal, ok=not bool(err),
                             reply=reply[:reply_chars], error=err, elapsed=time.time() - t0)
        except Exception as e:
            return SubResult(goal=task.goal, ok=False, error=f"{type(e).__name__}: {e}",
                             elapsed=time.time() - t0)

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(_run_one, i, t): i for i, t in enumerate(tasks)}
        for fut, i in futures.items():
            try:
                results[i] = fut.result(timeout=per_task_timeout)
            except FutureTimeout:
                results[i] = SubResult(goal=tasks[i].goal, ok=False,
                                       error=f"子任务超时（>{per_task_timeout}s）")
    return results


def summarize_for_parent(results: List[SubResult]) -> str:
    """把子任务结果压成主 Agent 可读的摘要（只带结论，不带工具日志）。"""
    lines = []
    for r in results:
        status = "完成" if r.ok else "失败"
        body = r.reply.strip() if r.ok else r.error
        lines.append(f"### [{status}] {r.goal}\n{body}")
    return "\n\n".join(lines)
