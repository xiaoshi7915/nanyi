#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用API路由
包含健康检查、缓存管理等通用功能
"""

from flask import Blueprint, request
from backend.utils.decorators import handle_errors
from backend.services.cache_service import cache_service
from backend.utils.response import APIResponse
from backend.utils.validators import validate_cache_clear_pattern
from backend.utils.admin_auth import require_admin_api_token

# 创建蓝图 - 添加API版本控制
# 注意：为了向后兼容，同时支持 /api 和 /api/v1
api_bp_v1 = Blueprint('api_v1', __name__, url_prefix='/api/v1')
api_bp = Blueprint('api', __name__, url_prefix='/api')  # 保持向后兼容


@api_bp.route('/health')
def health_check():
    """健康检查接口"""
    return APIResponse.success(
        data={'status': 'healthy'},
        message='API service is running'
    )


@api_bp.route('/cache/stats')
@require_admin_api_token
@handle_errors
def get_cache_stats():
    """获取缓存统计信息"""
    stats = cache_service.stats()
    return APIResponse.success(
        data={'cache_stats': stats},
        message='查询成功'
    )


@api_bp.route('/cache/clear', methods=['POST'])
@require_admin_api_token
@handle_errors
def clear_cache():
    """清理缓存"""
    data = request.get_json() or {}
    pattern = validate_cache_clear_pattern(data.get('pattern', '.*'))

    cache_service.clear_pattern(pattern)
    
    return APIResponse.success(
        message=f'缓存已清理: {pattern}',
        pattern=pattern
    )


@api_bp.route('/logs/access/stats')
@require_admin_api_token
@handle_errors
def get_access_log_stats():
    """获取访问日志统计"""
    try:
        from backend.models.access_log import AccessLog
        
        days = request.args.get('days', 7, type=int)
        
        # 获取访问统计
        stats = AccessLog.get_access_stats(days)
        top_ips = AccessLog.get_top_ips(10, days)
        popular_paths = AccessLog.get_popular_paths(10, days)
        
        return APIResponse.success(
            data={
                'daily_stats': stats,
                'top_ips': top_ips,
                'popular_paths': popular_paths,
                'period_days': days
            },
            message='查询成功'
        )
        
    except Exception as e:
        return APIResponse.server_error(
            message=f'获取访问统计失败: {str(e)}'
        )


# 错误处理
@api_bp.errorhandler(404)
def not_found(error):
    return APIResponse.not_found(message='资源不存在')


@api_bp.errorhandler(500)
def internal_error(error):
    return APIResponse.server_error(message='服务器内部错误')
