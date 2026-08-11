# -*- coding: utf-8 -*-
"""
墨核 AI Studio (InkCore) —— 桌面端启动器
把网页 UI 装进原生窗口（Windows 上调用系统 Edge/WebView2，体积小）。
功能：系统托盘菜单（新建对话 / 显示隐藏 / 打开配置目录 / 退出）+ 可配置全局热键唤起窗口。

开发调试： python3 desktop_app.py --headless   → 仅启动后端，浏览器开 http://127.0.0.1:7860
桌面窗口： python3 desktop_app.py              → 弹出原生窗口 + 托盘
打包 exe： 见 build.spec / build_windows.bat
"""
import os, sys, threading, time, subprocess, urllib.request
from app import app, config   # 复用同一套后端逻辑与配置（含全局热键设置）

PORT = 7860
URL = f"http://127.0.0.1:{PORT}"
HERE = os.path.dirname(os.path.abspath(__file__))

def run_server():
    """用 waitress 提供并发能力（SSE 流式 + 普通请求互不阻塞）；缺失时回退 dev server。"""
    try:
        from waitress import serve
        serve(app, host="127.0.0.1", port=PORT, threads=12, channel_timeout=120)
    except Exception as e:
        print("waitress 不可用，回退到 Flask dev server：", e)
        app.run(host="127.0.0.1", port=PORT, debug=False, threaded=True, use_reloader=False)

def wait_server():
    for _ in range(80):
        try:
            urllib.request.urlopen(URL, timeout=1); return True
        except Exception:
            time.sleep(0.2)
    return False

def make_tray_icon():
    """托盘图标：优先用品牌图（static/icon.png），缺失时退化为紫色方块「墨」。"""
    from PIL import Image
    p = os.path.join(HERE, "static", "icon.png")
    if os.path.exists(p):
        try:
            return Image.open(p).resize((64, 64), Image.LANCZOS).convert("RGBA")
        except Exception:
            pass
    from PIL import ImageDraw
    img = Image.new("RGBA", (64, 64), (124, 92, 255, 255))
    ImageDraw.Draw(img).text((22, 16), "墨", fill=(255, 255, 255, 255))
    return img

def open_config_dir():
    """打开配置/数据目录（跨平台）。"""
    d = os.path.expanduser("~/MoHeAI")
    try:
        if sys.platform.startswith("win"):
            os.startfile(d)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", d])
        else:
            subprocess.Popen(["xdg-open", d])
    except Exception as e:
        print("[托盘] 打开目录失败：", e)

def start_tray():
    """系统托盘菜单（独立线程，避免阻塞 webview.start）。缺失依赖时静默跳过。"""
    try:
        import webview, pystray
    except Exception as e:
        print("[托盘] 未启用（缺少 pystray/pillow）：", e); return
    def show():
        try: webview.windows[0].show()
        except Exception: pass
    def hide():
        try: webview.windows[0].hide()
        except Exception: pass
    def toggle():
        try:
            w = webview.windows[0]
            (w.hide() if w.shown else w.show())
        except Exception: pass
    def new_chat():
        try: webview.windows[0].evaluate_js("if(typeof newTab==='function') newTab()")
        except Exception: pass
    def quit_app(icon):
        try: webview.windows[0].destroy()
        except Exception: pass
        icon.stop()
    try:
        icon = pystray.Icon("mohe", make_tray_icon(), "墨核 AI Studio (InkCore)",
                            menu=pystray.Menu(
                                pystray.MenuItem("显示窗口", lambda _: show(), default=True),
                                pystray.MenuItem("隐藏窗口", lambda _: hide()),
                                pystray.MenuItem("新建对话", lambda _: new_chat()),
                                pystray.Menu.SEPARATOR,
                                pystray.MenuItem("打开配置目录", lambda _: open_config_dir()),
                                pystray.MenuItem("退出", quit_app)))
        icon.run()
    except Exception as e:
        print("[托盘] 启动失败（可能无桌面环境）：", e)

def start_hotkey():
    """全局热键唤起/隐藏窗口（仅 Windows，依赖 keyboard 库）。热键可在设置里配置，保存后热加载。"""
    try:
        import keyboard, webview
    except Exception:
        return
    def toggle():
        try:
            w = webview.windows[0]
            (w.hide() if w.shown else w.show())
        except Exception: pass
    cur = (config.get("hotkey") or "ctrl+alt+m").strip() or "ctrl+alt+m"
    try:
        keyboard.add_hotkey(cur, toggle)
    except Exception as e:
        print("[热键] 注册失败：", e)
    # 轮询配置变化，运行时改热键（保存后无需重启桌面程序）
    while True:
        time.sleep(2)
        try:
            new = (config.get("hotkey") or "ctrl+alt+m").strip() or "ctrl+alt+m"
            if new != cur:
                try: keyboard.remove_hotkey(cur)
                except Exception: pass
                try: keyboard.add_hotkey(new, toggle); cur = new
                except Exception as e:
                    print("[热键] 更新失败：", e)
        except Exception:
            pass

if __name__ == "__main__":
    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    ok = wait_server()
    if not ok:
        print("后端启动失败，请检查端口是否被占用。")
        sys.exit(1)
    if "--headless" in sys.argv:
        print(f"墨核 AI Studio (InkCore) 后端已就绪 → {URL}")
        print("（headless 模式：用浏览器访问上面的地址即可。Ctrl+C 退出）")
        try:
            while True: time.sleep(3600)
        except KeyboardInterrupt:
            pass
    else:
        import webview
        # 注意：pywebview 6.x 的 create_window 没有 icon 参数（窗口图标会自动取页面 favicon），
        # 此前传 icon=... 会导致 TypeError 启动失败。保留静态资源供 favicon 使用即可。
        webview.create_window(
            "墨核 AI Studio (InkCore) · 桌面智能助手",
            URL, width=1280, height=820, min_size=(960, 620),
        )
        # 托盘 + 热键 放独立线程，避免阻塞 webview.start()
        threading.Thread(target=start_tray, daemon=True).start()
        threading.Thread(target=start_hotkey, daemon=True).start()
        webview.start()
