#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redis缓存服务
提供Redis缓存实现，用于替换内存缓存
"""

import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis未安装，Redis缓存功能不可用。安装: pip install redis")

class RedisCacheService:
    """Redis缓存服务"""
    
    def __init__(self, host='localhost', port=6379, db=0, password=None, decode_responses=True):
        """
        初始化Redis缓存服务
        
        Args:
            host: Redis主机地址
            port: Redis端口
            db: Redis数据库编号
            password: Redis密码
            decode_responses: 是否自动解码响应
        """
        if not REDIS_AVAILABLE:
            raise ImportError("Redis未安装，请先安装: pip install redis")
        
        try:
            self.redis_client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=decode_responses,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # 测试连接
            self.redis_client.ping()
            logger.info("✅ Redis连接成功")
        except Exception as e:
            logger.error(f"❌ Redis连接失败: {e}")
            raise
    
    def get(self, key: str, default=None) -> Any:
        """获取缓存值"""
        try:
            value = self.redis_client.get(key)
            if value is None:
                return default
            # 尝试解析JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        except Exception as e:
            logger.error(f"Redis获取缓存失败 {key}: {e}")
            return default
    
    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """设置缓存值"""
        try:
            # 序列化值
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value, ensure_ascii=False)
            else:
                serialized_value = str(value)
            
            self.redis_client.setex(key, ttl, serialized_value)
            return True
        except Exception as e:
            logger.error(f"Redis设置缓存失败 {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis删除缓存失败 {key}: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """清理匹配模式的缓存"""
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Redis清理缓存模式失败 {pattern}: {e}")
            return 0
    
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        try:
            return self.redis_client.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis检查键存在失败 {key}: {e}")
            return False
    
    def get_stats(self) -> dict:
        """获取Redis统计信息"""
        try:
            info = self.redis_client.info()
            return {
                'connected_clients': info.get('connected_clients', 0),
                'used_memory_human': info.get('used_memory_human', '0B'),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'total_keys': sum([
                    int(info.get(f'db{i}', {}).get('keys', 0) or 0)
                    for i in range(16)
                ])
            }
        except Exception as e:
            logger.error(f"获取Redis统计信息失败: {e}")
            return {}

def get_redis_cache_service():
    """获取Redis缓存服务实例（如果可用）"""
    import os
    if not REDIS_AVAILABLE:
        return None
    
    try:
        redis_host = os.environ.get('REDIS_HOST', 'localhost')
        redis_port = int(os.environ.get('REDIS_PORT', 6379))
        redis_db = int(os.environ.get('REDIS_DB', 0))
        redis_password = os.environ.get('REDIS_PASSWORD')
        
        return RedisCacheService(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            password=redis_password
        )
    except Exception as e:
        logger.warning(f"Redis缓存服务不可用: {e}")
        return None
