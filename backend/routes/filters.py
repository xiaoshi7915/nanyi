#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
筛选相关路由
处理筛选相关的API请求
"""

from flask import Blueprint
from backend.controllers.product_controller import ProductController
from backend.utils.logger import log_access
from backend.services.cache_service import cached
from backend.utils.decorators import handle_errors
from backend.utils.response import APIResponse

# 创建蓝图
filters_bp = Blueprint('filters', __name__, url_prefix='/api')

# 创建控制器实例
product_controller = ProductController()


@filters_bp.route('/filters')
@log_access
# @cached(ttl=600, key_prefix='api_filters')  # 暂时禁用缓存，避免tuple序列化问题
@handle_errors
def get_filters():
    """获取筛选选项"""
    # 调用控制器处理业务逻辑
    result = product_controller.get_filter_options()
    
    # 使用APIResponse统一响应格式
    return APIResponse.success(
        data=result,
        message='查询成功'
    )
