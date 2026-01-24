#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API请求限流工具
使用内存存储实现简单的限流功能
生产环境建议使用Redis实现分布式限流
"""

from functools import wraps
from flask import request, jsonify, current_app
from collections import defaultdict
from datetime import datetime, timedelta
import time
import logging

logger = logging.getLogger(__name__)

# 内存存储：{ip: [(timestamp, count), ...]}
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
    
    for ip in list(_rate_limit_store.keys()):
        _rate_limit_store[ip] = [
            (ts, count) for ts, count in _rate_limit_store[ip]
            if ts > cutoff_time
        ]
        if not _rate_limit_store[ip]:
            del _rate_limit_store[ip]

def rate_limit(max_requests=60, per_seconds=60, per_minute=None):
    """
    请求限流装饰器
    
    Args:
        max_requests: 允许的最大请求数
        per_seconds: 时间窗口（秒）
        per_minute: 每分钟最大请求数（如果设置，会覆盖per_seconds）
    """
    if per_minute:
        per_seconds = 60
        max_requests = per_minute
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 获取客户端IP
            if request.headers.get('X-Forwarded-For'):
                client_ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
            else:
                client_ip = request.remote_addr or 'unknown'
            
            # 清理过期记录
            _cleanup_old_records()
            
            # 获取当前时间窗口内的请求数
            current_time = time.time()
            window_start = current_time - per_seconds
            
            # 过滤出时间窗口内的请求
            recent_requests = [
                ts for ts, _ in _rate_limit_store[client_ip]
                if ts > window_start
            ]
            
            # 检查是否超过限制
            if len(recent_requests) >= max_requests:
                logger.warning(f"请求限流触发: IP={client_ip}, 请求数={len(recent_requests)}/{max_requests}")
                return jsonify({
                    'success': False,
                    'error': f'请求过于频繁，请稍后再试。限制: {max_requests}次/{per_seconds}秒',
                    'type': 'rate_limit_exceeded',
                    'retry_after': int(per_seconds - (current_time - recent_requests[0]))
                }), 429
            
            # 记录本次请求
            _rate_limit_store[client_ip].append((current_time, 1))
            
            # 执行原函数
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def get_rate_limit_stats():
    """获取限流统计信息"""
    _cleanup_old_records()
    
    stats = {}
    current_time = time.time()
    
    for ip, requests in _rate_limit_store.items():
        # 统计最近1小时的请求数
        hour_ago = current_time - 3600
        recent_count = len([ts for ts, _ in requests if ts > hour_ago])
        stats[ip] = {
            'total_requests_1h': recent_count,
            'last_request': max([ts for ts, _ in requests]) if requests else None
        }
    
    return stats
