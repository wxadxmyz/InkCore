# 墨核 AI Studio (InkCore) · 一步步部署到 GitHub（超详细版）

> 目标：把源码推到 GitHub，并打一个版本 tag 让 GitHub 自动打包出 Windows 安装包、发布到 Releases。
> 适合第一次操作 GitHub 的人，照着做就行。每一步都写了「操作 / 命令 / 预期结果 / 出错了怎么办」。

---

## 〇、开始前先知道的几件事

1. **这个应用是桌面 exe，不是网站。** "部署到 GitHub" 在这里指两件事：① 把代码备份/分享到 GitHub；② 打版本号后 GitHub 自动帮你打包出 exe 安装包。
2. **你之前看的 `a92342c36b9e185da.bj6.agentos-app.net` 只是 UI 截图画廊**，跟 GitHub 无关，不用管。
3. **打包在 GitHub 的云电脑上完成**，你本机不需要装 Python 或任何依赖。
4. **当前沙箱连不上 github.com**，所以下面所有 `git` 命令都要在**你自己的电脑**上执行。本文件已包含在仓库里，推上去后随时能看。

---

## 一、准备工作（在自己电脑上做，约 5 分钟）

### 步骤 1：注册 / 登录 GitHub
- 打开浏览器，访问 https://github.com 。
- 如果已有账号：点右上角 **Sign in** 登录。
- 如果没有账号：点 **Sign up** 注册（用邮箱，跟着提示填用户名、密码、验证）。
- ✅ 成功标志：右上角出现你的头像图标。

### 步骤 2：确认本机装了 Git
- 打开「终端 / 命令提示符 / PowerShell」（Windows 可按 `Win + R`，输入 `cmd` 回车）。
- 输入：
  ```bash
  git --version
  ```
- ✅ 成功：显示类似 `git version 2.45.0`。
- ❌ 失败（提示"不是内部或外部命令"）：去 https://git-scm.com/downloads 下载安装，一路 Next，装完重开终端再试。

### 步骤 3：把项目文件夹拿到自己电脑上
> 如果你已经在自己电脑上开发了，跳过这步，直接进入项目目录即可。
> 如果代码现在只在沙箱里，请先把整个项目文件夹复制到本机（例如通过下载压缩包 / U 盘 / 同步工具），放到一个你知道的路径，比如 `D:\InkCore` 或 `~/InkCore`。

---

## 二、在 GitHub 上新建仓库

### 步骤 4：进入新建仓库页面
- 登录后，点页面右上角你的**头像**，在弹出的菜单里点 **Your repositories**。
- 在 repositories 页面右上角，点绿色的 **New**（或 **New repository**）按钮。
- ✅ 进入 "Create a new repository" 页面。

### 步骤 5：填写仓库信息
逐项填写（看清楚不要勾错）：

| 字段 | 填什么 | 注意 |
|------|--------|------|
| **Owner** | 你的用户名 | 一般已默认选中，不用改 |
| **Repository name** | `InkCore` | 仓库名，建议就是这个 |
| **Description** | 可留空，或写「墨核 AI Studio 桌面端 AI 助手」 | 选填 |
| **Public / Private** | 选 **Public** | 公开才能免费用 GitHub Actions 自动打包；Private 也行但额度少 |
| ⚠️ **Add a README file** | **不要勾** | 本地已有 README，勾了会冲突 |
| ⚠️ **Add .gitignore** | **不要勾** | 本地已有 .gitignore |
| ⚠️ **Choose a license** | 可不选 | 想选也行，但先别勾以免冲突 |

### 步骤 6：确认创建
- 拉到最下面，点绿色的 **Create repository** 按钮。
- ✅ 成功：跳转到新仓库的空页面，地址栏类似：
  ```
  https://github.com/wxadxmyz/InkCore
  ```
- 下面所有命令里的用户名已填好为 `wxadxmyz`，直接照抄即可（若你的 GitHub 用户名不同，全局替换即可）。

