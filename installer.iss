; ============================================================
;  墨核 AI Studio —— Windows 安装包脚本（Inno Setup 6）
;  用法：
;   1) 先用 build_windows.bat 生成 dist\InkCore.exe
;   2) 用 Inno Setup Compiler 打开本文件并编译
;   3) 产物： installer\InkCore_Setup_1.0.0.exe
;  说明：安装包不带签名，分发前建议用代码签名证书签名（见 README）。
; ============================================================
#define MyAppName "墨核 AI Studio (InkCore)"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "InkCore"
#define MyAppURL "https://github.com/wxadxmyz/InkCore"
#define MyAppExeName "InkCore.exe"

[Setup]
AppId={{INK-CORE-2024}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=installer
OutputBaseFilename=InkCore_Setup_{#MyAppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64
UninstallDisplayName={#MyAppName}
; 单文件 exe 已自带运行时，无需额外依赖

[Languages]
; 安装/卸载向导使用简体中文。Inno Setup 6 自带 ChineseSimplified.isl，无需额外下载。
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Files]
Source: "dist\InkCore.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加任务"; Flags: unchecked

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "立即启动 {#MyAppName}"; Flags: nowait postinstall skipifsilent
