#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
前端 WSGI 入口文件 - 用于 gunicorn 启动
"""

import os
import sys

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from frontend.server import create_frontend_app

# 创建应用实例
application = create_frontend_app()

if __name__ == "__main__":
    application.run()
