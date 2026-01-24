#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能监控工具
用于分析卡片生成各环节的耗时
"""

import time
import functools
from datetime import datetime
from collections import defaultdict
import threading
from backend.utils.logger import logger

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.timers = defaultdict(list)
        self.counters = defaultdict(int)
        self.lock = threading.Lock()
    
    def timer(self, name):
        """性能计时装饰器"""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    duration = (time.time() - start_time) * 1000  # 转换为毫秒
                    with self.lock:
                        self.timers[name].append(duration)
                        self.counters[name] += 1
                    
                    # 在调试模式下输出耗时
                    if duration > 100:  # 只记录超过100ms的操作
                        logger.debug(f"⏱️ {name}: {duration:.2f}ms")
            return wrapper
        return decorator
    
    def record_time(self, name, duration_ms):
        """手动记录耗时"""
        with self.lock:
            self.timers[name].append(duration_ms)
            self.counters[name] += 1
    
    def get_stats(self):
        """获取性能统计"""
        stats = {}
        with self.lock:
            for name, times in self.timers.items():
                if times:
                    stats[name] = {
                        'count': len(times),
                        'total': sum(times),
                        'average': sum(times) / len(times),
                        'min': min(times),
                        'max': max(times),
                        'latest': times[-1] if times else 0
                    }
        return stats
    
    def print_stats(self):
        """打印性能统计"""
        stats = self.get_stats()
        logger.info("="*50)
        logger.info("📊 性能监控统计")
        logger.info("="*50)
        
        if not stats:
            logger.info("暂无性能数据")
            return
        
        # 按平均耗时排序
        sorted_stats = sorted(stats.items(), key=lambda x: x[1]['average'], reverse=True)
        
        for name, data in sorted_stats:
            logger.info(f"\n🔍 {name}:")
            logger.info(f"   调用次数: {data['count']}")
            logger.info(f"   平均耗时: {data['average']:.2f}ms")
            logger.info(f"   最大耗时: {data['max']:.2f}ms")
            logger.info(f"   最小耗时: {data['min']:.2f}ms")
            logger.info(f"   总耗时: {data['total']:.2f}ms")
            
            # 性能警告
            if data['average'] > 1000:
                logger.warning(f"   ⚠️ 警告: 平均耗时超过1秒！")
            elif data['average'] > 500:
                logger.warning(f"   ⚠️ 注意: 平均耗时较长")
    
    def clear_stats(self):
        """清空统计数据"""
        with self.lock:
            self.timers.clear()
            self.counters.clear()

# 全局性能监控实例
performance_monitor = PerformanceMonitor()

# 便捷装饰器
def monitor_performance(name):
    """性能监控装饰器"""
    return performance_monitor.timer(name)

# 上下文管理器
class PerformanceTimer:
    """性能计时上下文管理器"""
    
    def __init__(self, name):
        self.name = name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (time.time() - self.start_time) * 1000
        performance_monitor.record_time(self.name, duration)
        if duration > 100:
            logger.debug(f"⏱️ {self.name}: {duration:.2f}ms") 