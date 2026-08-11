# -*- mode: python ; coding: utf-8 -*-
# 用法：
#   Windows:  pyinstaller build.spec          → 生成 dist/InkCore.exe（单文件）
#   Linux  :  pyinstaller build.spec          → 生成 dist/InkCore（验证打包链路）
# 注意：打包前先 pip install flask python-docx pywebview pyinstaller requests
import os
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

a = Analysis(
    ['desktop_app.py'],
    pathex=[os.getcwd()],
    binaries=[],
    datas=[('static', 'static')],          # 把前端静态资源打进 exe
    # waitress 作为生产级 WSGI 服务器（支持并发 SSE 流式）
    hiddenimports=[
        'webview', 'flask', 'docx', 'requests', 'jinja2', 'werkzeug',
        'itsdangerous', 'click', 'blinker', 'markupsafe', 'lxml', 'urllib.parse',
        # 新增依赖
        'bs4', 'beautifulsoup4', 'reportlab', 'reportlab.pdfgen', 'reportlab.lib.pagesizes',
        'PIL', 'PIL.Image', 'PIL.ImageDraw', 'pystray', 'keyboard',
        'waitress', 'waitress.server', 'waitress.channel', 'waitress.tasks', 'waitress.wasyncore',
        # 本地内置模型（llama-cpp-python 原生推理库）
        'llama_cpp', 'llama_cpp.llama_cpp', 'llama_cpp._llama_cpp',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=['PyQt5', 'PyQt6', 'tkinter', 'matplotlib', 'numpy', 'pandas'],
    win_no_preferences=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='InkCore',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,                 # Windows 下不弹黑框
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join('static', 'icon.ico'),
)
