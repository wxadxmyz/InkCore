@echo off
set GH_USER=wxadxmyz
set GH_TOKEN=PASTE_YOUR_TOKEN_HERE
set REPO=InkCore
set VERSION=v1.0.0

if "%GH_TOKEN%"=="PASTE_YOUR_TOKEN_HERE" goto NEEDTOKEN

where git
if errorlevel 1 goto NOGIT

set REMOTE=https://%GH_USER%:%GH_TOKEN%@github.com/%GH_USER%/%REPO%.git

echo [1/4] Committing and pushing to GitHub...
git init -q
git add -A
git commit -q -m "deploy"
git branch -M main
git remote remove origin
git remote add origin %REMOTE%
git push -u origin main

echo [2/4] Creating tag to trigger auto build...
git tag %VERSION%
git push origin %VERSION%

echo [3/4] Removing token from local git config...
git remote set-url origin https://github.com/%GH_USER%/%REPO%.git

echo.
echo Done! Open https://github.com/%GH_USER%/%REPO%
echo   Actions tab: watch build progress (5-15 minutes)
echo   Releases tab: download InkCore.exe / setup
goto END

:NEEDTOKEN
echo ERROR: Please set GH_TOKEN in this file first.
echo   Go to https://github.com/settings/tokens
echo   Generate new token (classic), select scope "repo"
echo   Copy the ghp_ token and paste it above, then save.
goto END

:NOGIT
echo ERROR: git not found. Install from https://git-scm.com/downloads
goto END

:END
pause
