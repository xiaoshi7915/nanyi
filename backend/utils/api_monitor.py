#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API响应时间监控中间件
用于记录每个API端点的响应时间和性能指标
"""

import time
import functools
from flask import request, g
from backend.utils.logger import logger
from backend.utils.performance_monitor import performance_monitor

# 慢查询阈值（毫秒）
SLOW_QUERY_THRESHOLD = 1000  # 1秒

def monitor_api_performance():
    """API性能监控装饰器"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 记录开始时间
            start_time = time.time()
            
            # 获取API端点名称
            endpoint = request.endpoint or func.__name__
            method = request.method
            path = request.path
            
            try:
                # 执行函数
                result = func(*args, **kwargs)
                
                # 计算响应时间
                duration_ms = (time.time() - start_time) * 1000
                
                # 记录性能数据
                performance_monitor.record_time(f"api:{method}:{path}", duration_ms)
                
                # 记录慢查询
                if duration_ms > SLOW_QUERY_THRESHOLD:
                    logger.warning(
                        f"🐌 慢查询警告: {method} {path} "
                        f"耗时 {duration_ms:.2f}ms (阈值: {SLOW_QUERY_THRESHOLD}ms)"
                    )
                else:
                    logger.debug(
                        f"⏱️ API响应: {method} {path} "
                        f"耗时 {duration_ms:.2f}ms"
                    )
                
                # 在响应头中添加性能信息（可选）
                if hasattr(result, 'headers'):
                    result.headers['X-Response-Time'] = f"{duration_ms:.2f}ms"
                
                return result
                
            except Exception as e:
                # 即使出错也记录响应时间
                duration_ms = (time.time() - start_time) * 1000
                logger.error(
                    f"❌ API错误: {method} {path} "
                    f"耗时 {duration_ms:.2f}ms, 错误: {str(e)}"
                )
                raise
        
        return wrapper
    return decorator


def init_api_monitoring(app):
    """
    初始化API监控中间件
    
    Args:
        app: Flask应用实例
    """
    @app.before_request
    def before_request():
        """请求前记录开始时间"""
        g.start_time = time.time()
    
    @app.after_request
    def after_request(response):
        """请求后记录响应时间"""
        if hasattr(g, 'start_time'):
            duration_ms = (time.time() - g.start_time) * 1000
            method = request.method
            path = request.path
            
            # 记录性能数据
            performance_monitor.record_time(f"api:{method}:{path}", duration_ms)
            
            # 在响应头中添加性能信息
            response.headers['X-Response-Time'] = f"{duration_ms:.2f}ms"
            
            # 记录慢查询
            if duration_ms > SLOW_QUERY_THRESHOLD:
                logger.warning(
                    f"🐌 慢查询警告: {method} {path} "
                    f"耗时 {duration_ms:.2f}ms (阈值: {SLOW_QUERY_THRESHOLD}ms)"
                )
            elif duration_ms > 500:  # 中等延迟
                logger.info(
                    f"⏱️ API响应: {method} {path} "
                    f"耗时 {duration_ms:.2f}ms"
                )
        
        return response
    
    logger.info("✅ API性能监控已启用")


def get_api_stats():
    """
    获取API性能统计信息
    
    Returns:
        dict: API性能统计
    """
    stats = performance_monitor.get_stats()
    
    # 过滤出API相关的统计
    api_stats = {
        k: v for k, v in stats.items() 
        if k.startswith('api:')
    }
    
    return api_stats


def print_api_stats():
    """打印API性能统计"""
    logger.info("="*50)
    logger.info("📊 API性能统计")
    logger.info("="*50)
    
    api_stats = get_api_stats()
    
    if not api_stats:
        logger.info("暂无API性能数据")
        return
    
    # 按平均耗时排序
    sorted_stats = sorted(api_stats.items(), key=lambda x: x[1]['average'], reverse=True)
    
    for endpoint, data in sorted_stats:
        logger.info(f"\n🔍 {endpoint}:")
        logger.info(f"   调用次数: {data['count']}")
        logger.info(f"   平均耗时: {data['average']:.2f}ms")
        logger.info(f"   最大耗时: {data['max']:.2f}ms")
        logger.info(f"   最小耗时: {data['min']:.2f}ms")
        
        # 性能警告
        if data['average'] > SLOW_QUERY_THRESHOLD:
            logger.warning(f"   ⚠️ 警告: 平均耗时超过{SLOW_QUERY_THRESHOLD}ms！")
        elif data['average'] > 500:
            logger.warning(f"   ⚠️ 注意: 平均耗时较长")
