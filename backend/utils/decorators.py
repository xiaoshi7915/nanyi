#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一装饰器工具模块
提供统一的错误处理、参数验证等功能
"""

from functools import wraps
from flask import jsonify, request, current_app
import traceback
import logging
from backend.exceptions import (
    BaseAPIException,
    ValidationError,
    NotFoundError,
    PermissionError,
    DatabaseError,
    ServiceError,
    AuthenticationError,
    RateLimitError
)

logger = logging.getLogger(__name__)

def handle_errors(f):
    """
    统一错误处理装饰器
    捕获具体异常类型，记录详细错误信息
    优先使用自定义异常类体系
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except BaseAPIException as e:
            # 自定义API异常，直接使用异常类的to_dict()方法
            logger.warning(f"API异常 {f.__name__}: {e.message} (错误代码: {e.error_code})")
            return jsonify(e.to_dict()), e.status_code
        except ValidationError as e:
            # 参数验证错误（兼容标准异常）
            logger.warning(f"参数验证错误 {f.__name__}: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'error_code': 'VALIDATION_ERROR',
                'type': 'validation_error'
            }), 400
        except PermissionError as e:
            # 权限错误（兼容标准异常）
            logger.warning(f"权限错误 {f.__name__}: {e}")
            return jsonify({
                'success': False,
                'error': '权限不足',
                'error_code': 'PERMISSION_DENIED',
                'type': 'permission_error'
            }), 403
        except FileNotFoundError as e:
            # 文件未找到，转换为NotFoundError
            logger.warning(f"文件未找到 {f.__name__}: {e}")
            not_found_error = NotFoundError(
                message='资源不存在',
                details={'original_error': str(e)}
            )
            return jsonify(not_found_error.to_dict()), not_found_error.status_code
        except ValueError as e:
            # 值错误，转换为ValidationError
            logger.warning(f"参数验证错误 {f.__name__}: {e}")
            validation_error = ValidationError(
                message=str(e),
                details={'original_error': str(e)}
            )
            return jsonify(validation_error.to_dict()), validation_error.status_code
        except Exception as e:
            # 其他未预期的错误
            error_msg = str(e)
            error_traceback = traceback.format_exc()
            logger.error(f"API错误 {f.__name__}: {error_msg}\n{error_traceback}")
            
            # 生产环境不返回详细错误信息
            if current_app.config.get('DEBUG', False):
                return jsonify({
                    'success': False,
                    'error': error_msg,
                    'error_code': 'SERVER_ERROR',
                    'traceback': error_traceback,
                    'type': 'server_error'
                }), 500
            else:
                return jsonify({
                    'success': False,
                    'error': '服务器内部错误',
                    'error_code': 'SERVER_ERROR',
                    'type': 'server_error'
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