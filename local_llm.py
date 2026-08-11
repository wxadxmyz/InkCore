# -*- coding: utf-8 -*-
"""
本地内置大模型（离线推理，无需 Ollama / 无需用户手动安装）

设计目标：
- 用户安装软件后，无需下载安装 Ollama，也无需配置任何 API Key。
- 首次使用「本地内置模型」时，由本模块自动下载一个量化 GGUF 权重（默认 Qwen2.5-1.5B Q4，约 1.1GB），
  之后完全离线可用。
- 推理走 llama-cpp-python（跨平台：Linux / Windows / macOS 一致），进程内加载，
  通过已有的 Flask + waitress 直接流式返回，不额外占用端口、不起第二个服务。

对外接口：
- MODELS            可选模型登记表
- model_path(key)   返回某模型本地路径
- is_ready(key)     模型权重是否已下载
- get_status()      下载 / 加载状态（供前端轮询）
- start_download(key) 后台线程下载（首次使用触发）
- stream(messages, model_key, temperature, max_tokens)  生成器，逐块产出文本
"""
import os
import sys
import json
import threading
from pathlib import Path

# 模型默认放在用户数据目录下，跨平台可写
MODEL_DIR = Path(os.path.expanduser("~")) / "MoHeAI" / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

# 可选模型：默认 Qwen2.5-1.5B-Instruct Q4（中文好、体积小、CPU 可跑）。
# 另提供 0.5B 作为低内存机器的备选。GGUF 源自 HuggingFace 官方 GGUF 仓库。
MODELS = {
    "qwen2.5-1.5b-instruct-q4_k_m": {
        "label": "Qwen2.5-1.5B-Instruct (Q4，中文，≈1.1GB)",
        "file": "qwen2.5-1.5b-instruct-q4_k_m.gguf",
        "url": "https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf",
        "size": 1_150_000_000,
        "default": True,
    },
    "qwen2.5-0.5b-instruct-q4_k_m": {
        "label": "Qwen2.5-0.5B-Instruct (Q4，轻量，≈0.4GB)",
        "file": "qwen2.5-0.5b-instruct-q4_k_m.gguf",
        "url": "https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_k_m.gguf",
        "size": 420_000_000,
    },
}

DEFAULT_MODEL = next((k for k, v in MODELS.items() if v.get("default")), list(MODELS)[0])

# 线程安全状态（供前端轮询下载进度 / 加载状态）
_status_lock = threading.Lock()
_status = {
    "downloading": False,
    "progress": 0.0,      # 0..1
    "downloaded_bytes": 0,
    "total_bytes": 0,
    "done": False,
    "error": None,
    "model": DEFAULT_MODEL,
    "llama_available": None,   # None=未知, True/False
    "path": None,
}

# 懒加载的 llama_cpp 实例（全局仅加载一次）
_llm = None
_llm_key = None
_llm_lock = threading.Lock()


def _default_model_key(key=None):
    return key or DEFAULT_MODEL


def model_path(key=None):
    info = MODELS.get(_default_model_key(key))
    return MODEL_DIR / info["file"]


def is_ready(key=None):
    p = model_path(key)
    return p.exists() and p.stat().st_size > 1_000_000  # 排除明显不完整的文件


def get_status():
    with _status_lock:
        s = dict(_status)
    s["ready"] = is_ready(s.get("model"))
    s["models"] = {
        k: {"label": v["label"], "default": bool(v.get("default")), "ready": is_ready(k),
            "size": v.get("size")}
        for k, v in MODELS.items()
    }
    # 探测 llama_cpp 是否可用（仅首次）
    if s["llama_available"] is None:
        try:
            import llama_cpp  # noqa: F401
            s["llama_available"] = True
        except Exception:
            s["llama_available"] = False
    return s


def _set(**kw):
    with _status_lock:
        _status.update(kw)


def download(key=None, progress_cb=None):
    """同步下载模型权重到 MODEL_DIR；通过 _status 暴露进度。可被后台线程调用。"""
    import requests  # 延迟导入，减少启动负担

    key = _default_model_key(key)
    info = MODELS[key]
    dest = model_path(key)
    part = dest.with_suffix(dest.suffix + ".part")
    _set(downloading=True, progress=0.0, downloaded_bytes=0, total_bytes=info.get("size", 0),
         done=False, error=None, model=key, path=str(dest))

    try:
        headers = {"User-Agent": "InkCore"}
        with requests.get(info["url"], headers=headers, stream=True, timeout=30, allow_redirects=True) as r:
            r.raise_for_status()
            total = int(r.headers.get("Content-Length", info.get("size", 0)) or 0)
            _set(total_bytes=total)
            have = 0
            with open(part, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 256):
                    if not chunk:
                        continue
                    f.write(chunk)
                    have += len(chunk)
                    prog = (have / total) if total else 0.0
                    _set(downloaded_bytes=have, progress=min(1.0, prog))
                    if progress_cb:
                        progress_cb(prog, have, total)
        part.replace(dest)  # 原子替换，避免半截文件被当成已就绪
        _set(downloading=False, done=True, progress=1.0, path=str(dest))
        return True
    except Exception as e:
        _set(downloading=False, error=str(e))
        # 清理半截文件
        try:
            if part.exists():
                part.unlink()
        except Exception:
            pass
        return False


def start_download(key=None):
    """后台线程启动下载，立即返回。前端用 get_status() 轮询进度。"""
    if _status.get("downloading"):
        return False
    t = threading.Thread(target=download, args=(key,), daemon=True)
    t.start()
    return True


def _load_llama(key):
    """懒加载 llama_cpp 模型（仅一次）。返回 Llama 实例或抛出异常。"""
    global _llm, _llm_key
    key = _default_model_key(key)
    with _llm_lock:
        if _llm is not None and _llm_key == key:
            return _llm
        import llama_cpp  # 必须已安装；未安装会抛出清晰异常
        p = model_path(key)
        if not is_ready(key):
            raise FileNotFoundError(f"本地模型权重未就绪：{p}（请先在设置里下载）")
        n_threads = max(1, (os.cpu_count() or 4) // 2)
        llm = llama_cpp.Llama(
            model_path=str(p),
            n_ctx=4096,
            n_threads=n_threads,
            n_batch=512,
            verbose=False,
        )
        _llm = llm
        _llm_key = key
        return _llm


def stream(messages, model_key=None, temperature=0.9, max_tokens=2048):
    """
    生成器：逐块产出助手回复文本。
    messages 为 OpenAI 风格的 [{role, content}, ...]。
    若 llama_cpp 未安装或权重缺失，产出一段可读的错误提示（不影响主程序）。
    """
    try:
        llm = _load_llama(model_key)
        resp = llm.create_chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        for chunk in resp:
            try:
                delta = chunk["choices"][0]["delta"].get("content") or ""
            except Exception:
                delta = ""
            if delta:
                yield delta
    except Exception as e:
        yield f"\n\n[本地模型不可用] {e} —— 请确认已在设置中下载本地模型，且已安装 llama-cpp-python。"
