#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Web版本启动脚本"""

import sys
import os
import webbrowser
import threading

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web.app import app


def open_browser():
    """延迟打开浏览器"""
    import time
    time.sleep(1.5)
    webbrowser.open('http://127.0.0.1:5000')


if __name__ == "__main__":
    print("=" * 50)
    print("抖音视频自动发布工具 - Web版")
    print("=" * 50)
    print()
    print("正在启动服务...")
    print("访问地址: http://127.0.0.1:5000")
    print()
    print("按 Ctrl+C 停止服务")
    print("=" * 50)

    # 在新线程中打开浏览器
    threading.Thread(target=open_browser, daemon=True).start()

    # 启动Flask服务
    app.run(host="127.0.0.1", port=5000, debug=False)
