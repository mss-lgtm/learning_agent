# 抖音视频自动发布工具 - 操作手册

## 目录

1. [环境准备](#1-环境准备)
2. [快速开始](#2-快速开始)
3. [详细操作步骤](#3-详细操作步骤)
4. [生成安装包](#4-生成安装包)
5. [安装和部署](#5-安装和部署)
6. [常见问题](#6-常见问题)

---

## 1. 环境准备

### 1.1 安装Python

**下载Python**
1. 访问 https://www.python.org/downloads/
2. 下载 Python 3.8 或更高版本（推荐 3.10+）
3. 运行安装程序

**重要：安装时务必勾选 "Add Python to PATH"**

![Python安装示意图](https://docs.python.org/zh-cn/3/_images/win_installer.png)

**验证安装**
打开命令提示符（Win+R，输入cmd，回车），输入：
```bash
python --version
```
应显示类似：`Python 3.10.11`

### 1.2 安装Git（可选）

如果需要使用Git管理代码：
1. 访问 https://git-scm.com/downloads
2. 下载并安装

---

## 2. 快速开始

### 方法一：一键运行（最简单）

1. **打开项目目录**
   - 打开文件资源管理器
   - 进入 `D:\AIproject\tiptok-vidio` 目录

2. **双击运行 `make_all.bat`**
   - 此脚本会自动完成所有操作
   - 等待执行完成（约2-5分钟）

3. **查看结果**
   - 完成后会自动打开 `dist` 文件夹
   - 可执行文件位于 `dist\TikTokPublisherWeb.exe`

### 方法二：分步运行

如果一键运行失败，可以分步执行：

**步骤1：打开命令提示符**
- 按 `Win + R`
- 输入 `cmd`
- 按回车

**步骤2：进入项目目录**
```bash
cd /d D:\AIproject\tiptok-vidio
```

**步骤3：安装依赖**
```bash
pip install -r requirements.txt
```

**步骤4：运行程序**
```bash
python run_web.py
```

浏览器会自动打开 http://127.0.0.1:5000

---

## 3. 详细操作步骤

### 3.1 运行Web版本（开发模式）

```bash
# 1. 打开命令提示符（Win+R，输入cmd）

# 2. 进入项目目录
cd /d D:\AIproject\tiptok-vidio

# 3. 安装依赖（只需执行一次）
pip install -r requirements.txt

# 4. 运行Web版本
python run_web.py

# 5. 浏览器会自动打开，如果没有，手动访问：
#    http://127.0.0.1:5000

# 6. 停止服务：在命令窗口按 Ctrl+C
```

### 3.2 运行桌面版本（tkinter）

```bash
# 1. 打开命令提示符

# 2. 进入项目目录
cd /d D:\AIproject\tiptok-vidio

# 3. 安装依赖（只需执行一次）
pip install -r requirements.txt

# 4. 创建图标
python create_icon.py

# 5. 运行桌面版本
python main.py
```

### 3.3 打包为可执行文件

**打包Web版本：**
```bash
# 方法1：双击运行 build_web.bat

# 方法2：命令行执行
cd /d D:\AIproject\tiptok-vidio
build_web.bat
```

**打包桌面版本：**
```bash
# 方法1：双击运行 build.bat

# 方法2：命令行执行
cd /d D:\AIproject\tiptok-vidio
build.bat
```

**打包完成后：**
- 可执行文件位于 `dist` 文件夹
- 可以将 `dist` 文件夹复制到其他电脑运行

---

## 4. 生成安装包

### 4.1 简易安装包（推荐新手）

无需安装额外软件，使用Windows自带功能。

**操作步骤：**

1. **打包程序**
   ```bash
   # 双击运行
   build_web.bat
   ```

2. **运行安装脚本**
   - 找到 `installer\install_simple.bat`
   - **右键点击** → **以管理员身份运行**
   - 按照提示完成安装

3. **安装完成后**
   - 桌面会有快捷方式
   - 程序会开机自动启动
   - 安装目录：`C:\Program Files\TikTokPublisher`

**简易安装包功能：**
- ✅ 创建桌面快捷方式
- ✅ 创建开始菜单
- ✅ 设置开机自启动
- ✅ 包含卸载程序
- ✅ 自动检测并关闭旧版本

### 4.2 专业安装包（需要Inno Setup）

**步骤1：安装Inno Setup 6**

方法A：自动安装（推荐）
```bash
# 双击运行
installer\download_inno.ps1

# 如果无法运行，右键点击 → 使用PowerShell运行
```

方法B：手动安装
1. 访问 https://jrsoftware.org/isdl.php
2. 下载 Inno Setup 6
3. 运行安装程序

**步骤2：生成安装包**

```bash
# 方法1：双击运行
build_installer.bat

# 方法2：使用完整构建脚本
make_all.bat
```

**步骤3：查看结果**
- 安装包位于：`dist\installer\TikTokPublisher_Setup_1.0.0.exe`
- 可以分发给其他用户安装

**专业安装包功能：**
- ✅ 自定义安装目录
- ✅ 可选创建桌面快捷方式
- ✅ 可选开机自启动
- ✅ 中文安装界面
- ✅ 完整卸载程序
- ✅ 支持静默安装

### 4.3 一键构建所有内容

```bash
# 双击运行 make_all.bat
# 此脚本会：
# 1. 安装依赖
# 2. 创建图标
# 3. 打包程序
# 4. 生成安装包（如果安装了Inno Setup）
# 5. 自动打开生成目录
```

---

## 5. 安装和部署

### 5.1 在本机安装

**使用简易安装包：**
1. 以管理员身份运行 `installer\install_simple.bat`
2. 按提示完成安装
3. 双击桌面快捷方式启动

**使用专业安装包：**
1. 双击 `TikTokPublisher_Setup_1.0.0.exe`
2. 选择安装目录（可选）
3. 勾选需要的选项
4. 点击"安装"

### 5.2 在其他电脑部署

**方法1：复制可执行文件（绿色版）**
1. 将整个 `dist` 文件夹复制到目标电脑
2. 双击 `TikTokPublisherWeb.exe` 运行
3. 如需开机自启动，手动运行 `installer\install_simple.bat`

**方法2：使用安装包**
1. 将安装包复制到目标电脑
2. 双击运行安装
3. 按照向导完成安装

### 5.3 企业批量部署

**使用静默安装：**
```bash
# 简易安装脚本（静默模式）
installer\install_simple.bat /silent

# 专业安装包（静默模式）
TikTokPublisher_Setup_1.0.0.exe /VERYSILENT /SUPPRESSMSGBOXES /NORESTART
```

**使用GPO部署：**
1. 将安装包放在网络共享目录
2. 在组策略中创建软件安装策略
3. 指向网络共享中的安装包

---

## 6. 常见问题

### Q1: 运行脚本时提示"python不是内部或外部命令"

**原因：** Python未添加到系统PATH

**解决方法：**
1. 重新安装Python
2. 安装时勾选 "Add Python to PATH"
3. 或手动添加PATH：
   - 右键"此电脑" → 属性 → 高级系统设置
   - 环境变量 → 系统变量 → Path
   - 添加Python安装路径，如：`C:\Python310`

### Q2: pip install 失败

**原因：** 网络问题或权限问题

**解决方法：**
```bash
# 使用国内镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 或使用阿里云镜像
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
```

### Q3: PyInstaller打包失败

**原因：** 依赖问题或路径问题

**解决方法：**
```bash
# 1. 确保所有依赖已安装
pip install -r requirements.txt

# 2. 清理旧的打包文件
rmdir /s /q build dist

# 3. 重新打包
build_web.bat
```

### Q4: 安装包被杀毒软件拦截

**原因：** 安装包会修改注册表和创建自启动项

**解决方法：**
1. 临时关闭杀毒软件的实时防护
2. 或将程序添加到白名单
3. 安装完成后重新开启防护

### Q5: 程序无法启动

**可能原因：**
- 端口5000被占用
- 缺少运行时依赖

**解决方法：**
```bash
# 1. 检查端口占用
netstat -ano | findstr :5000

# 2. 如果被占用，结束进程或修改端口
# 编辑 web/app.py，修改端口号：
# app.run(host="127.0.0.1", port=5001, debug=False)

# 3. 重新打包运行
```

### Q6: 如何卸载程序

**简易安装包卸载：**
1. 运行安装目录下的 `uninstall.bat`
   - 默认位置：`C:\Program Files\TikTokPublisher\uninstall.bat`

**专业安装包卸载：**
1. 控制面板 → 程序和功能
2. 找到"抖音视频自动发布工具"
3. 点击"卸载"

### Q7: 如何更新程序

**方法1：重新安装**
1. 下载新版本安装包
2. 直接运行安装（会自动覆盖旧版本）

**方法2：手动更新**
1. 关闭正在运行的程序
2. 将新的可执行文件复制到安装目录
3. 重新启动程序

---

## 附录：脚本说明

| 脚本文件 | 功能 | 运行方式 |
|----------|------|----------|
| `make_all.bat` | 一键构建所有内容 | 双击运行 |
| `build_web.bat` | 打包Web版本 | 双击运行 |
| `build.bat` | 打包桌面版本 | 双击运行 |
| `build_installer.bat` | 生成专业安装包 | 双击运行 |
| `installer\install_simple.bat` | 简易安装脚本 | **右键→以管理员身份运行** |
| `installer\download_inno.ps1` | 下载安装Inno Setup | 右键→使用PowerShell运行 |
| `run_web.py` | 启动Web版本 | 命令行：`python run_web.py` |
| `main.py` | 启动桌面版本 | 命令行：`python main.py` |
| `create_icon.py` | 创建应用图标 | 命令行：`python create_icon.py` |

---

## 技术支持

如有问题，请检查：
1. Python版本是否正确（3.8+）
2. 是否以管理员身份运行安装脚本
3. 网络连接是否正常
4. 杀毒软件是否拦截

---

**最后更新：2024年**
