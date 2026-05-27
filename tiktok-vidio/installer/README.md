# 安装包生成指南

本文档说明如何生成抖音视频自动发布工具的一键安装包。

## 方案一：简易安装包（推荐）

无需额外工具，使用Windows自带功能创建安装脚本。

### 步骤

1. **打包程序**
   ```bash
   # 在项目根目录运行
   build_web.bat
   ```

2. **运行安装脚本**
   ```bash
   # 以管理员身份运行
   installer\install_simple.bat
   ```

3. **安装完成后**
   - 桌面快捷方式已创建
   - 开机自启动已设置
   - 卸载程序位于安装目录

### 特点

- 无需安装额外软件
- 支持自动更新
- 包含卸载程序
- 设置开机自启动

---

## 方案二：Inno Setup安装包（专业）

使用Inno Setup创建专业的Windows安装程序。

### 前置准备

1. **安装Inno Setup 6**
   - 下载地址：https://jrsoftware.org/isdl.php
   - 或运行自动安装脚本：
     ```powershell
     powershell -ExecutionPolicy Bypass -File installer\download_inno.ps1
     ```

2. **打包程序**
   ```bash
   build_web.bat
   ```

3. **生成安装包**
   ```bash
   # 使用完整打包脚本
   build_installer.bat
   ```

### 生成的安装包

安装包位于：`dist\installer\TikTokPublisher_Setup_1.0.0.exe`

### 安装包功能

- 自定义安装目录
- 创建桌面快捷方式（可选）
- 创建开始菜单（可选）
- 设置开机自启动（默认勾选）
- 安装完成后自动启动程序
- 完整的卸载程序
- 支持中文界面

---

## 方案三：NSIS安装包（高级）

如果需要更高级的自定义，可以使用NSIS。

### 前置准备

1. **安装NSIS**
   - 下载地址：https://nsis.sourceforge.io/Download

2. **创建NSIS脚本**（参考）

```nsis
!include "MUI2.nsh"

Name "抖音视频自动发布工具"
OutFile "dist\installer\TikTokPublisher_Setup.exe"
InstallDir "$PROGRAMFILES\TikTokPublisher"
Icon "assets\icon.ico"

Page directory
Page instfiles

Section "安装"
    SetOutPath "$INSTDIR"
    File "dist\TikTokPublisherWeb.exe"
    File /r "dist\web"
    File "assets\icon.ico"
    
    ; 创建快捷方式
    CreateShortcut "$DESKTOP\抖音发布工具.lnk" "$INSTDIR\TikTokPublisherWeb.exe"
    
    ; 设置自启动
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "TikTokPublisher" '"$INSTDIR\TikTokPublisherWeb.exe"'
    
    ; 创建卸载程序
    WriteUninstaller "$INSTDIR\uninstall.exe"
SectionEnd

Section "卸载"
    Delete "$INSTDIR\TikTokPublisherWeb.exe"
    RMDir /r "$INSTDIR\web"
    Delete "$INSTDIR\uninstall.exe"
    RMDir "$INSTDIR"
    DeleteRegValue HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "TikTokPublisher"
SectionEnd
```

---

## 静默安装

用于批量部署或自动化安装：

```bash
# 简易安装脚本（静默模式）
installer\install_simple.bat /silent

# Inno Setup安装包（静默模式）
TikTokPublisher_Setup_1.0.0.exe /VERYSILENT /SUPPRESSMSGBOXES /NORESTART
```

---

## 企业部署

### 使用GPO部署

1. 将安装包放在网络共享目录
2. 在组策略中创建软件安装策略
3. 指向网络共享中的MSI或EXE安装包

### 使用SCCM/Intune部署

1. 将安装包上传到SCCM/Intune
2. 创建应用程序部署
3. 设置静默安装命令：
   ```
   TikTokPublisher_Setup_1.0.0.exe /VERYSILENT /SUPPRESSMSGBOXES
   ```

### 卸载命令

```bash
# 使用卸载程序
"%ProgramFiles%\TikTokPublisher\uninstall.bat"

# 或使用Inno Setup卸载
"%ProgramFiles%\TikTokPublisher\unins000.exe" /VERYSILENT
```

---

## 常见问题

### Q: 安装包被杀毒软件拦截？

A: 这是正常现象，因为安装包会修改注册表和创建自启动项。请：
1. 添加到杀毒软件白名单
2. 或在安装前临时关闭实时防护

### Q: 如何更新已安装的程序？

A: 
1. 下载新版本安装包
2. 直接运行安装（会自动覆盖旧版本）
3. 或使用简易安装脚本（会自动检测并关闭旧版本）

### Q: 如何完全卸载？

A:
1. 运行开始菜单中的"卸载"快捷方式
2. 或运行安装目录下的 `uninstall.bat`
3. 程序文件、快捷方式、自启动项都会被删除

---

## 技术支持

如有问题，请访问：
- GitHub Issues: https://github.com/tiktok-publisher/issues
