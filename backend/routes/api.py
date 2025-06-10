#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
前端API路由
"""

import os
import time
from functools import wraps
from flask import Blueprint, jsonify, request, send_file, abort, current_app
from services.image_service import ImageService
from services.product_service import ProductService
from backend.utils.logger import log_access

# 简单的内存缓存
_cache = {}
_cache_timestamps = {}
CACHE_DURATION = 300  # 5分钟缓存

def cache_response(duration=CACHE_DURATION):
    """缓存装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{f.__name__}_{request.path}_{request.query_string.decode()}"
            current_time = time.time()
            
            # 检查缓存是否存在且未过期
            if (cache_key in _cache and 
                cache_key in _cache_timestamps and 
                current_time - _cache_timestamps[cache_key] < duration):
                return _cache[cache_key]
            
            # 执行函数并缓存结果
            result = f(*args, **kwargs)
            _cache[cache_key] = result
            _cache_timestamps[cache_key] = current_time
            
            # 清理过期缓存
            expired_keys = [k for k, t in _cache_timestamps.items() 
                          if current_time - t > duration]
            for key in expired_keys:
                _cache.pop(key, None)
                _cache_timestamps.pop(key, None)
            
            return result
        return decorated_function
    return decorator

def handle_errors(f):
    """错误处理装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            print(f"API错误 {f.__name__}: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    return decorated_function

# 创建蓝图
api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/images')
@log_access
@cache_response(duration=180)  # 3分钟缓存
@handle_errors
def get_images():
    """获取所有图片信息"""
    image_service = ImageService()
    images = image_service.get_all_images()
    
    # 从数据库获取产品信息
    Product = None
    try:
        # 确保在应用上下文中导入
        with current_app.app_context():
            from models.product import Product
    except ImportError as e:
        print(f"Product模型导入失败: {e}")
        Product = None
    
    # 按品牌分组，合并同名不同颜色的品牌
    brands = {}
    brand_products = {}  # 存储品牌对应的产品信息
    
    # 获取所有产品信息
    if Product:
        try:
            products = Product.query.all()
            for product in products:
                brand_products[product.brand_name] = product
        except Exception as e:
            print(f"数据库查询错误: {e}")
            products = []
    else:
        products = []
    
    # 首先按基础品牌名分组
    base_brands = {}
    for img in images:
        original_brand_name = img['brand_name']
        
        # 提取基础品牌名（去掉颜色部分）
        base_brand_name = original_brand_name
        if '(' in original_brand_name and ')' in original_brand_name:
            base_brand_name = original_brand_name.split('(')[0]
        
        if base_brand_name not in base_brands:
            base_brands[base_brand_name] = []
        base_brands[base_brand_name].append(img)
    
    # 为每个基础品牌创建合并后的品牌信息
    for base_brand_name, brand_images in base_brands.items():
        # 收集所有颜色
        brand_colors = set()
        for img in brand_images:
            if '(' in img['brand_name'] and ')' in img['brand_name']:
                color = img['brand_name'].split('(')[1].split(')')[0]
                brand_colors.add(color)
        
        # 构建显示的品牌名称
        if brand_colors:
            display_brand_name = f"{base_brand_name}({'/'.join(sorted(brand_colors))})"
        else:
            display_brand_name = base_brand_name
        
        # 从数据库获取产品信息（优先使用完整品牌名，其次使用基础品牌名）
        product_info = None
        for img in brand_images:
            if img['brand_name'] in brand_products:
                product_info = brand_products[img['brand_name']]
                break
        
        if not product_info and base_brand_name in brand_products:
            product_info = brand_products[base_brand_name]
        
        if product_info:
            year = product_info.year
            if not year and product_info.publish_month:
                try:
                    year = int(product_info.publish_month[:4])
                except:
                    year = 2024
            elif not year:
                year = 2024
                
            brands[display_brand_name] = {
                'name': display_brand_name,
                'images': brand_images,
                'year': year,
                'material': product_info.material or '棉麻',
                'theme_series': product_info.theme_series or '经典系列',
                'print_size': product_info.print_size or '循环印花料',
                'inspiration_origin': product_info.inspiration_origin or f'{display_brand_name}的设计灵感来源于传统文化与现代美学的融合。',
                'publish_month': product_info.publish_month or '2024-01'
            }
        else:
            brands[display_brand_name] = {
                'name': display_brand_name,
                'images': brand_images,
                'year': 2024,
                'material': '棉麻',
                'theme_series': '经典系列',
                'print_size': '循环印花料',
                'inspiration_origin': f'{display_brand_name}的设计灵感来源于传统文化与现代美学的融合。',
                'publish_month': '2024-01'
            }
    
    # 转换为列表格式并按发布时间排序
    brand_list = []
    for brand_name, brand_data in brands.items():
        brand_list.append({
            **brand_data,
            'imageCount': len(brand_data['images'])
        })
    
    # 按发布年份和月份排序（最新的在前）
    brand_list.sort(key=lambda x: (
        int(x.get('year', 2024)), 
        x.get('publish_month', '2024-01')
    ), reverse=True)
    
    return jsonify({
        'success': True,
        'images': images,
        'brands': brand_list,
        'total': len(images)
    })

@api_bp.route('/filters')
@log_access
@cache_response(duration=300)  # 5分钟缓存
@handle_errors
def get_filters():
    """获取筛选选项"""
    Product = None
    try:
        # 确保在应用上下文中导入
        with current_app.app_context():
            from models.product import Product
        
        # 从数据库获取所有产品信息
        products = Product.query.all()
        
        # 统计各个属性的数量
        years = {}
        materials = {}
        theme_series = {}
        print_sizes = {}
        
        for product in products:
            # 年份统计
            if product.year:
                year_str = str(product.year)
                years[year_str] = years.get(year_str, 0) + 1
            
            # 材质统计
            if product.material:
                materials[product.material] = materials.get(product.material, 0) + 1
            
            # 主题系列统计
            if product.theme_series:
                theme_series[product.theme_series] = theme_series.get(product.theme_series, 0) + 1
            
            # 印制尺寸统计
            if product.print_size:
                print_sizes[product.print_size] = print_sizes.get(product.print_size, 0) + 1
        
        # 按数量排序并添加"全部"选项
        def sort_and_add_all(data_dict):
            sorted_items = sorted(data_dict.items(), key=lambda x: x[1], reverse=True)
            result = ['全部'] + [item[0] for item in sorted_items]
            return result
        
        filter_data = {
            'years': sort_and_add_all(years),
            'materials': sort_and_add_all(materials),
            'theme_series': sort_and_add_all(theme_series),
            'print_sizes': sort_and_add_all(print_sizes),
            'brand_counts': {
                'years': years,
                'materials': materials,
                'theme_series': theme_series,
                'print_sizes': print_sizes
            }
        }
        
        return jsonify({
            'success': True,
            'filters': filter_data,
            **filter_data
        })
        
    except Exception as e:
        print(f"获取筛选选项错误: {e}")
        # 如果数据库查询失败，返回默认选项
        return jsonify({
            'success': True,
            'filters': {
                'years': ['全部', '2025', '2024', '2023', '2022', '2021', '2020', '2019', '2018', '2017'],
                'materials': ['全部', '棉麻', '真丝', '雪纺'],
                'theme_series': ['全部', '经典系列', '现代系列'],
                'print_sizes': ['全部', '循环印花料', '定位印花料']
            },
            'years': ['全部', '2025', '2024', '2023', '2022', '2021', '2020', '2019', '2018', '2017'],
            'materials': ['全部', '棉麻', '真丝', '雪纺'],
            'theme_series': ['全部', '经典系列', '现代系列'],
            'print_sizes': ['全部', '循环印花料', '定位印花料']
        })

@api_bp.route('/brand/<brand_name>')
@log_access
@cache_response(duration=600)  # 10分钟缓存
@handle_errors
def get_brand_detail(brand_name):
    """获取品牌详细信息"""
    from urllib.parse import unquote
    
    # URL解码品牌名
    brand_name = unquote(brand_name)
    
    # 从品牌名中提取基础品牌名（去掉花色信息）
    base_brand_name = brand_name
    if '(' in brand_name:
        base_brand_name = brand_name.split('(')[0]
    
    # 使用基础品牌名获取品牌信息
    product = ProductService.get_product_by_brand_name(base_brand_name)
    
    # 获取该品牌的所有图片（使用基础品牌名）
    image_service = ImageService()
    brand_images = image_service.get_brand_images(base_brand_name)
    
    if not brand_images:
        return jsonify({
            'success': False,
            'error': '品牌不存在'
        }), 404
    
    # 构建返回数据
    result = {
        'success': True,
        'brand': {
            'name': brand_name,  # 返回原始品牌名（带花色）
            'base_name': base_brand_name,  # 返回基础品牌名
            'images': brand_images,
            'imageCount': len(brand_images)
        }
    }
    
    # 如果有产品信息，添加到结果中
    if product:
        brand_info = product.to_dict()
        result['brand'].update(brand_info)
    
    return jsonify(result)

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