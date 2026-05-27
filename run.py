#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""快速启动脚本"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import main

if __name__ == "__main__":
    main()
