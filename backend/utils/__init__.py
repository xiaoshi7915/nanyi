#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具函数包
"""

from .file_utils import *
from .db_utils import *

try:
    from .decorators import *
except ImportError:
    # 如果decorators模块导入失败，定义基本的装饰器
    from functools import wraps
    from flask import session, redirect, url_for, jsonify, request
    
    def require_login(f):
        """登录验证装饰器"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'admin_id' not in session:
                if request.is_json:
                    return jsonify({'success': False, 'error': '请先登录'}), 401
                return redirect(url_for('admin_login'))
            return f(*args, **kwargs)
        return decorated_function
    
    def handle_errors(f):
        """错误处理装饰器"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception as e:
                error_msg = str(e)
                print(f"API错误: {error_msg}")
                
                if request.is_json:
                    return jsonify({
                        'success': False,
                        'error': error_msg
                    }), 500
                else:
                    return f"服务器错误: {error_msg}", 500
        return decorated_function

__all__ = [
    'allowed_file', 'parse_filename', 'secure_filename_custom',
    'init_database', 'create_default_admin',
    'require_login', 'handle_errors'
] 