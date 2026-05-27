#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Web版本启动脚本"""

import sys
import os
import socket
import webbrowser
import threading

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web.app import app

DEFAULT_PORT = 5000


def find_available_port(start_port):
    """从 start_port 开始找一个可用端口"""
    for port in range(start_port, start_port + 20):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    return None


def open_browser(port):
    """延迟打开浏览器"""
    import time
    time.sleep(3)
    webbrowser.open(f'http://127.0.0.1:{port}')


if __name__ == "__main__":
    port = find_available_port(DEFAULT_PORT)
    if port is None:
        print("错误: 无法找到可用端口，请关闭占用端口的程序后重试")
        input("按回车键退出...")
        sys.exit(1)

    print("=" * 50)
    print("抖音视频自动发布工具 - Web版")
    print("=" * 50)
    print()
    print("正在启动服务...")
    print(f"访问地址: http://127.0.0.1:{port}")
    print()
    print("按 Ctrl+C 停止服务")
    print("=" * 50)

    # 在新线程中打开浏览器
    threading.Thread(target=open_browser, args=(port,), daemon=True).start()

    # 启动Flask服务（use_reloader=False 防止 PyInstaller 环境下重复启动）
    app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)
