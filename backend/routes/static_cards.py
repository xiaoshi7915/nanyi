#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
静态卡片路由
提供预生成的静态卡片HTML文件访问
"""

import os
from flask import Blueprint, send_from_directory, abort
from backend.utils.logger import log_access
from backend.utils.decorators import handle_errors

# 创建蓝图
static_cards_bp = Blueprint('static_cards', __name__)

@static_cards_bp.route('/static/cards/<path:brand_name>.html')
@log_access
@handle_errors
def get_static_card(brand_name):
    """获取预生成的静态卡片HTML"""
    try:
        # 获取静态卡片目录
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        static_cards_dir = os.path.join(project_root, 'frontend', 'static', 'cards')
        
        # 检查文件是否存在
        file_path = os.path.join(static_cards_dir, f'{brand_name}.html')
        if os.path.exists(file_path):
            return send_from_directory(static_cards_dir, f'{brand_name}.html')
        else:
            # 如果静态文件不存在，返回404
            abort(404)
    except Exception as e:
        abort(404)
