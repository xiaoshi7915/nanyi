#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
前端API路由
"""

from flask import Blueprint, jsonify, send_file, request, abort
from backend.services import ImageService, ProductService
from backend.utils.decorators import handle_errors
import os

# 创建蓝图
api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/images')
@handle_errors
def get_images():
    """获取所有图片信息"""
    image_service = ImageService()
    images = image_service.get_all_images()
    
    # 按品牌分组
    brands = {}
    for img in images:
        brand_name = img['brand_name']
        if brand_name not in brands:
            brands[brand_name] = {
                'name': brand_name,
                'images': [],
                'year': 2024,  # 默认年份
                'material': '棉麻',  # 默认材质
                'theme_series': '经典系列',  # 默认主题
                'print_size': '循环印花料',  # 默认印制尺寸
                'inspiration_origin': f'{brand_name}的设计灵感来源于传统文化与现代美学的融合。'
            }
        brands[brand_name]['images'].append(img)
    
    # 转换为列表格式
    brand_list = []
    for brand_name, brand_data in brands.items():
        brand_list.append({
            **brand_data,
            'imageCount': len(brand_data['images'])
        })
    
    return jsonify({
        'success': True,
        'images': images,
        'brands': brand_list,
        'total': len(images)
    })

@api_bp.route('/filters')
@handle_errors
def get_filters():
    """获取筛选选项"""
    image_service = ImageService()
    filter_data = image_service.get_filter_options()
    
    return jsonify({
        'success': True,
        **filter_data
    })

@api_bp.route('/brand/<brand_name>')
@handle_errors
def get_brand_detail(brand_name):
    """获取品牌详细信息"""
    # 获取品牌信息
    product = ProductService.get_product_by_brand_name(brand_name)
    if not product:
        return jsonify({
            'success': False,
            'error': '品牌不存在'
        }), 404
    
    # 获取该品牌的所有图片
    image_service = ImageService()
    brand_images = image_service.get_brand_images(brand_name)
    
    return jsonify({
        'success': True,
        'brand_info': product.to_dict(),
        'images': brand_images
    })

@api_bp.route('/products')
@handle_errors
def get_products():
    """获取产品列表（用于管理界面）"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '')
    
    filters = {}
    if request.args.get('theme'):
        filters['theme'] = request.args.get('theme')
    if request.args.get('year'):
        filters['year'] = int(request.args.get('year'))
    if request.args.get('material'):
        filters['material'] = request.args.get('material')
    
    products = ProductService.get_all_products(
        page=page, per_page=per_page, search=search, filters=filters
    )
    
    if products is None:
        return jsonify({
            'success': False,
            'error': '获取产品列表失败'
        }), 500
    
    return jsonify({
        'success': True,
        'products': [product.to_dict() for product in products.items],
        'pagination': {
            'page': products.page,
            'pages': products.pages,
            'per_page': products.per_page,
            'total': products.total,
            'has_next': products.has_next,
            'has_prev': products.has_prev
        }
    })

@api_bp.route('/statistics')
@handle_errors
def get_statistics():
    """获取统计信息"""
    stats = ProductService.get_statistics()
    
    return jsonify({
        'success': True,
        'statistics': stats
    })

# 文件服务路由
@api_bp.route('/view/<path:filepath>')
@handle_errors
def view_image(filepath):
    """查看图片"""
    from config.config import Config
    
    # 构建完整路径
    full_path = os.path.join(Config.UPLOAD_FOLDER, filepath)
    
    # 检查文件是否存在
    if not os.path.exists(full_path):
        abort(404)
    
    # 检查文件是否在允许的目录内（安全检查）
    if not os.path.abspath(full_path).startswith(os.path.abspath(Config.UPLOAD_FOLDER)):
        abort(403)
    
    return send_file(full_path)

@api_bp.route('/download/<path:filepath>')
@handle_errors
def download_image(filepath):
    """下载图片"""
    from config.config import Config
    
    # 构建完整路径
    full_path = os.path.join(Config.UPLOAD_FOLDER, filepath)
    
    # 检查文件是否存在
    if not os.path.exists(full_path):
        abort(404)
    
    # 检查文件是否在允许的目录内（安全检查）
    if not os.path.abspath(full_path).startswith(os.path.abspath(Config.UPLOAD_FOLDER)):
        abort(403)
    
    return send_file(full_path, as_attachment=True)

@api_bp.route('/health')
def health_check():
    """健康检查接口"""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'message': 'API service is running'
    })

# 错误处理
@api_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': '资源不存在'
    }), 404

@api_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': '服务器内部错误'
    }), 500 