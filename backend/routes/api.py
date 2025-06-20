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
from services.cache_service import cached, cache_service, DatabaseQueryCache
from backend.utils.logger import log_access
from backend.utils.cache_control import smart_cache, cache_control

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
@smart_cache
@handle_errors
def get_images():
    """获取图片信息，支持分页"""
    # 获取分页参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)  # 默认每页12个品牌
    load_all = request.args.get('load_all', 'false').lower() == 'true'
    
    # 限制每页数量，避免过大请求
    per_page = min(per_page, 50)
    
    return _get_images_with_pagination(page, per_page, load_all)

def _get_images_with_pagination(page, per_page, load_all):
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
            print(f"🔍 数据库查询到 {len(products)} 个产品")
            for product in products:
                brand_products[product.brand_name] = product
                # 调试输出新品牌
                if product.brand_name in ['江南春', '有才华']:
                    print(f"🎯 找到目标品牌: {product.brand_name} - {product.year} - {product.theme_series}")
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
    
    # 分页处理
    total_brands = len(brand_list)
    total_images = len(images)
    
    if load_all:
        # 加载所有数据（用于筛选等功能）
        paginated_brands = brand_list
        current_page = 1
        total_pages = 1
        has_next = False
        has_prev = False
    else:
        # 分页加载
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_brands = brand_list[start_idx:end_idx]
        
        total_pages = (total_brands + per_page - 1) // per_page
        has_next = page < total_pages
        has_prev = page > 1
        current_page = page
    
    return jsonify({
        'success': True,
        'images': images if load_all else [],  # 分页时不返回所有图片数据
        'brands': paginated_brands,
        'pagination': {
            'current_page': current_page,
            'per_page': per_page,
            'total_brands': total_brands,
            'total_pages': total_pages,
            'has_next': has_next,
            'has_prev': has_prev
        },
        'total': total_images
    })

@api_bp.route('/filters')
@log_access
@cached(ttl=600, key_prefix='api_filters')  # 10分钟缓存
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
            
            # 材质统计 - 支持/分隔的材质
            if product.material:
                # 按/分隔符拆分材质，每个拆分后的材质都算作一种分类
                material_list = [m.strip() for m in product.material.split('/') if m.strip()]
                for material in material_list:
                    materials[material] = materials.get(material, 0) + 1
            
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
@cached(ttl=900, key_prefix='api_brand')  # 15分钟缓存
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

@api_bp.route('/cache/stats')
@handle_errors
def get_cache_stats():
    """获取缓存统计信息"""
    stats = cache_service.stats()
    return jsonify({
        'success': True,
        'cache_stats': stats
    })

@api_bp.route('/cache/clear', methods=['POST'])
@handle_errors
def clear_cache():
    """清理缓存"""
    data = request.get_json() or {}
    pattern = data.get('pattern', '.*')
    
    cache_service.clear_pattern(pattern)
    
    return jsonify({
        'success': True,
        'message': f'缓存已清理: {pattern}'
    })

