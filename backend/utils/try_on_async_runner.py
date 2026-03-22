#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
异步任务运行器
封装 asyncio 在线程池中的执行，用于在 Flask 同步环境中运行异步任务
"""

import asyncio
import threading
import concurrent.futures
from typing import Callable, Any, Optional, TypeVar, Coroutine
from functools import wraps
import traceback

from backend.utils.logger import logger

# 类型变量，用于泛型
T = TypeVar('T')


class AsyncTaskRunner:
    """
    异步任务运行器
    使用线程池执行 asyncio.run()，用于在 Flask 同步环境中执行异步任务
    
    方案：使用 asyncio.run() 在后台线程中执行异步任务
    优点：保持原有异步逻辑，改动最小
    """
    
    def __init__(self, max_workers: int = 5):
        """
        初始化异步任务运行器
        
        Args:
            max_workers: 线程池最大工作线程数
        """
        self.max_workers = max_workers
        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="async_runner"
        )
        logger.info(f"异步任务运行器已初始化，最大工作线程数: {max_workers}")
    
    def run_async(self, coro: Coroutine[Any, Any, T], timeout: Optional[float] = None) -> T:
        """
        在后台线程中使用 asyncio.run() 运行异步协程（同步调用，阻塞直到完成）
        
        Args:
            coro: 要运行的协程
            timeout: 超时时间（秒），None 表示不超时
        
        Returns:
            协程的返回值
        
        Raises:
            TimeoutError: 如果超时
            Exception: 协程执行过程中的异常
        """
        def run_coro():
            """在线程池中运行协程"""
            try:
                # 使用 asyncio.run() 在新线程中运行协程
                # 每个线程会创建自己的事件循环
                return asyncio.run(coro)
            except Exception as e:
                logger.error(f"异步任务执行错误: {e}", exc_info=True)
                raise
        
        # 在线程池中执行并等待结果（带超时）
        try:
            future = self.executor.submit(run_coro)
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            raise TimeoutError(f"异步任务执行超时（{timeout}秒）")
    
    def run_async_in_thread(self, coro: Coroutine[Any, Any, T]) -> concurrent.futures.Future:
        """
        在后台线程中异步运行协程（非阻塞）
        
        Args:
            coro: 要运行的协程
        
        Returns:
            Future 对象，可以通过 future.result() 获取结果
        """
        def run_coro():
            """在线程池中运行协程"""
            try:
                # 使用 asyncio.run() 在新线程中运行协程
                return asyncio.run(coro)
            except Exception as e:
                logger.error(f"异步任务执行错误: {e}", exc_info=True)
                raise
        
        # 在线程池中执行（非阻塞）
        return self.executor.submit(run_coro)
    
    def shutdown(self, wait: bool = True):
        """
        关闭线程池
        
        Args:
            wait: 是否等待所有任务完成
        """
        self.executor.shutdown(wait=wait)
        logger.info("异步任务运行器已关闭")


# 全局异步任务运行器实例
_async_runner: Optional[AsyncTaskRunner] = None


def get_async_runner() -> AsyncTaskRunner:
    """
    获取全局异步任务运行器实例
    
    Returns:
        AsyncTaskRunner 实例
    """
    global _async_runner
    if _async_runner is None:
        _async_runner = AsyncTaskRunner()
    return _async_runner


def run_async_sync(coro: Coroutine[Any, Any, T], timeout: Optional[float] = None) -> T:
    """
    在后台线程中同步运行异步协程（阻塞直到完成）
    
    这是一个便捷函数，用于在 Flask 同步代码中运行异步函数
    使用 asyncio.run() 在后台线程中执行
    
    Args:
        coro: 要运行的协程
        timeout: 超时时间（秒），None 表示不超时
    
    Returns:
        协程的返回值
    
    Example:
        ```python
        async def async_function():
            await some_async_operation()
            return "result"
        
        # 在 Flask 路由中调用
        result = run_async_sync(async_function())
        ```
    """
    runner = get_async_runner()
    return runner.run_async(coro, timeout=timeout)


def run_async_background(coro: Coroutine[Any, Any, T]) -> concurrent.futures.Future:
    """
    在后台线程中异步运行协程（非阻塞）
    
    这是一个便捷函数，用于在 Flask 同步代码中启动异步任务（不等待完成）
    使用 asyncio.run() 在后台线程中执行
    
    Args:
        coro: 要运行的协程
    
    Returns:
        Future 对象，可以通过 future.result() 获取结果（可选）
    
    Example:
        ```python
        async def async_function():
            await some_async_operation()
            return "result"
        
        # 在 Flask 路由中调用（不等待完成）
        future = run_async_background(async_function())
        # 可以继续执行其他代码，不等待异步任务完成
        ```
    """
    runner = get_async_runner()
    return runner.run_async_in_thread(coro)


def async_to_sync(func: Callable[..., Coroutine[Any, Any, T]]) -> Callable[..., T]:
    """
    装饰器：将异步函数转换为同步函数
    
    使用这个装饰器可以将异步函数包装为同步函数，在 Flask 路由中直接调用
    
    Args:
        func: 异步函数
    
    Returns:
        同步包装函数
    
    Example:
        ```python
        @async_to_sync
        async def async_function():
            await some_async_operation()
            return "result"
        
        # 在 Flask 路由中可以直接调用
        @app.route('/api/test')
        def test():
            result = async_function()  # 同步调用
            return result
        ```
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        coro = func(*args, **kwargs)
        return run_async_sync(coro)
    
    return wrapper
