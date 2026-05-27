# 抖音视频自动发布工具

一个Windows桌面应用程序，用于自动扫描指定目录的视频文件，并按定时计划发布到抖音。

提供两个版本：
- **桌面版**：传统tkinter界面，支持系统托盘
- **Web版**：现代化暗色科技风界面，浏览器中运行

## 功能特性

- 扫描指定目录下的所有视频文件（支持mp4、avi、mov、mkv等格式）
- 显示视频文件的修改时间、大小等信息
- 支持定时发布（可配置每周几、几点发布）
- 使用抖音开放平台API进行视频发布
- 支持系统托盘后台运行
- 支持开机自启动
- 提供一键安装包
- **Web版**：暗色科技风UI，毛玻璃效果，流畅动画

## 前置条件

1. **抖音开放平台账号**
   - 访问 [抖音开放平台](https://open.douyin.com/) 注册账号
   - 创建应用并获取 `Client Key` 和 `Client Secret`
   - 申请 `video.create` 和 `video.data` 权限

2. **Python环境**（仅开发时需要）
   - Python 3.8 或更高版本

## 快速开始

### 开发模式运行

**桌面版（tkinter）**
```bash
# 安装依赖
pip install -r requirements.txt

# 创建图标
python create_icon.py

# 运行程序
python main.py
```

**Web版（推荐）**
```bash
# 安装依赖
pip install -r requirements.txt

# 运行Web版本
python run_web.py
```

浏览器会自动打开 http://127.0.0.1:5000

### 生成安装包

**方式一：一键构建（推荐）**
```bash
# 运行完整构建脚本
make_all.bat
```

此脚本会自动：
1. 安装依赖
2. 创建图标
3. 使用PyInstaller打包
4. 生成安装包（如果安装了Inno Setup）

**方式二：分步构建**
```bash
# 1. 打包程序
build_web.bat

# 2. 生成简易安装包（无需额外工具）
# 以管理员身份运行:
installer\install_simple.bat

# 3. 生成专业安装包（需要Inno Setup）
build_installer.bat
```

**方式三：仅打包可执行文件**
```bash
# 桌面版打包
build.bat

# Web版打包
build_web.bat
```

### 安装包类型

| 类型 | 文件 | 特点 |
|------|------|------|
| 简易安装包 | `installer\install_simple.bat` | 无需额外工具，管理员运行即可 |
| 专业安装包 | `dist\installer\TikTokPublisher_Setup_1.0.0.exe` | 需要Inno Setup，支持自定义安装 |
| 可执行文件 | `dist\TikTokPublisherWeb.exe` | 绿色版，直接运行 |

### 静默安装（企业部署）

```bash
# 简易安装脚本
installer\install_simple.bat /silent

# Inno Setup安装包
TikTokPublisher_Setup_1.0.0.exe /VERYSILENT /SUPPRESSMSGBOXES
```

## 使用说明

### 1. 配置抖音凭证

1. 启动程序后，点击"设置凭证"按钮
2. 输入从抖音开放平台获取的 `Client Key` 和 `Client Secret`
3. 点击"授权登录"完成OAuth授权

### 2. 设置视频目录

1. 点击"浏览"按钮选择视频文件所在的目录
2. 程序会自动扫描并显示目录中的视频文件

### 3. 配置定时发布

1. 勾选"启用"定时发布
2. 选择发布日期（如：周二,周四）
3. 设置发布时间（如：17:00）
4. 点击"保存配置"

### 4. 发布视频

- **定时发布**：程序会在设定的时间自动发布最新视频
- **立即发布**：点击"立即发布"按钮手动发布最新视频

## 项目结构

```
tiptok-vidio/
├── main.py              # 桌面版入口
├── run_web.py           # Web版入口
├── core/                # 核心模块
│   ├── config.py        # 配置管理
│   ├── video_scanner.py # 视频扫描
│   ├── douyin_api.py    # 抖音API
│   └── scheduler.py     # 定时任务
├── gui/                 # 桌面界面模块
│   ├── main_window.py   # 主窗口
│   └── tray_icon.py     # 系统托盘
├── web/                 # Web界面模块
│   ├── app.py           # Flask应用
│   ├── templates/       # HTML模板
│   └── static/          # 静态资源
│       ├── css/         # 样式文件
│       └── js/          # JavaScript文件
├── utils/               # 工具函数
│   └── helpers.py       # 辅助函数
├── assets/              # 资源文件
│   └── icon.ico         # 应用图标
├── requirements.txt     # 依赖列表
├── build.bat            # 桌面版打包脚本
├── build_web.bat        # Web版打包脚本
├── create_installer.bat # 安装包创建脚本
└── TikTokPublisher.spec # PyInstaller配置
```

## 配置文件位置

配置文件保存在：`%APPDATA%\TikTokPublisher\config.json`

## 注意事项

1. **抖音API限制**
   - 需要在抖音开放平台申请应用并获得审核
   - 视频发布有频率限制，请合理设置定时计划
   - 部分API功能需要企业认证

2. **视频格式**
   - 支持的格式：mp4, avi, mov, mkv, wmv, flv, webm, m4v, mpg, mpeg, 3gp, ts
   - 建议使用mp4格式以获得最佳兼容性

3. **系统要求**
   - Windows 10/11
   - 网络连接（用于API调用）

## 故障排除

### 问题：授权失败
- 检查Client Key和Client Secret是否正确
- 确认已在抖音开放平台申请相应权限

### 问题：视频上传失败
- 检查网络连接
- 确认视频文件格式受支持
- 检查视频文件大小是否超过限制

### 问题：定时任务不执行
- 确认程序正在运行（检查系统托盘）
- 确认定时发布已启用
- 检查时间配置是否正确

## 许可证

MIT License
