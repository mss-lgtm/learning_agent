; Inno Setup 安装脚本
; 抖音视频自动发布工具 安装程序

#define MyAppName "抖音视频自动发布工具"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "TikTok Publisher"
#define MyAppURL "https://github.com/tiktok-publisher"
#define MyAppExeName "TikTokPublisherWeb.exe"

[Setup]
; 注: AppId 的值为唯一标识此程序
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
LicenseFile=..\LICENSE
OutputDir=..\dist\installer
OutputBaseFilename=TikTokPublisher_Setup_{#MyAppVersion}
SetupIconFile=..\assets\icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "autostart"; Description: "开机自动启动"; GroupDescription: "其他选项:"; Flags: checked

[Files]
Source: "..\dist\TikTokPublisherWeb.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\web\templates\*"; DestDir: "{app}\web\templates"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\dist\web\static\*"; DestDir: "{app}\web\static"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\assets\icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Dirs]
Name: "{app}\config"
Name: "{app}\logs"

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\icon.ico"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Registry]
; 开机自启动
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "TikTokPublisher"; ValueData: """{app}\{#MyAppExeName}"""; Tasks: autostart; Flags: uninsdeletevalue

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent shellexec

[UninstallDelete]
Type: filesandordirs; Name: "{app}\config"
Type: filesandordirs; Name: "{app}\logs"
Type: dirifempty; Name: "{app}"

[Code]
// 检查是否已安装
function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;

  // 检查是否正在运行
  if FindWindowByClassName('TikTokPublisher') <> 0 then
  begin
    if MsgBox('检测到程序正在运行，是否关闭后继续安装？', mbConfirmation, MB_YESNO) = IDYES then
    begin
      // 尝试关闭进程
      Exec('taskkill', '/F /IM TikTokPublisherWeb.exe', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
      Sleep(1000);
    end
    else
    begin
      Result := False;
    end;
  end;
end;

// 安装完成后创建配置目录
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // 创建默认配置文件
    SaveStringToFile(ExpandConstant('{app}\config\settings.json'),
      '{"video_directory":"","schedule":{"enabled":true,"days":["tuesday","thursday"],"time":"17:00"},"auto_start":true}', False);
  end;
end;
