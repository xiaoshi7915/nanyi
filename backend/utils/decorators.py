#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
装饰器工具
"""

from functools import wraps
from flask import jsonify, request
import traceback

def handle_errors(f):
    """错误处理装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            error_msg = str(e)
            print(f"API错误: {error_msg}")
            print(f"错误详情: {traceback.format_exc()}")
            
            return jsonify({
                'success': False,
                'error': error_msg,
                'message': '服务器内部错误'
            }), 500
    
    return decorated_function

def require_json(f):
    """要求JSON输入的装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': '请求必须是JSON格式'
            }), 400
        return f(*args, **kwargs)
    
    return decorated_function

def validate_params(required_params):
    """参数验证装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.method in ['POST', 'PUT']:
                data = request.get_json()
                if not data:
                    return jsonify({
                        'success': False,
                        'error': '请求数据不能为空'
                    }), 400
                
                missing_params = []
                for param in required_params:
                    if param not in data or not data[param]:
                        missing_params.append(param)
                
                if missing_params:
                    return jsonify({
                        'success': False,
                        'error': f'缺少必需参数: {", ".join(missing_params)}'
                    }), 400
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def cache_response(seconds=300):
    """响应缓存装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            response = f(*args, **kwargs)
            if hasattr(response, 'cache_control'):
                response.cache_control.max_age = seconds
            return response
        
        return decorated_function
    return decorator