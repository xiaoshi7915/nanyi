#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一响应格式模块
封装API响应格式，确保所有API返回格式一致
"""

from flask import jsonify
from typing import Any, Dict, Optional, List


class APIResponse:
    """
    API响应封装类
    提供统一的响应格式，包括成功响应、错误响应和分页响应
    """
    
    @staticmethod
    def success(data: Any = None, message: str = '操作成功', **kwargs) -> tuple:
        """
        成功响应
        
        Args:
            data: 响应数据（可以是字典、列表或任何可序列化的对象）
            message: 成功消息
            **kwargs: 额外的响应字段
        
        Returns:
            tuple: (Flask Response对象, HTTP状态码)
        
        Example:
            >>> APIResponse.success({'id': 1, 'name': 'test'}, '创建成功')
            >>> APIResponse.success(data=[1, 2, 3], message='查询成功', total=3)
        """
        response_data = {
            'success': True,
            'message': message
        }
        
        # 添加数据
        if data is not None:
            response_data['data'] = data
        
        # 添加额外字段
        response_data.update(kwargs)
        
        return jsonify(response_data), 200
    
    @staticmethod
    def error(
        message: str = '操作失败',
        error_code: str = None,
        status_code: int = 500,
        details: Dict = None,
        **kwargs
    ) -> tuple:
        """
        错误响应
        
        Args:
            message: 错误消息
            error_code: 错误代码（用于前端识别错误类型）
            status_code: HTTP状态码
            details: 错误详情
            **kwargs: 额外的响应字段
        
        Returns:
            tuple: (Flask Response对象, HTTP状态码)
        
        Example:
            >>> APIResponse.error('参数验证失败', error_code='VALIDATION_ERROR', status_code=400)
            >>> APIResponse.error('资源不存在', error_code='NOT_FOUND', status_code=404, resource_id=123)
        """
        response_data = {
            'success': False,
            'error': message
        }
        
        # 添加错误代码
        if error_code:
            response_data['error_code'] = error_code
        
        # 添加错误详情
        if details:
            response_data.update(details)
        
        # 添加额外字段
        response_data.update(kwargs)
        
        return jsonify(response_data), status_code
    
    @staticmethod
    def paginated(
        items: List[Any],
        page: int,
        per_page: int,
        total: int,
        message: str = '查询成功',
        **kwargs
    ) -> tuple:
        """
        分页响应
        
        Args:
            items: 当前页的数据列表
            page: 当前页码
            per_page: 每页数量
            total: 总记录数
            message: 成功消息
            **kwargs: 额外的响应字段（如 brands, filters 等）
        
        Returns:
            tuple: (Flask Response对象, HTTP状态码)
        
        Example:
            >>> APIResponse.paginated(
            ...     items=[{'id': 1}, {'id': 2}],
            ...     page=1,
            ...     per_page=10,
            ...     total=100
            ... )
        """
        # 计算分页信息
        total_pages = (total + per_page - 1) // per_page if per_page > 0 else 1
        has_next = page < total_pages
        has_prev = page > 1
        
        response_data = {
            'success': True,
            'message': message,
            'data': items,
            'pagination': {
                'current_page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': total_pages,
                'has_next': has_next,
                'has_prev': has_prev
            }
        }
        
        # 添加额外字段（如 brands, filters 等）
        response_data.update(kwargs)
        
        return jsonify(response_data), 200
    
    @staticmethod
    def created(data: Any = None, message: str = '创建成功', **kwargs) -> tuple:
        """
        创建成功响应（201状态码）
        
        Args:
            data: 响应数据
            message: 成功消息
            **kwargs: 额外的响应字段
        
        Returns:
            tuple: (Flask Response对象, HTTP状态码 201)
        """
        response_data = {
            'success': True,
            'message': message
        }
        
        if data is not None:
            response_data['data'] = data
        
        response_data.update(kwargs)
        
        return jsonify(response_data), 201
    
    @staticmethod
    def updated(data: Any = None, message: str = '更新成功', **kwargs) -> tuple:
        """
        更新成功响应
        
        Args:
            data: 响应数据
            message: 成功消息
            **kwargs: 额外的响应字段
        
        Returns:
            tuple: (Flask Response对象, HTTP状态码 200)
        """
        return APIResponse.success(data=data, message=message, **kwargs)
    
    @staticmethod
    def deleted(message: str = '删除成功', **kwargs) -> tuple:
        """
        删除成功响应
        
        Args:
            message: 成功消息
            **kwargs: 额外的响应字段
        
        Returns:
            tuple: (Flask Response对象, HTTP状态码 200)
        """
        return APIResponse.success(data=None, message=message, **kwargs)
    
    @staticmethod
    def not_found(message: str = '资源不存在', resource_type: str = None, resource_id: Any = None, details: Dict = None) -> tuple:
        """
        资源不存在响应（404）
        
        Args:
            message: 错误消息
            resource_type: 资源类型
            resource_id: 资源ID
            details: 额外错误详情
        
        Returns:
            tuple: (Flask Response对象, HTTP状态码 404)
        """
        error_details = details or {}
        if resource_type:
            error_details['resource_type'] = resource_type
        if resource_id is not None:
            error_details['resource_id'] = resource_id
        
        return APIResponse.error(
            message=message,
            error_code='NOT_FOUND',
            status_code=404,
            details=error_details
        )
    
    @staticmethod
    def validation_error(message: str = '参数验证失败', field: str = None, value: Any = None, **kwargs) -> tuple:
        """
        参数验证错误响应（400）
        
        Args:
            message: 错误消息
            field: 验证失败的字段名
            value: 验证失败的值
            **kwargs: 额外的响应字段
        
        Returns:
            tuple: (Flask Response对象, HTTP状态码 400)
        """
        details = {}
        if field:
            details['field'] = field
        if value is not None:
            details['value'] = value
        
        return APIResponse.error(
            message=message,
            error_code='VALIDATION_ERROR',
            status_code=400,
            details=details,
            **kwargs
        )
    
    @staticmethod
    def permission_denied(message: str = '权限不足', required_permission: str = None) -> tuple:
        """
        权限不足响应（403）
        
        Args:
            message: 错误消息
            required_permission: 所需的权限
        
        Returns:
            tuple: (Flask Response对象, HTTP状态码 403)
        """
        details = {}
        if required_permission:
            details['required_permission'] = required_permission
        
        return APIResponse.error(
            message=message,
            error_code='PERMISSION_DENIED',
            status_code=403,
            details=details
        )
    
    @staticmethod
    def unauthorized(message: str = '认证失败', reason: str = None) -> tuple:
        """
        认证失败响应（401）
        
        Args:
            message: 错误消息
            reason: 认证失败的原因
        
        Returns:
            tuple: (Flask Response对象, HTTP状态码 401)
        """
        details = {}
        if reason:
            details['reason'] = reason
        
        return APIResponse.error(
            message=message,
            error_code='AUTHENTICATION_ERROR',
            status_code=401,
            details=details
        )
    
    @staticmethod
    def rate_limit_exceeded(message: str = '请求过于频繁，请稍后再试', retry_after: int = None) -> tuple:
        """
        限流响应（429）
        
        Args:
            message: 错误消息
            retry_after: 重试等待时间（秒）
        
        Returns:
            tuple: (Flask Response对象, HTTP状态码 429)
        """
        details = {}
        if retry_after:
            details['retry_after'] = retry_after
        
        return APIResponse.error(
            message=message,
            error_code='RATE_LIMIT_EXCEEDED',
            status_code=429,
            details=details
        )
    
    @staticmethod
    def server_error(message: str = '服务器内部错误', details: Dict = None) -> tuple:
        """
        服务器内部错误响应（500）
        
        Args:
            message: 错误消息
            details: 错误详情（生产环境不应包含敏感信息）
        
        Returns:
            tuple: (Flask Response对象, HTTP状态码 500)
        """
        return APIResponse.error(
            message=message,
            error_code='SERVER_ERROR',
            status_code=500,
            details=details or {}
        )


# 导出APIResponse类
__all__ = ['APIResponse']
