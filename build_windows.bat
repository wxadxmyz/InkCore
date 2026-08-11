@echo off
REM ============================================================
REM  墨核 AI Studio —— Windows 一键打包为 exe
REM  在「墨核AIStudio」项目根目录（含 desktop_app.py / app.py / static）下运行本脚本。
REM  前置：已安装 Python 3.10+ 并勾选 "Add to PATH"
REM ============================================================

echo [1/3] 安装依赖...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo [2/3] 清理旧的构建产物...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo [3/3] 开始打包（单文件 exe，约需 1-3 分钟）...
pyinstaller build.spec

echo.
echo 完成！exe 位于： dist\InkCore.exe
echo 双击即可运行（首次需联网加载系统 Edge WebView2，Win10/11 已内置）。
pause