### 步骤 7：复制仓库的 git 地址
- 在新仓库页面，点绿色的 **Code** 按钮（中间偏右）。
- 在弹出的小窗里，确认标签页是 **HTTPS**，点地址右边的 **复制图标**（两个方块叠一起那个）。
- 复制到的内容形如：
  ```
  https://github.com/wxadxmyz/InkCore.git
  ```
- 把它先粘贴到一个记事本里备用。

---

## 三、在本地把代码推上去

### 步骤 8：打开终端并进入项目目录
- 打开终端（cmd / PowerShell / Terminal）。
- 用 `cd` 进入项目文件夹（换成你的真实路径）：
  ```bash
  # Windows 举例
  cd D:\InkCore

  # macOS / Linux 举例
  cd ~/InkCore
  ```
- ✅ 成功：命令行提示符前面显示项目路径。
- 验证一下目录下确实有代码：
  ```bash
  dir        # Windows
  ls         # macOS / Linux
  ```
- ✅ 应看到 `app.py`、`static`、`build.spec`、`.github` 等。

### 步骤 9：确认本地已是一个 git 仓库
```bash
git status
```
- ✅ 显示 `On branch master` 和一堆文件列表 → 已经是 git 仓库，继续。
- ❌ 显示 `not a git repository` → 说明代码还没初始化。按顺序执行：
  ```bash
  git init
  git add -A
  git commit -m "init: 墨核 AI Studio 初始代码"
  ```
  然后再继续。

### 步骤 10：关联远程仓库
下面命令里的用户名已填好为 `wxadxmyz`，整行粘贴执行：
```bash
git remote add origin https://github.com/wxadxmyz/InkCore.git
```
- ✅ 没报错就是成功（命令执行后通常没有任何输出）。
- 验证：
  ```bash
  git remote -v
  ```
- ✅ 应显示两行，都指向你的 `InkCore.git`：
  ```
  origin  https://github.com/wxadxmyz/InkCore.git (fetch)
  origin  https://github.com/wxadxmyz/InkCore.git (push)
  ```

### 步骤 11：处理分支名差异（重要小坑）
- 本地分支叫 `master`，GitHub 新建仓库默认分支叫 `main`。两者必须对齐，否则推送会乱。
- **推荐方案：把本地分支改名为 main：**
  ```bash
  git branch -M main
  ```
- 想保留 `master` 也行，但得去 GitHub 网页把默认分支改掉（见步骤 12 备注），更麻烦，不推荐。

### 步骤 12：首次推送代码
```bash
git push -u origin main
```
- 第一次推送会弹出登录框 / 要求输入账号密码：
  - **用户名**：填你的 GitHub 账号（邮箱或用户名）。
  - **密码**：⚠️ **不能填 GitHub 登录密码**（GitHub 已停用密码登录）。要填 **Personal Access Token**，见步骤 13。
- ✅ 成功：终端滚动一堆 `Enumerating objects... / Writing objects...`，最后显示 `main -> main` 和 `done`。

> 备注（选 master 方案的人）：若你在 GitHub 网页把默认分支设成了 master，则这步改执行 `git push -u origin master`。

### 步骤 13：生成并使用 Personal Access Token（如果这是你第一次推）
GitHub 不再接受密码登录，需要用 Token 当密码：
1. 打开 https://github.com/settings/tokens 。
2. 点 **Generate new token** → 选 **Generate new token (classic)**。
3. 填：
   - **Note**：`InkCore-deploy`（随便写，方便认）
   - **Expiration**：选 `90 days` 或 `No expiration`（长期用选无过期）
   - **Select scopes**：勾选 **`repo`**（这一项就够，它包含全部仓库读写权限）
4. 拉到底点 **Generate token**。
5. 页面会显示一串 `ghp_xxxxxxxx` 开头的字符 —— **立刻复制保存**，离开页面后就看不到了。
6. 回到终端推送时，"密码" 那一栏粘贴这串 token 即可。
7. 想以后免密：配置 SSH key，然后把远程地址改成 `git@github.com:wxadxmyz/InkCore.git`（具体可搜 "GitHub SSH key 配置"）。