@api_bp.route('/logs/access/stats')
@handle_errors
def get_access_log_stats():
    """获取访问日志统计"""
    try:
        from models.access_log import AccessLog
        
        days = request.args.get('days', 7, type=int)
        
        # 获取访问统计
        stats = AccessLog.get_access_stats(days)
        top_ips = AccessLog.get_top_ips(10, days)
        popular_paths = AccessLog.get_popular_paths(10, days)
        
        return jsonify({
            'success': True,
            'stats': {
                'daily_stats': stats,
                'top_ips': top_ips,
                'popular_paths': popular_paths,
                'period_days': days
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取访问统计失败: {str(e)}'
        }), 500

@api_bp.route('/share/card/<path:brand_name>')
@log_access
@handle_errors
def generate_share_card(brand_name):
    """生成布料分享卡片"""
    try:
        # URL解码品牌名
        import urllib.parse
        # Flask路由参数需要进一步解码，处理特殊字符
        try:
            decoded_brand_name = urllib.parse.unquote(brand_name, encoding='utf-8')
        except:
            decoded_brand_name = brand_name
        print(f"🎯 生成卡片请求: 原始={brand_name}, 解码={decoded_brand_name}")
        
        # 提取基础品牌名（去掉颜色部分）
        base_brand_name = decoded_brand_name.split('(')[0] if '(' in decoded_brand_name else decoded_brand_name
        print(f"🏷️ 基础品牌名: {base_brand_name}")
        
        # 获取品牌详情数据
        image_service = ImageService()
        
        # 首先尝试完整品牌名
        images = image_service.get_brand_images(decoded_brand_name)
        matched_brand_name = decoded_brand_name
        
        # 如果没找到，尝试基础品牌名
        if not images:
            images = image_service.get_brand_images(base_brand_name)
            if images:
                matched_brand_name = base_brand_name
        
        # 如果仍然没有找到，尝试模糊匹配
        if not images:
            all_images = image_service.get_all_images()
            available_brands = set()
            for img in all_images:
                available_brands.add(img.get('brand_name', ''))
            print(f"🔍 可用品牌名: {list(available_brands)[:5]}...")
            
            # 尝试模糊匹配，处理多颜色品牌名
            for brand in available_brands:
                brand_base = brand.split('(')[0] if '(' in brand else brand
                
                if (base_brand_name == brand_base or base_brand_name in brand or 
                    brand_base == base_brand_name or brand in decoded_brand_name):
                    print(f"🎯 找到匹配品牌: {brand}")
                    temp_images = image_service.get_brand_images(brand)
                    if temp_images:  # 确保找到了图片
                        images = temp_images
                        matched_brand_name = brand
                        break
        
        print(f"📸 最终匹配品牌: {matched_brand_name}, 找到图片数量: {len(images) if images else 0}")
        
        # 从数据库获取产品信息（优先使用基础品牌名）
        Product = None
        try:
            from models.product import Product
            # 首先尝试基础品牌名
            product = Product.get_by_brand_name(base_brand_name)
            # 如果没找到，尝试完整品牌名
            if not product:
                product = Product.get_by_brand_name(decoded_brand_name)
            # 如果仍然没找到，尝试匹配的品牌名
            if not product and matched_brand_name != decoded_brand_name:
                product = Product.get_by_brand_name(matched_brand_name)
            print(f"🏷️ 数据库产品信息: {product.brand_name if product else '未找到'}")
        except ImportError:
            product = None
        
        # 即使没有找到图片或产品信息，也生成基础卡片
        if not images and not product:
            print(f"⚠️ 未找到品牌 '{decoded_brand_name}' 的详细信息，生成基础卡片")
        
        # 准备卡片数据
        card_data = {
            'brand_name': decoded_brand_name,
            'year': product.year if product else 2024,
            'material': product.material if product else '棉麻',
            'theme_series': product.theme_series if product else '经典系列',
            'print_size': product.print_size if product else '循环印花料',
            'inspiration_origin': product.inspiration_origin if product else f'{decoded_brand_name}的设计灵感来源于传统文化与现代美学的融合。',
            'images': []
        }
        
        # 处理图片数据，每种类型最多取一张
        image_types = ['宣传图', '设计图', '布料图', '成衣图', '模特图', '买家秀图']
        type_image_map = {}
        
        for img in images:
            if img['image_type'] in image_types and img['image_type'] not in type_image_map:
                # 构建图片URL
                img_url = ''
                if img.get('medium_url') and img['medium_url'].startswith('http'):
                    img_url = img['medium_url']
                elif img.get('url') and img['url'].startswith('http'):
                    img_url = img['url']
                elif img.get('relative_path'):
                    img_url = f"/static/images/{img['relative_path']}"
                else:
                    img_url = f"/static/images/{img.get('filename', 'placeholder.jpg')}"
                
                type_image_map[img['image_type']] = {
                    'image_type': img['image_type'],
                    'url': img_url,
                    'medium_url': img.get('medium_url'),
                    'relative_path': img.get('relative_path'),
                    'filename': img.get('filename')
                }
        
        # 按指定顺序添加图片
        for img_type in image_types:
            if img_type in type_image_map:
                card_data['images'].append(type_image_map[img_type])
        
        # 生成卡片URL - 指向前端服务器
        frontend_host = request.host.replace(':5001', ':8500')  # 将后端端口替换为前端端口
        frontend_url = f"http://{frontend_host}/card.html?brand={decoded_brand_name}"
        card_data['card_url'] = frontend_url
        
        # 获取点赞数
        try:
            from models.brand_like import BrandLike
            like_count = BrandLike.get_like_count(base_brand_name)
            card_data['like_count'] = like_count
        except Exception as e:
            print(f"获取点赞数失败: {e}")
            card_data['like_count'] = 0
        
        return jsonify({
            'success': True,
            'card_data': card_data,
            'card_url': frontend_url
        })
        
    except Exception as e:
        print(f"生成分享卡片失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# 错误处理
@api_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': '资源不存在'
    }), 404

