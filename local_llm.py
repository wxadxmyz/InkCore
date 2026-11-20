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
import time
import threading
from pathlib import Path

# 模型默认放在用户数据目录下，跨平台可写
MODEL_DIR = Path(os.path.expanduser("~")) / "MoHeAI" / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

# v2.4.0：GGUF 权重文件头魔数。仅靠「文件 > 1MB」判断就绪会误把镜像返回的错误页
# 当成模型（体积够大），真正加载时 GGUF 解析失败，表现为「下载了却用不了」。
GGUF_MAGIC = b"GGUF"
# 下载成功后的回调（由 app.py 注册，用于自动把当前 provider 切到内置模型）
_on_downloaded = None


def set_on_downloaded(cb):
    """注册下载成功回调 cb(model_key)，供 app.py 自动切换 provider。"""
    global _on_downloaded
    _on_downloaded = cb


def _is_valid_gguf(path):
    """校验是否为真正的 GGUF 权重：文件存在、体积合理、文件头为 b'GGUF'。"""
    try:
        p = Path(path)
        if not p.exists() or p.stat().st_size <= 1_000_000:
            return False
        with open(p, "rb") as f:
            return f.read(4) == GGUF_MAGIC
    except Exception:
        return False

# 可选模型：默认 Qwen2.5-1.5B-Instruct Q4（中文好、体积小、CPU 可跑）。
# 另提供 0.5B 作为低内存机器的备选。GGUF 源自 HuggingFace 官方 GGUF 仓库。
#
# v2.3.0：每个模型配「镜像源 + 官方源」两条下载通道。
# 国内直连 huggingface.co 经常超时/极慢，先走 hf-mirror.com 镜像，
# 镜像失败再自动回退官方源，两个都失败才报错。
MIRROR_PREFIX = "https://hf-mirror.com/"
_HF_PREFIX = "https://huggingface.co/"


def _mirror_url(url):
    """把 huggingface 官方地址换成国内镜像地址。"""
    if url.startswith(_HF_PREFIX):
        return MIRROR_PREFIX + url[len(_HF_PREFIX):]
    return url


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
    "speed": 0,           # 字节/秒（近期平均）
    "done": False,
    "error": None,
    "model": DEFAULT_MODEL,
    "llama_available": None,   # None=未知, True/False
    "path": None,
    "source": "",         # 当前使用的下载源（mirror / official）
    "attempts": [],       # 试过的源与结果，前端可展示
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
    """模型是否真正可用：v2.4 起校验 GGUF 文件头，杜绝错误页/半截文件被误判就绪。"""
    return _is_valid_gguf(model_path(key))


def get_status():
    with _status_lock:
        s = dict(_status)
    s["ready"] = is_ready(s.get("model"))
    s["models"] = {
        k: {"label": v["label"], "default": bool(v.get("default")), "ready": is_ready(k),
            "size": v.get("size")}
        for k, v in MODELS.items()
    }
    # 探测 llama_cpp 是否可用（仅首次，结果写回 _status，避免每次调用都重复 import）
    if s["llama_available"] is None:
        try:
            import llama_cpp  # noqa: F401
            available = True
        except Exception as e:
            available = False
            _set(llama_available=False, llama_error=str(e))
        else:
            _set(llama_available=True)
        s["llama_available"] = available
    return s


def _set(**kw):
    with _status_lock:
        _status.update(kw)


def _reset_download_state(key, info, attempts):
    """开始一次下载前，把所有进度/错误状态清干净（修 v2.2 永久「下载中」的 bug）。"""
    _set(downloading=True, progress=0.0, downloaded_bytes=0,
         total_bytes=int(info.get("size", 0) or 0),
         done=False, error=None, model=key, speed=0,
         source="", attempts=list(attempts))


def _download_from(url, part, total_guess, progress_cb=None, timeout=30):
    """从单个源下载。返回 (是否成功, 总字节数, 错误信息)。"""
    import requests

    headers = {"User-Agent": "InkCore"}
    with requests.get(url, headers=headers, stream=True, timeout=timeout, allow_redirects=True) as r:
        r.raise_for_status()
        total = int(r.headers.get("Content-Length", total_guess) or 0)
        have = 0
        last_t = time.time()
        last_bytes = 0
        with open(part, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 256):
                if not chunk:
                    continue
                f.write(chunk)
                have += len(chunk)
                # 速度：每 0.5 秒算一次平均
                now = time.time()
                if now - last_t >= 0.5:
                    sp = int((have - last_bytes) / (now - last_t))
                    last_t, last_bytes = now, have
                    _set(speed=sp)
                prog = (have / total) if total else 0.0
                _set(downloaded_bytes=have, progress=min(1.0, prog))
                if progress_cb:
                    progress_cb(prog, have, total)
    return True, total, None


def download(key=None, progress_cb=None):
    """下载模型权重到 MODEL_DIR。

    v2.3.0：先走国内镜像（hf-mirror.com），失败自动回退官方源；
    无论成功失败都复位 downloading 状态（修「永久下载中」）。
    """
    key = _default_model_key(key)
    info = MODELS[key]
    dest = model_path(key)
    part = dest.with_suffix(dest.suffix + ".part")
    official = info["url"]
    mirror = _mirror_url(official)
    attempts = []

    _reset_download_state(key, info, attempts)

    # 依次尝试：镜像 → 官方
    for label, url in (("mirror", mirror), ("official", official)):
        if label == "official" and mirror == official:
            continue    # 本身就是官方地址，不必重复尝试
        try:
            _set(source=label)
            ok, total, err = _download_from(url, part, info.get("size", 0), progress_cb)
            if not ok:
                raise RuntimeError(err or "下载失败")
            # v2.4：下载完先校验文件头。镜像偶尔返回 HTML 错误页/拦截页，
            # 体积可能 >1MB，必须确认是真 GGUF 才算成功，否则换下一个源重试。
            if not _is_valid_gguf(part):
                raise RuntimeError("下载内容不是有效的 GGUF 模型（可能是镜像返回的错误页）")
            attempts.append({"source": label, "ok": True})
            part.replace(dest)   # 原子替换，避免半截文件被当成已就绪
            _set(downloading=False, done=True, progress=1.0, path=str(dest),
                 speed=0, source=label, attempts=attempts)
            # 下载成功后回调：自动把当前 provider 切到内置模型（v2.4）
            if _on_downloaded:
                try:
                    _on_downloaded(key)
                except Exception:
                    pass
            return True
        except Exception as e:
            attempts.append({"source": label, "ok": False, "error": str(e)})
            _set(attempts=attempts)
            # 清掉半截文件再试下一个源
            try:
                if part.exists():
                    part.unlink()
            except Exception:
                pass
            continue

    # 两个源都失败
    msg = attempts[-1].get("error", "未知错误") if attempts else "未知错误"
    _set(downloading=False, error="下载失败：" + msg, progress=0.0,
         downloaded_bytes=0, speed=0, attempts=attempts)
    return False


def start_download(key=None):
    """后台线程启动下载，立即返回。前端用 get_status() 轮询进度。"""
    if _status.get("downloading"):
        return False
    def _worker():
        try:
            download(key)
        except Exception as e:
            # 兜底：线程内任何未捕获异常都要复位状态，否则前端会永远显示「下载中」
            _set(downloading=False, error="下载失败：" + str(e), progress=0.0, speed=0)
    t = threading.Thread(target=_worker, daemon=True)
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
