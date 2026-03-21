#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API请求限流工具
使用内存存储实现简单的限流功能
生产环境建议使用Redis实现分布式限流
"""

from functools import wraps
from collections import defaultdict
import time
import logging

from backend.utils.response import APIResponse
from backend.utils.client_ip import get_trusted_client_ip

logger = logging.getLogger(__name__)

# 内存存储：{scope_ip: [(timestamp, count), ...]}，按 scope 分桶避免与无关接口共用配额
_rate_limit_store = defaultdict(list)
_last_cleanup = time.time()

def _cleanup_old_records():
    """清理过期的限流记录"""
    global _last_cleanup
    current_time = time.time()
    
    # 每5分钟清理一次
    if current_time - _last_cleanup < 300:
        return
    
    _last_cleanup = current_time
    cutoff_time = current_time - 3600  # 保留1小时内的记录
    
    for key in list(_rate_limit_store.keys()):
        _rate_limit_store[key] = [
            (ts, count) for ts, count in _rate_limit_store[key]
            if ts > cutoff_time
        ]
        if not _rate_limit_store[key]:
            del _rate_limit_store[key]

def rate_limit(max_requests=60, per_seconds=60, per_minute=None, scope='global'):
    """
    请求限流装饰器
    
    Args:
        max_requests: 允许的最大请求数
        per_seconds: 时间窗口（秒）
        per_minute: 每分钟最大请求数（如果设置，会覆盖per_seconds）
        scope: 限流分桶标识，不同接口应使用不同 scope 以免共用配额
    """
    if per_minute:
        per_seconds = 60
        max_requests = per_minute
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            client_ip = get_trusted_client_ip()
            store_key = f"{scope}:{client_ip}"
            
            # 清理过期记录
            _cleanup_old_records()
            
            # 获取当前时间窗口内的请求数
            current_time = time.time()
            window_start = current_time - per_seconds
            
            # 过滤出时间窗口内的请求
            recent_requests = [
                ts for ts, _ in _rate_limit_store[store_key]
                if ts > window_start
            ]
            
            # 检查是否超过限制
            if len(recent_requests) >= max_requests:
                logger.warning(
                    "请求限流触发: scope=%s IP=%s 请求数=%s/%s",
                    scope, client_ip, len(recent_requests), max_requests,
                )
                retry_after = max(1, int(per_seconds - (current_time - recent_requests[0])))
                return APIResponse.rate_limit_exceeded(
                    message=f'请求过于频繁，请稍后再试（限流: {max_requests} 次 / {per_seconds} 秒）',
                    retry_after=retry_after,
                )
            
            # 记录本次请求
            _rate_limit_store[store_key].append((current_time, 1))
            
            # 执行原函数
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def get_rate_limit_stats():
    """获取限流统计信息"""
    _cleanup_old_records()
    
    stats = {}
    current_time = time.time()
    
    for key, requests in _rate_limit_store.items():
        # 统计最近1小时的请求数
        hour_ago = current_time - 3600
        recent_count = len([ts for ts, _ in requests if ts > hour_ago])
        stats[key] = {
            'total_requests_1h': recent_count,
            'last_request': max([ts for ts, _ in requests]) if requests else None
        }
    
    return stats