@api_bp.route('/like/card/<path:brand_name>', methods=['POST'])
@handle_errors
def like_brand_card(brand_name):
    """点赞布料卡片"""
    try:
        import urllib.parse
        decoded_brand_name = urllib.parse.unquote(brand_name, encoding='utf-8')
        
        # 提取基础品牌名（去掉颜色部分）
        base_brand_name = decoded_brand_name.split('(')[0] if '(' in decoded_brand_name else decoded_brand_name
        
        # 获取客户端IP作为唯一标识
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', ''))
        user_agent = request.environ.get('HTTP_USER_AGENT', '')
        
        # 创建唯一标识（使用基础品牌名）
        import hashlib
        unique_id = hashlib.md5(f"{client_ip}_{user_agent}_{base_brand_name}".encode()).hexdigest()
        
        # 使用数据库存储点赞记录
        try:
            from models.brand_like import BrandLike
            success, result = BrandLike.add_like(base_brand_name, unique_id, client_ip, user_agent)
            
            if not success:
                # 获取当前点赞数
                like_count = BrandLike.get_like_count(base_brand_name)
                return jsonify({
                    'success': False,
                    'message': result,
                    'liked': True,
                    'like_count': like_count
                })
            
            return jsonify({
                'success': True,
                'message': '点赞成功！',
                'liked': True,
                'like_count': result
            })
            
        except Exception as db_error:
            print(f"数据库点赞失败，回退到缓存: {db_error}")
            # 数据库失败时回退到缓存
            cache_key = f"like_{unique_id}"
            cache_count_key = f"like_count_{base_brand_name}"
            
            # 检查是否已经点赞过
            has_liked = cache_service.get(cache_key)
            if has_liked:
                return jsonify({
                    'success': False,
                    'message': '您已经点赞过了',
                    'liked': True,
                    'like_count': cache_service.get(cache_count_key) or 0
                })
            
            # 记录点赞
            cache_service.set(cache_key, True, ttl=86400*30)
            
            # 更新点赞数
            current_count = cache_service.get(cache_count_key) or 0
            new_count = current_count + 1
            cache_service.set(cache_count_key, new_count, ttl=86400*365)
            
            return jsonify({
                'success': True,
                'message': '点赞成功！',
                'liked': True,
                'like_count': new_count
            })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/like/card/<path:brand_name>', methods=['GET'])
@handle_errors  
def get_brand_like_count(brand_name):
    """获取布料卡片点赞数"""
    try:
        import urllib.parse
        decoded_brand_name = urllib.parse.unquote(brand_name, encoding='utf-8')
        
        # 提取基础品牌名（去掉颜色部分）
        base_brand_name = decoded_brand_name.split('(')[0] if '(' in decoded_brand_name else decoded_brand_name
        
        # 获取客户端IP作为唯一标识
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', ''))
        user_agent = request.environ.get('HTTP_USER_AGENT', '')
        
        # 创建唯一标识（使用基础品牌名）
        import hashlib
        unique_id = hashlib.md5(f"{client_ip}_{user_agent}_{base_brand_name}".encode()).hexdigest()
        
        # 使用数据库查询点赞状态
        try:
            from models.brand_like import BrandLike
            has_liked = BrandLike.check_user_liked(base_brand_name, unique_id)
            like_count = BrandLike.get_like_count(base_brand_name)
            
            return jsonify({
                'success': True,
                'liked': has_liked,
                'like_count': like_count
            })
            
        except Exception as db_error:
            print(f"数据库查询失败，回退到缓存: {db_error}")
            # 数据库失败时回退到缓存
            cache_key = f"like_{unique_id}"
            cache_count_key = f"like_count_{base_brand_name}"
            
            has_liked = bool(cache_service.get(cache_key))
            like_count = cache_service.get(cache_count_key) or 0
            
            return jsonify({
                'success': True,
                'liked': has_liked,
                'like_count': like_count
            })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': '服务器内部错误'
    }), 500 