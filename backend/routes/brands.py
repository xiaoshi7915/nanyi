#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
品牌相关路由
处理品牌相关的API请求
"""

from flask import Blueprint, request
from backend.controllers.brand_controller import BrandController
from backend.utils.logger import log_access
from backend.services.cache_service import cached
from backend.utils.decorators import handle_errors
from backend.utils.response import APIResponse
from backend.utils.client_ip import get_trusted_client_ip
from backend.utils.rate_limit import rate_limit

# 创建蓝图
brands_bp = Blueprint('brands', __name__, url_prefix='/api')

# 创建控制器实例
brand_controller = BrandController()


@brands_bp.route('/brand/<path:brand_name>')
@log_access
@handle_errors
def get_brand_detail(brand_name):
    """获取品牌详细信息"""
    # 调用控制器处理业务逻辑
    result = brand_controller.get_brand_detail(brand_name)
    
    if result is None:
        from urllib.parse import unquote
        decoded_brand_name = unquote(brand_name)
        base_brand_name = decoded_brand_name.split('(')[0] if '(' in decoded_brand_name else decoded_brand_name
        
        return APIResponse.not_found(
            message=f'品牌不存在: {decoded_brand_name}',
            resource_type='brand',
            resource_id=decoded_brand_name,
            details={
                'requested_brand': decoded_brand_name,
                'base_brand': base_brand_name
            }
        )
    
    # 使用APIResponse统一响应格式
    return APIResponse.success(
        data=result,
        message='查询成功'
    )


@brands_bp.route('/like/card/<path:brand_name>', methods=['POST'])
@rate_limit(max_requests=40, per_seconds=60, scope='like_toggle')
@handle_errors
def like_brand_card(brand_name):
    """切换布料卡片点赞状态（点赞/取消点赞）"""
    client_ip = get_trusted_client_ip()
    user_agent = request.environ.get('HTTP_USER_AGENT', '')
    
    # 创建唯一标识（使用基础品牌名）
    import hashlib
    import urllib.parse
    decoded_brand_name = urllib.parse.unquote(brand_name, encoding='utf-8')
    base_brand_name = decoded_brand_name.split('(')[0] if '(' in decoded_brand_name else decoded_brand_name
    unique_id = hashlib.md5(f"{client_ip}_{user_agent}_{base_brand_name}".encode()).hexdigest()
    
    # 调用控制器处理业务逻辑
    result = brand_controller.toggle_like(brand_name, unique_id, client_ip, user_agent)
    
    # 使用APIResponse统一响应格式
    if result.get('success'):
        return APIResponse.success(
            data={
                'liked': result.get('liked'),
                'like_count': result.get('like_count')
            },
            message=result.get('message', '操作成功')
        )
    else:
        return APIResponse.error(
            message=result.get('message', '操作失败'),
            status_code=500
        )


@brands_bp.route('/like/card/<path:brand_name>', methods=['GET'])
@rate_limit(max_requests=120, per_seconds=60, scope='like_status')
@handle_errors  
def get_brand_like_count(brand_name):
    """获取布料卡片点赞数"""
    client_ip = get_trusted_client_ip()
    user_agent = request.environ.get('HTTP_USER_AGENT', '')
    
    # 创建唯一标识（使用基础品牌名）
    import hashlib
    import urllib.parse
    decoded_brand_name = urllib.parse.unquote(brand_name, encoding='utf-8')
    base_brand_name = decoded_brand_name.split('(')[0] if '(' in decoded_brand_name else decoded_brand_name
    unique_id = hashlib.md5(f"{client_ip}_{user_agent}_{base_brand_name}".encode()).hexdigest()
    
    # 调用控制器处理业务逻辑
    result = brand_controller.get_like_status(brand_name, unique_id)
    
    # 使用APIResponse统一响应格式
    return APIResponse.success(
        data={
            'liked': result.get('liked'),
            'like_count': result.get('like_count')
        },
        message='查询成功'
    )
