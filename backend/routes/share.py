#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分享卡片路由
处理分享卡片相关的API请求
"""

from flask import Blueprint, request
from backend.controllers.product_controller import ProductController
from backend.utils.logger import log_access
from backend.services.cache_service import cached
from backend.utils.decorators import handle_errors
from backend.utils.response import APIResponse

# 创建蓝图
share_bp = Blueprint('share', __name__, url_prefix='/api')

# 创建控制器实例
product_controller = ProductController()


@share_bp.route('/share/card/<path:brand_name>')
@log_access
@cached(ttl=1800, key_prefix='share_card')
@handle_errors
def generate_share_card(brand_name):
    """生成分享卡片数据 - 性能优化版"""
    # 生成前端主机地址
    frontend_host = request.host.replace(':5432', ':8500')  # 将后端端口替换为前端端口
    
    # 获取请求协议（在路由层获取，避免在控制器中使用request）
    request_protocol = 'https' if (request.is_secure or 
                                  request.headers.get('X-Forwarded-Proto') == 'https' or
                                  request.headers.get('X-Forwarded-Ssl') == 'on') else 'http'
    
    # 调用控制器处理业务逻辑，传递协议信息
    result = product_controller.generate_share_card(brand_name, frontend_host, request_protocol)
    
    # 使用APIResponse统一响应格式
    if result.get('success'):
        # 为了兼容前端代码，直接返回card_data在data字段中
        card_data = result.get('card_data', {})
        # 添加card_url到card_data中
        if result.get('card_url'):
            card_data['card_url'] = result.get('card_url')
        return APIResponse.success(
            data=card_data,
            message='生成成功'
        )
    else:
        return APIResponse.not_found(
            message=result.get('error', '生成失败'),
            resource_type='share_card',
            resource_id=brand_name
        )
