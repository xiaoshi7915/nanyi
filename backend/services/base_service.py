#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础服务类
提供统一的缓存、日志、异常处理功能，供所有服务类继承
"""

import logging
from typing import Any, Optional, Callable
from functools import wraps

from backend.services.cache_service import cache_service
from backend.exceptions import ServiceError, DatabaseError

# 创建模块级别的logger
logger = logging.getLogger(__name__)


class BaseService:
    """
    基础服务类
    提供统一的缓存、日志、异常处理功能
    """
    
    def __init__(self, service_name: str = None):
        """
        初始化基础服务
        
        Args:
            service_name: 服务名称，用于日志和异常处理
        """
        self.service_name = service_name or self.__class__.__name__
        self.logger = logging.getLogger(f"{__name__}.{self.service_name}")
    
    def get_cache(self, key: str, default: Any = None) -> Any:
        """
        从缓存获取数据
        
        Args:
            key: 缓存键
            default: 默认值（如果缓存不存在）
        
        Returns:
            缓存的值或默认值
        """
        try:
            value = cache_service.get(key, default)
            if value is not None:
                self.logger.debug(f"从缓存获取数据: {key}")
            return value
        except Exception as e:
            self.logger.warning(f"获取缓存失败 {key}: {e}", exc_info=True)
            return default
    
    def set_cache(self, key: str, value: Any, ttl: int = 300) -> bool:
        """
        设置缓存数据
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），默认300秒
        
        Returns:
            是否设置成功
        """
        try:
            success = cache_service.set(key, value, ttl)
            if success:
                self.logger.debug(f"设置缓存成功: {key} (TTL: {ttl}s)")
            return success
        except Exception as e:
            self.logger.warning(f"设置缓存失败 {key}: {e}", exc_info=True)
            return False
    
    def delete_cache(self, key: str) -> bool:
        """
        删除缓存
        
        Args:
            key: 缓存键
        
        Returns:
            是否删除成功
        """
        try:
            success = cache_service.delete(key)
            if success:
                self.logger.debug(f"删除缓存成功: {key}")
            return success
        except Exception as e:
            self.logger.warning(f"删除缓存失败 {key}: {e}", exc_info=True)
            return False
    
    def get_or_set_cache(
        self,
        key: str,
        callback: Callable[[], Any],
        ttl: int = 300
    ) -> Any:
        """
        获取缓存，如果不存在则调用回调函数生成并缓存
        
        Args:
            key: 缓存键
            callback: 生成缓存值的回调函数
            ttl: 过期时间（秒）
        
        Returns:
            缓存的值或回调函数生成的值
        """
        # 尝试从缓存获取
        cached_value = self.get_cache(key)
        if cached_value is not None:
            return cached_value
        
        # 缓存不存在，调用回调函数生成值
        try:
            value = callback()
            self.set_cache(key, value, ttl)
            return value
        except Exception as e:
            self.logger.error(
                f"缓存回调函数执行失败 {key}: {e}",
                exc_info=True
            )
            raise ServiceError(
                message=f"服务处理失败: {e}",
                service_name=self.service_name,
                details={'cache_key': key, 'error': str(e)}
            )
    
    def clear_cache_pattern(self, pattern: str) -> int:
        """
        清理匹配模式的缓存
        
        Args:
            pattern: 缓存键模式（正则表达式）
        
        Returns:
            清理的缓存数量
        """
        try:
            count = cache_service.clear_pattern(pattern)
            if count > 0:
                self.logger.info(f"清理缓存模式成功: {pattern} (清理了 {count} 个缓存)")
            return count
        except Exception as e:
            self.logger.warning(f"清理缓存模式失败 {pattern}: {e}", exc_info=True)
            return 0
    
    def handle_database_error(self, operation: str, error: Exception) -> None:
        """
        统一处理数据库错误
        
        Args:
            operation: 数据库操作类型（如 'query', 'insert', 'update', 'delete'）
            error: 异常对象
        
        Raises:
            DatabaseError: 数据库错误异常
        """
        self.logger.error(
            f"数据库操作失败 [{operation}]: {error}",
            exc_info=True
        )
        raise DatabaseError(
            message=f"数据库操作失败: {str(error)}",
            operation=operation,
            details={'service_name': self.service_name, 'error': str(error)}
        )
    
    def handle_service_error(self, message: str, error: Exception = None, details: dict = None) -> None:
        """
        统一处理服务错误
        
        Args:
            message: 错误消息
            error: 异常对象（可选）
            details: 额外错误详情（可选）
        
        Raises:
            ServiceError: 服务错误异常
        """
        error_details = details or {}
        if error:
            error_details['error'] = str(error)
            self.logger.error(
                f"服务处理失败 [{self.service_name}]: {message}",
                exc_info=True
            )
        else:
            self.logger.error(f"服务处理失败 [{self.service_name}]: {message}")
        
        raise ServiceError(
            message=message,
            service_name=self.service_name,
            details=error_details
        )
    
    def log_info(self, message: str, **kwargs):
        """
        记录信息日志
        
        Args:
            message: 日志消息
            **kwargs: 额外的日志上下文信息
        """
        if kwargs:
            context = ', '.join([f"{k}={v}" for k, v in kwargs.items()])
            self.logger.info(f"{message} [{context}]")
        else:
            self.logger.info(message)
    
    def log_warning(self, message: str, **kwargs):
        """
        记录警告日志
        
        Args:
            message: 日志消息
            **kwargs: 额外的日志上下文信息
        """
        if kwargs:
            context = ', '.join([f"{k}={v}" for k, v in kwargs.items()])
            self.logger.warning(f"{message} [{context}]")
        else:
            self.logger.warning(message)
    
    def log_error(self, message: str, error: Exception = None, **kwargs):
        """
        记录错误日志
        
        Args:
            message: 日志消息
            error: 异常对象（可选）
            **kwargs: 额外的日志上下文信息
        """
        if error:
            if kwargs:
                context = ', '.join([f"{k}={v}" for k, v in kwargs.items()])
                self.logger.error(f"{message} [{context}]", exc_info=True)
            else:
                self.logger.error(f"{message}", exc_info=True)
        else:
            if kwargs:
                context = ', '.join([f"{k}={v}" for k, v in kwargs.items()])
                self.logger.error(f"{message} [{context}]")
            else:
                self.logger.error(message)
    
    def log_debug(self, message: str, **kwargs):
        """
        记录调试日志
        
        Args:
            message: 日志消息
            **kwargs: 额外的日志上下文信息
        """
        if kwargs:
            context = ', '.join([f"{k}={v}" for k, v in kwargs.items()])
            self.logger.debug(f"{message} [{context}]")
        else:
            self.logger.debug(message)


def cached_method(ttl: int = 300, key_prefix: str = None):
    """
    方法缓存装饰器
    用于缓存服务方法的返回值
    
    Args:
        ttl: 缓存过期时间（秒）
        key_prefix: 缓存键前缀（如果不提供，使用类名.方法名）
    
    Example:
        class MyService(BaseService):
            @cached_method(ttl=600)
            def get_data(self, id):
                return self.query_data(id)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # 生成缓存键
            if key_prefix:
                prefix = key_prefix
            else:
                prefix = f"{self.__class__.__name__}.{func.__name__}"
            
            cache_key = cache_service.generate_key(prefix, args=args, kwargs=kwargs)
            
            # 尝试从缓存获取
            cached_result = self.get_cache(cache_key)
            if cached_result is not None:
                return cached_result
            
            # 执行方法并缓存结果
            result = func(self, *args, **kwargs)
            self.set_cache(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator
