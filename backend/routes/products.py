#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
产品管理路由
处理产品管理相关的API请求
"""

from flask import Blueprint, request
from backend.controllers.product_controller import ProductController
from backend.utils.decorators import handle_errors
from backend.utils.response import APIResponse
from backend.utils.validators import validate_pagination, validate_search, validate_filters
from backend.exceptions import ValidationError

# 创建蓝图
products_bp = Blueprint('products', __name__, url_prefix='/api')

# 创建控制器实例
product_controller = ProductController()


@products_bp.route('/products')
@handle_errors
def get_products():
    """获取产品列表（用于管理界面）"""
    # 使用validators模块统一参数验证
    try:
        page, per_page = validate_pagination(max_per_page=100)
        search = validate_search(min_length=0, max_length=100)  # 允许空搜索
        filters = validate_filters(allowed_filters=['theme', 'year', 'material', 'state'])
    except ValidationError as e:
        return APIResponse.validation_error(
            message=str(e),
            field=e.details.get('field'),
            value=e.details.get('value')
        )
    
    # 调用控制器处理业务逻辑
    result = product_controller.get_products(
        page=page,
        per_page=per_page,
        search=search,
        filters=filters
    )
    
    # 使用APIResponse统一响应格式
    if result.get('success'):
        return APIResponse.success(
            data=result,
            message='查询成功'
        )
    else:
        return APIResponse.error(
            message=result.get('error', '查询失败'),
            status_code=500
        )


@products_bp.route('/statistics')
@handle_errors
def get_statistics():
    """获取统计信息"""
    # 调用控制器处理业务逻辑
    result = product_controller.get_statistics()
    
    # 使用APIResponse统一响应格式
    return APIResponse.success(
        data=result.get('statistics', {}),
        message='查询成功'
    )
