#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库管理器
统一管理数据库会话、事务和连接池
"""

from functools import wraps
from typing import Callable, Any, Optional
from contextlib import contextmanager
import logging

from backend.models import db
from backend.exceptions import DatabaseError
from backend.utils.logger import logger

# 创建模块级别的logger
db_logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    数据库管理器类
    提供统一的数据库会话管理、事务管理和连接池管理
    """
    
    @staticmethod
    def get_session():
        """
        获取数据库会话
        
        Returns:
            SQLAlchemy会话对象
        """
        return db.session
    
    @staticmethod
    @contextmanager
    def session_scope():
        """
        数据库会话上下文管理器
        自动处理提交和回滚
        
        Yields:
            SQLAlchemy会话对象
        
        Example:
            with DatabaseManager.session_scope() as session:
                product = Product(name='test')
                session.add(product)
                # 自动提交，如果出错则自动回滚
        """
        session = db.session
        try:
            yield session
            session.commit()
            db_logger.debug("数据库事务提交成功")
        except Exception as e:
            session.rollback()
            db_logger.error(f"数据库事务回滚: {e}", exc_info=True)
            raise DatabaseError(
                message=f"数据库操作失败: {str(e)}",
                operation="transaction",
                details={'error': str(e)}
            )
        finally:
            session.close()
    
    @staticmethod
    def execute_query(query_func: Callable, *args, **kwargs) -> Any:
        """
        执行数据库查询，自动处理异常
        
        Args:
            query_func: 查询函数
            *args: 位置参数
            **kwargs: 关键字参数
        
        Returns:
            查询结果
        
        Raises:
            DatabaseError: 数据库操作失败时抛出
        """
        try:
            result = query_func(*args, **kwargs)
            db_logger.debug(f"数据库查询成功: {query_func.__name__}")
            return result
        except Exception as e:
            db_logger.error(f"数据库查询失败: {e}", exc_info=True)
            raise DatabaseError(
                message=f"数据库查询失败: {str(e)}",
                operation="query",
                details={'query_func': query_func.__name__, 'error': str(e)}
            )
    
    @staticmethod
    def execute_transaction(transaction_func: Callable, *args, **kwargs) -> Any:
        """
        执行数据库事务，自动处理提交和回滚
        
        Args:
            transaction_func: 事务函数
            *args: 位置参数
            **kwargs: 关键字参数
        
        Returns:
            事务执行结果
        
        Raises:
            DatabaseError: 数据库操作失败时抛出
        """
        session = db.session
        try:
            result = transaction_func(session, *args, **kwargs)
            session.commit()
            db_logger.debug(f"数据库事务执行成功: {transaction_func.__name__}")
            return result
        except Exception as e:
            session.rollback()
            db_logger.error(f"数据库事务执行失败: {e}", exc_info=True)
            raise DatabaseError(
                message=f"数据库事务失败: {str(e)}",
                operation="transaction",
                details={'transaction_func': transaction_func.__name__, 'error': str(e)}
            )
        finally:
            session.close()
    
    @staticmethod
    def check_connection() -> bool:
        """
        检查数据库连接是否正常
        
        Returns:
            bool: 连接是否正常
        """
        try:
            # 执行简单查询测试连接
            db.session.execute('SELECT 1')
            db_logger.debug("数据库连接检查成功")
            return True
        except Exception as e:
            db_logger.error(f"数据库连接检查失败: {e}", exc_info=True)
            return False
    
    @staticmethod
    def get_connection_pool_stats() -> dict:
        """
        获取连接池统计信息
        
        Returns:
            dict: 连接池统计信息
        """
        try:
            engine = db.engine
            pool = engine.pool
            
            stats = {
                'pool_size': pool.size(),
                'checked_in': pool.checkedin(),
                'checked_out': pool.checkedout(),
                'overflow': pool.overflow(),
                'invalid': pool.invalid()
            }
            
            db_logger.debug(f"连接池统计信息: {stats}")
            return stats
        except Exception as e:
            db_logger.warning(f"获取连接池统计信息失败: {e}")
            return {}


def transactional(func: Callable) -> Callable:
    """
    事务装饰器
    自动处理数据库事务的提交和回滚
    
    Args:
        func: 被装饰的函数
    
    Returns:
        装饰后的函数
    
    Example:
        @transactional
        def create_product(data):
            product = Product(**data)
            db.session.add(product)
            return product
            # 自动提交，如果出错则自动回滚
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        session = db.session
        try:
            result = func(*args, **kwargs)
            session.commit()
            db_logger.debug(f"事务装饰器: {func.__name__} 提交成功")
            return result
        except Exception as e:
            session.rollback()
            db_logger.error(f"事务装饰器: {func.__name__} 回滚: {e}", exc_info=True)
            raise DatabaseError(
                message=f"数据库事务失败: {str(e)}",
                operation=func.__name__,
                details={'error': str(e)}
            )
        finally:
            session.close()
    
    return wrapper


def query_cache(ttl: int = 300, key_prefix: str = None):
    """
    查询结果缓存装饰器
    缓存数据库查询结果，减少数据库压力
    
    Args:
        ttl: 缓存过期时间（秒），默认300秒
        key_prefix: 缓存键前缀（如果不提供，使用函数名）
    
    Returns:
        装饰器函数
    
    Example:
        @query_cache(ttl=600, key_prefix='products')
        def get_all_products():
            return Product.query.all()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 导入缓存服务（避免循环导入）
            from backend.services.cache_service import cache_service
            
            # 生成缓存键
            if key_prefix:
                prefix = key_prefix
            else:
                prefix = func.__name__
            
            # 构建缓存键（包含参数）
            cache_key = cache_service.generate_key(
                prefix,
                args=args,
                kwargs=kwargs
            )
            
            # 尝试从缓存获取
            cached_result = cache_service.get(cache_key)
            if cached_result is not None:
                db_logger.debug(f"查询缓存命中: {cache_key}")
                return cached_result
            
            # 执行查询
            result = func(*args, **kwargs)
            
            # 缓存结果
            cache_service.set(cache_key, result, ttl)
            db_logger.debug(f"查询结果已缓存: {cache_key} (TTL: {ttl}s)")
            
            return result
        
        return wrapper
    return decorator


def db_retry(max_retries: int = 3, retry_delay: float = 1.0):
    """
    数据库操作重试装饰器
    当数据库操作失败时自动重试
    
    Args:
        max_retries: 最大重试次数，默认3次
        retry_delay: 重试延迟（秒），默认1秒
    
    Returns:
        装饰器函数
    
    Example:
        @db_retry(max_retries=5, retry_delay=2.0)
        def critical_operation():
            # 关键数据库操作
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            import time
            
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except DatabaseError as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        db_logger.warning(
                            f"数据库操作失败，{retry_delay}秒后重试 "
                            f"({attempt + 1}/{max_retries}): {e}"
                        )
                        time.sleep(retry_delay)
                    else:
                        db_logger.error(f"数据库操作重试{max_retries}次后仍失败: {e}")
                        raise
            
            # 如果所有重试都失败，抛出最后一个异常
            raise last_exception
        
        return wrapper
    return decorator


# 创建全局数据库管理器实例
db_manager = DatabaseManager()

# 导出
__all__ = [
    'DatabaseManager',
    'db_manager',
    'transactional',
    'query_cache',
    'db_retry'
]