---

## 四、验证推送是否成功

### 步骤 14：刷新 GitHub 网页确认代码已上传
- 回到浏览器，刷新你的仓库页面 `https://github.com/wxadxmyz/InkCore`。
- ✅ 应看到文件列表：`app.py`、`desktop_app.py`、`static/`、`build.spec`、`.github/` 等约 90 个文件。
- ✅ 顶部应显示默认分支是 `main`（或你设的 `master`），并显示提交数 `1 commit` 或更多。
- ❌ 如果还是空仓库：说明推送没成功，回到步骤 10–12 检查 `git remote -v` 和分支名。

### 步骤 15：确认大文件/密钥没有被传上去
- 在仓库文件列表里找一下，确认 **没有** 这些情况：
  - 没有 `InkCore-latest.zip`（`.zip` 已被忽略）
  - 没有 `_ui_gallery/` 文件夹（已被忽略）
  - 没有 `dist/`、`build/`（打包产物，已被忽略）
  - 没有 `.env`、含 `secret` / `token` / `key` 的文件
- ✅ 以上都没有 = 干净，可以放心公开。

---

## 五、打版本 tag，触发自动打包出 exe

> 只有推送 `v` 开头的 tag 才会触发打包（这是 `build.yml` 里设好的规则）。当前版本号是 **1.0.0**（见 `version.json`）。

### 步骤 16：打本地 tag
```bash
git tag v1.0.0
```
- ✅ 无输出即成功。
- 查看已有 tag：`git tag` → 应列出 `v1.0.0`。

### 步骤 17：推送 tag 到 GitHub（这一步才触发打包）
```bash
git push origin v1.0.0
```
> 等价于 `git push --tags`，但明确指定名字更安全。

### 步骤 18：在 GitHub Actions 里看打包进度
1. 打开仓库页面，点顶部第二个标签 **Actions**。
2. ✅ 应看到一条名为 **Build Windows Release** 的工作流正在运行（黄色圆点转圈）。
3. 点进去可以看到每一步日志：
   - Checkout → Set up Python 3.11 → Install dependencies → Build exe → Build installer → Create Release
4. 等待完成，首次约 **5–15 分钟**（装依赖最慢）。
5. ✅ 全部变绿色对勾 = 成功。若某步红色 = 失败，点开看红色步骤的日志（常见原因见末尾 FAQ）。

### 步骤 19：去 Releases 下载安装包
1. 回到仓库首页，右侧边栏找 **Releases**（或地址栏加 `/releases`）。
2. ✅ 应看到刚发布的 `墨核 AI Studio v1.0.0`。
3. 展开 **Assets**，下载：
   - **`InkCore.exe`** —— 单文件版，双击即用，无需安装。
   - **`InkCore_Setup_1.0.0.exe`** —— 安装版，推荐大多数用户，会建开始菜单/桌面快捷方式。
4. 双击运行。若看到 Windows SmartScreen「Windows 已保护你的电脑」→ 点 **详细信息 → 仍要运行**（未签名程序的正常提示，不是病毒）。

---

## 六、以后每次更新代码的固定流程

### 步骤 20：本地改完代码 → 提交 → 推送（日常）
```bash
git add -A
git commit -m "这里写你改了什么，比如：修复引导页图标"
git push
```
> 这一步只更新源码，**不会**自动打包。

### 步骤 21：要发新版本时
1. 先更新 `version.json` 里的 `version`（如 `"1.1.1"`）和 `url`（改成新版本地址），提交：
   ```bash
   git add version.json
   git commit -m "bump version to 1.1.1"
   git push
   ```
2. 打新 tag 并推送（触发打包）：
   ```bash
   git tag v1.1.1
   git push origin v1.1.1
   ```
