#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级缓存服务
支持内存缓存、Redis缓存和数据库缓存
"""

import time
import json
import hashlib
import threading
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, List
from functools import wraps

class MemoryCache:
    """内存缓存类"""
    
    def __init__(self):
        self._cache = {}
        self._timestamps = {}
        self._access_count = {}
        self._lock = threading.RLock()
        self._max_size = 1000  # 最大缓存条目数
        
    def get(self, key: str, default=None):
        """获取缓存值"""
        with self._lock:
            if key in self._cache:
                self._access_count[key] = self._access_count.get(key, 0) + 1
                return self._cache[key]
            return default
    
    def set(self, key: str, value: Any, ttl: int = 300):
        """设置缓存值"""
        with self._lock:
            # 如果缓存已满，清理最少使用的缓存
            if len(self._cache) >= self._max_size:
                self._evict_lru()
            
            self._cache[key] = value
            self._timestamps[key] = time.time() + ttl
            self._access_count[key] = 1
    
    def delete(self, key: str):
        """删除缓存"""
        with self._lock:
            self._cache.pop(key, None)
            self._timestamps.pop(key, None)
            self._access_count.pop(key, None)
    
    def is_expired(self, key: str) -> bool:
        """检查是否过期"""
        if key not in self._timestamps:
            return True
        return time.time() > self._timestamps[key]
    
    def cleanup_expired(self):
        """清理过期缓存"""
        with self._lock:
            current_time = time.time()
            expired_keys = [
                key for key, expire_time in self._timestamps.items()
                if current_time > expire_time
            ]
            
            for key in expired_keys:
                self.delete(key)
    
    def _evict_lru(self):
        """清理最少使用的缓存"""
        if not self._access_count:
            return
        
        # 找到访问次数最少的key
        lru_key = min(self._access_count.keys(), key=lambda k: self._access_count[k])
        self.delete(lru_key)
    
    def stats(self) -> Dict:
        """获取缓存统计"""
        with self._lock:
            return {
                'size': len(self._cache),
                'max_size': self._max_size,
                'hit_ratio': sum(self._access_count.values()) / max(len(self._access_count), 1)
            }

class CacheService:
    """缓存服务管理器"""
    
    def __init__(self):
        self.memory_cache = MemoryCache()
        self._cache_stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0
        }
        
        # 启动后台清理线程
        self._start_cleanup_thread()
    
    def _start_cleanup_thread(self):
        """启动后台清理线程"""
        def cleanup_worker():
            while True:
                try:
                    self.memory_cache.cleanup_expired()
                    time.sleep(60)  # 每分钟清理一次
                except Exception as e:
                    print(f"缓存清理失败: {e}")
                    time.sleep(60)
        
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
    
    def generate_key(self, prefix: str, **kwargs) -> str:
        """生成缓存键"""
        key_data = f"{prefix}:{json.dumps(kwargs, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, key: str, default=None) -> Any:
        """获取缓存"""
        # 先检查内存缓存
        if not self.memory_cache.is_expired(key):
            value = self.memory_cache.get(key)
            if value is not None:
                self._cache_stats['hits'] += 1
                return value
        
        self._cache_stats['misses'] += 1
        return default
    
    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """设置缓存"""
        try:
            # 存储到内存缓存
            self.memory_cache.set(key, value, ttl)
            self._cache_stats['sets'] += 1
            return True
        except Exception as e:
            print(f"设置缓存失败: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            self.memory_cache.delete(key)
            self._cache_stats['deletes'] += 1
            return True
        except Exception as e:
            print(f"删除缓存失败: {e}")
            return False
    
    def get_or_set(self, key: str, callback, ttl: int = 300) -> Any:
        """获取缓存，如果不存在则调用回调函数设置"""
        value = self.get(key)
        if value is not None:
            return value
        
        # 生成新值
        try:
            value = callback()
            self.set(key, value, ttl)
            return value
        except Exception as e:
            print(f"缓存回调函数执行失败: {e}")
            return None
    
    def clear_pattern(self, pattern: str):
        """清理匹配模式的缓存"""
        import re
        try:
            pattern_re = re.compile(pattern)
            keys_to_delete = []
            
            for key in self.memory_cache._cache.keys():
                if pattern_re.search(key):
                    keys_to_delete.append(key)
            
            for key in keys_to_delete:
                self.delete(key)
                
        except Exception as e:
            print(f"清理缓存模式失败: {e}")
    
    def stats(self) -> Dict:
        """获取缓存统计信息"""
        memory_stats = self.memory_cache.stats()
        
        total_operations = sum(self._cache_stats.values())
        hit_ratio = self._cache_stats['hits'] / max(total_operations, 1) * 100
        
        return {
            'memory_cache': memory_stats,
            'operations': self._cache_stats,
            'hit_ratio': round(hit_ratio, 2),
            'total_operations': total_operations
        }

# 全局缓存实例
cache_service = CacheService()

def cached(ttl: int = 300, key_prefix: str = None):
    """缓存装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            prefix = key_prefix or f"{func.__module__}.{func.__name__}"
            cache_key = cache_service.generate_key(prefix, args=args, kwargs=kwargs)
            
            # 尝试从缓存获取
            result = cache_service.get(cache_key)
            if result is not None:
                return result
            
            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            cache_service.set(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator

def cache_invalidate(pattern: str):
    """缓存失效装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            # 执行完成后清理相关缓存
            cache_service.clear_pattern(pattern)
            return result
        return wrapper
    return decorator

class DatabaseQueryCache:
    """数据库查询缓存"""
    
    @staticmethod
    def cached_query(query_func, cache_key: str, ttl: int = 600):
        """缓存数据库查询结果"""
        return cache_service.get_or_set(
            cache_key, 
            query_func, 
            ttl
        )
    
    @staticmethod
    def invalidate_model_cache(model_name: str):
        """清理模型相关的缓存"""
        pattern = f".*{model_name}.*"
        cache_service.clear_pattern(pattern)

# API响应缓存
class APIResponseCache:
    """API响应缓存"""
    
    @staticmethod
    def cache_api_response(endpoint: str, params: dict = None, ttl: int = 300):
        """缓存API响应"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # 生成缓存键
                cache_key = cache_service.generate_key(
                    f"api:{endpoint}",
                    params=params or {},
                    kwargs=kwargs
                )
                
                # 尝试从缓存获取
                cached_response = cache_service.get(cache_key)
                if cached_response is not None:
                    return cached_response
                
                # 执行API函数
                response = func(*args, **kwargs)
                
                # 缓存成功响应
                if hasattr(response, 'status_code') and response.status_code == 200:
                    cache_service.set(cache_key, response, ttl)
                elif isinstance(response, (dict, list)):
                    cache_service.set(cache_key, response, ttl)
                
                return response
            
            return wrapper
        return decorator

# 缓存预热
class CacheWarmer:
    """缓存预热器"""
    
    def __init__(self):
        self.warming_tasks = []
    
    def add_warming_task(self, key: str, callback, ttl: int = 600):
        """添加预热任务"""
        self.warming_tasks.append({
            'key': key,
            'callback': callback,
            'ttl': ttl
        })
    
    def warm_up(self):
        """执行缓存预热"""
        print("开始缓存预热...")
        
        for task in self.warming_tasks:
            try:
                key = task['key']
                if cache_service.get(key) is None:
                    value = task['callback']()
                    cache_service.set(key, value, task['ttl'])
                    print(f"预热缓存: {key}")
            except Exception as e:
                print(f"预热缓存失败 {task['key']}: {e}")
        
        print("缓存预热完成")

# 全局缓存预热器
cache_warmer = CacheWarmer()

# 导出主要接口
__all__ = [
    'cache_service',
    'cached',
    'cache_invalidate', 
    'DatabaseQueryCache',
    'APIResponseCache',
    'cache_warmer'
] 