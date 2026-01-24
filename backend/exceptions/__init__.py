#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一异常处理体系
定义基础异常类和具体异常类，用于统一错误处理
"""


class BaseAPIException(Exception):
    """
    基础API异常类
    所有API异常都应该继承此类
    """
    
    def __init__(self, message: str, status_code: int = 500, error_code: str = None, details: dict = None):
        """
        初始化异常
        
        Args:
            message: 错误消息
            status_code: HTTP状态码
            error_code: 错误代码（用于前端识别错误类型）
            details: 额外错误详情
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
    
    def to_dict(self):
        """
        将异常转换为字典格式，用于JSON响应
        
        Returns:
            dict: 包含错误信息的字典
        """
        return {
            'success': False,
            'error': self.message,
            'error_code': self.error_code,
            'status_code': self.status_code,
            **self.details
        }


class ValidationError(BaseAPIException):
    """
    参数验证错误
    当请求参数不符合要求时抛出
    """
    
    def __init__(self, message: str = '参数验证失败', field: str = None, value: any = None, details: dict = None):
        """
        初始化验证错误
        
        Args:
            message: 错误消息
            field: 验证失败的字段名
            value: 验证失败的值
            details: 额外错误详情
        """
        error_details = details or {}
        if field:
            error_details['field'] = field
        if value is not None:
            error_details['value'] = value
        
        super().__init__(
            message=message,
            status_code=400,
            error_code='VALIDATION_ERROR',
            details=error_details
        )


class NotFoundError(BaseAPIException):
    """
    资源不存在错误
    当请求的资源不存在时抛出
    """
    
    def __init__(self, message: str = '资源不存在', resource_type: str = None, resource_id: any = None, details: dict = None):
        """
        初始化资源不存在错误
        
        Args:
            message: 错误消息
            resource_type: 资源类型（如 'product', 'brand'）
            resource_id: 资源ID或标识符
            details: 额外错误详情
        """
        error_details = details or {}
        if resource_type:
            error_details['resource_type'] = resource_type
        if resource_id is not None:
            error_details['resource_id'] = resource_id
        
        super().__init__(
            message=message,
            status_code=404,
            error_code='NOT_FOUND',
            details=error_details
        )


class PermissionError(BaseAPIException):
    """
    权限错误
    当用户没有权限执行操作时抛出
    """
    
    def __init__(self, message: str = '权限不足', required_permission: str = None, details: dict = None):
        """
        初始化权限错误
        
        Args:
            message: 错误消息
            required_permission: 所需的权限
            details: 额外错误详情
        """
        error_details = details or {}
        if required_permission:
            error_details['required_permission'] = required_permission
        
        super().__init__(
            message=message,
            status_code=403,
            error_code='PERMISSION_DENIED',
            details=error_details
        )


class DatabaseError(BaseAPIException):
    """
    数据库错误
    当数据库操作失败时抛出
    """
    
    def __init__(self, message: str = '数据库操作失败', operation: str = None, details: dict = None):
        """
        初始化数据库错误
        
        Args:
            message: 错误消息
            operation: 数据库操作类型（如 'query', 'insert', 'update', 'delete'）
            details: 额外错误详情
        """
        error_details = details or {}
        if operation:
            error_details['operation'] = operation
        
        super().__init__(
            message=message,
            status_code=500,
            error_code='DATABASE_ERROR',
            details=error_details
        )


class ServiceError(BaseAPIException):
    """
    服务层错误
    当业务逻辑处理失败时抛出
    """
    
    def __init__(self, message: str = '服务处理失败', service_name: str = None, details: dict = None):
        """
        初始化服务错误
        
        Args:
            message: 错误消息
            service_name: 服务名称（如 'ProductService', 'ImageService'）
            details: 额外错误详情
        """
        error_details = details or {}
        if service_name:
            error_details['service_name'] = service_name
        
        super().__init__(
            message=message,
            status_code=500,
            error_code='SERVICE_ERROR',
            details=error_details
        )


class AuthenticationError(BaseAPIException):
    """
    认证错误
    当用户未登录或认证失败时抛出
    """
    
    def __init__(self, message: str = '认证失败', reason: str = None, details: dict = None):
        """
        初始化认证错误
        
        Args:
            message: 错误消息
            reason: 认证失败的原因
            details: 额外错误详情
        """
        error_details = details or {}
        if reason:
            error_details['reason'] = reason
        
        super().__init__(
            message=message,
            status_code=401,
            error_code='AUTHENTICATION_ERROR',
            details=error_details
        )


class RateLimitError(BaseAPIException):
    """
    限流错误
    当请求频率超过限制时抛出
    """
    
    def __init__(self, message: str = '请求过于频繁，请稍后再试', retry_after: int = None, details: dict = None):
        """
        初始化限流错误
        
        Args:
            message: 错误消息
            retry_after: 重试等待时间（秒）
            details: 额外错误详情
        """
        error_details = details or {}
        if retry_after:
            error_details['retry_after'] = retry_after
        
        super().__init__(
            message=message,
            status_code=429,
            error_code='RATE_LIMIT_EXCEEDED',
            details=error_details
        )


# 导出所有异常类
__all__ = [
    'BaseAPIException',
    'ValidationError',
    'NotFoundError',
    'PermissionError',
    'DatabaseError',
    'ServiceError',
    'AuthenticationError',
    'RateLimitError'
]