3. 回到步骤 18–19 等打包、去 Releases 下载。

> `version.json` 里的 `url` 建议写成：
> ```json
> "url": "https://github.com/wxadxmyz/InkCore/releases/download/v1.1.1/InkCore_Setup_1.1.1.exe"
> ```

---

## 七、可选增强（按需做）

### 步骤 22（可选）：消除 SmartScreen 黄色警告 —— 代码签名
未签名程序用户下载会看到「未知发布者」。有代码签名证书后：
1. 在 `build.yml` 里找到被注释掉的 `# - name: Sign exe` 段，删掉前面的 `#` 取消注释。
2. 仓库页面 → **Settings → Secrets and variables → Actions → New repository secret**，添加：
   - `CERT_BASE64`：你的 pfx 证书转成的 base64
   - `CERT_PASSWORD`：证书密码

### 步骤 23（可选）：把 UI 画廊也发到网上（GitHub Pages）
若想让那个界面截图画廊有个公开网址：仓库 **Settings → Pages**，Source 选 `main` 分支、目录选根目录或 `/docs`。注意画廊文件较大（内嵌 base64 截图），建议单独放，不要直接进主仓库。

### 步骤 24（可选）：配置 SSH 免密推送
搜 "GitHub SSH key 配置"，生成密钥后执行：
```bash
git remote set-url origin git@github.com:wxadxmyz/InkCore.git
```
之后推送不再需要输 token。

---

## 八、常见问题（FAQ）

**Q1：推送时提示 `remote: Support for password authentication was removed`？**
→ 你在用 GitHub 登录密码当密码了。改用 Personal Access Token（步骤 13）。

**Q2：推送报错 `failed to push some refs` / `non-fast-forward`？**
→ 远程仓库不是空的（可能你勾了初始化 README）。解决：
```bash
git pull origin main --allow-unrelated-histories
git push -u origin main
```
或干脆新建仓库时**不要勾**任何初始化选项（步骤 5）。

**Q3：推送报错 `repository not found`？**
→ 远程地址写错或仓库是 Private 且没权限。检查 `git remote -v` 里的用户名/仓库名；Private 仓库确保用的是有 `repo` 权限的 token。

**Q4：Actions 跑失败怎么看原因？**
→ 进 `Actions` 点对应任务，看红色步骤的日志。常见：依赖装不上（查 `requirements.txt`）、Python 版本不对（工作流固定 3.11）、或 `installer.iss` 路径问题。改完代码 `git push` 后，去 Actions 页手动 **Run workflow** 重试。

**Q5：我只想托管源码、不要自动打包？**
→ 只做步骤 8–14（创建仓库 + `git push`）即可，不打 tag，`build.yml` 就不会触发。

**Q6：安装包有多大？模型要打进去吗？**
→ 安装包只有几十 MB（模型权重不打进包）。首次启动若选「本地内置模型」，软件会自动下载约 1.1GB 量化权重，之后永久离线可用。

**Q7：本地分支是 master，GitHub 默认 main，一定要改名吗？**
→ 不一定。改名（`git branch -M main`）最省事；想保留 master 就去 GitHub `Settings → Branches` 把 Default branch 设成 master，再 `git push -u origin master`。

---

## 九、一页速查（复制这串就能走完主流程）

```bash
# —— 在你自己电脑的终端里，进入项目目录后 ——

# 1) 关联远程（用户名已填为 wxadxmyz）
git remote add origin https://github.com/wxadxmyz/InkCore.git

# 2) 分支对齐 + 首次推送
git branch -M main
git push -u origin main

# 3) 打版本 tag 触发自动打包
git tag v1.0.0
git push origin v1.0.0

# 4) 然后去 GitHub 网页：Actions 看进度 → Releases 下载 exe
```

> 完成信号：GitHub 仓库 `Releases` 里出现 `墨核 AI Studio v1.0.0`，含 `InkCore.exe` 与 `InkCore_Setup_1.0.0.exe`。
