#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
产品处理服务
"""

from backend.models import db, init_models
from datetime import datetime
from urllib.parse import unquote

# 初始化模型
Product, Admin, AccessLog = init_models()

class ProductService:
    """产品处理服务类"""
    
    @staticmethod
    def get_all_products(page=1, per_page=20, search=None, filters=None):
        """获取所有产品（支持分页和筛选）"""
        try:
            if not Product:
                print("Product模型未初始化")
                return None
                
            query = Product.query
            
            # 多字段搜索过滤
            if search:
                search_term = f'%{search}%'
                query = query.filter(
                    db.or_(
                        Product.brand_name.like(search_term),
                        Product.title.like(search_term),
                        Product.material.like(search_term),
                        Product.theme_series.like(search_term),
                        Product.inspiration_origin.like(search_term),
                        Product.year.like(search_term),
                        Product.publish_month.like(search_term)
                    )
                )
            
            # 其他筛选条件
            if filters:
                if filters.get('theme'):
                    query = query.filter(Product.theme_series == filters['theme'])
                if filters.get('year'):
                    query = query.filter(Product.year == filters['year'])
                if filters.get('material'):
                    query = query.filter(Product.material == filters['material'])
                if filters.get('state'):
                    query = query.filter(Product.state == filters['state'])
            
            # 排序和分页
            products = query.order_by(Product.updated_at.desc()).paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            return products
            
        except Exception as e:
            print(f"获取产品列表失败: {str(e)}")
            return None
    
    @staticmethod
    def get_product_by_id(product_id):
        """根据ID获取产品"""
        try:
            return Product.query.get(product_id)
        except Exception as e:
            print(f"获取产品失败: {str(e)}")
            return None
    
    @staticmethod
    def get_product_by_brand_name(brand_name):
        """根据品牌名获取产品"""
        try:
            return Product.query.filter_by(brand_name=brand_name).first()
        except Exception as e:
            print(f"获取产品失败: {str(e)}")
            return None
    
    @staticmethod
    def get_brand_detail(brand_name):
        """获取品牌详细信息，包括处理多颜色品牌"""
        try:
            from urllib.parse import unquote
            
            # URL解码品牌名
            decoded_brand_name = unquote(brand_name)
            print(f"正在查询品牌: {brand_name} -> 解码后: {decoded_brand_name}")
            
            # 保存原始请求的品牌名（可能包含颜色信息）
            requested_brand_name = decoded_brand_name
            
            # 首先尝试精确匹配
            product = Product.query.filter_by(brand_name=decoded_brand_name).first()
            
            if not product:
                # 如果没有找到，尝试模糊匹配（处理多颜色情况）
                print(f"精确匹配失败，尝试模糊匹配: {decoded_brand_name}")
                product = Product.query.filter(Product.brand_name.like(f'{decoded_brand_name}%')).first()
            
            if not product:
                # 尝试反向模糊匹配（品牌名可能包含在查询字符串中）
                print(f"正向模糊匹配失败，尝试反向匹配: {decoded_brand_name}")
                product = Product.query.filter(Product.brand_name.like(f'%{decoded_brand_name}%')).first()
            
            if not product:
                # 尝试去除括号和特殊字符后匹配
                clean_brand = decoded_brand_name.split('(')[0] if '(' in decoded_brand_name else decoded_brand_name
                clean_brand = clean_brand.strip().replace(' ', '').replace('-', '').replace('_', '')
                print(f"特殊字符匹配: {clean_brand}")
                products = Product.query.all()
                for p in products:
                    clean_p_name = p.brand_name.split('(')[0] if '(' in p.brand_name else p.brand_name
                    clean_p_name = clean_p_name.replace(' ', '').replace('-', '').replace('_', '')
                    if clean_brand == clean_p_name or clean_brand in clean_p_name or clean_p_name in clean_brand:
                        product = p
                        print(f"找到匹配品牌: {p.brand_name} (通过清理后匹配)")
                        break
            
            if not product:
                print(f"所有匹配方式都失败，未找到品牌: {decoded_brand_name}")
                # 打印数据库中所有品牌名，用于调试
                all_brands = Product.query.with_entities(Product.brand_name).distinct().limit(20).all()
                print(f"数据库中的品牌示例: {[b[0] for b in all_brands]}")
                return None
            
            print(f"找到匹配的品牌: {product.brand_name}")
            
            # 构建品牌详情数据 - 使用请求的品牌名而不是数据库中的品牌名
            brand_info = {
                'id': product.id,
                'name': requested_brand_name,  # 使用用户请求的完整品牌名
                'brand_name': requested_brand_name,  # 使用用户请求的完整品牌名
                'db_brand_name': product.brand_name,  # 保留数据库中的品牌名用于内部查询
                'title': product.title,
                'year': product.year,
                'publish_month': product.publish_month,
                'material': product.material,
                'theme_series': product.theme_series,
                'print_size': product.print_size,
                'inspiration_origin': product.inspiration_origin,
                'created_at': product.created_at.isoformat() if product.created_at else None,
                'updated_at': product.updated_at.isoformat() if product.updated_at else None
            }
            
            # 获取图片数据 - 根据配置选择图片源
            from flask import current_app
            image_source = current_app.config.get('IMAGE_SOURCE', 'oss').lower()
            print(f"🔧 当前图片源配置: {image_source}")
            
            try:
                if image_source == 'local':
                    # 优先使用本地图片服务
                    print("📁 使用本地图片服务")
                    from services.image_service import ImageService
                    image_service = ImageService()
                    # 使用请求的品牌名获取图片（可能包含颜色信息）
                    brand_images = image_service.get_brand_images(requested_brand_name)
                    
                    # 如果使用完整品牌名没找到图片，尝试使用基础品牌名
                    if not brand_images and requested_brand_name != product.brand_name:
                        print(f"使用完整品牌名未找到图片，尝试基础品牌名: {product.brand_name}")
                        brand_images = image_service.get_brand_images(product.brand_name)
                    
                    brand_info['images'] = brand_images
                    brand_info['imageCount'] = len(brand_images)
                    print(f"📁 本地图片服务获取到 {len(brand_images)} 张图片")
                else:
                    # 使用OSS图片服务
                    print("🌐 使用OSS图片服务")
                    from services.oss_image_service import OSSImageService
                    oss_service = OSSImageService()
                    # 使用请求的品牌名获取图片
                    images = oss_service.get_brand_images(requested_brand_name)
                    
                    # 如果使用完整品牌名没找到图片，尝试使用基础品牌名
                    if not images and requested_brand_name != product.brand_name:
                        print(f"使用完整品牌名未找到图片，尝试基础品牌名: {product.brand_name}")
                        images = oss_service.get_brand_images(product.brand_name)
                    
                    brand_info['images'] = images
                    brand_info['imageCount'] = len(images)
                    print(f"🌐 OSS图片服务获取到 {len(images)} 张图片")
                    
            except Exception as e:
                print(f"获取图片失败: {e}")
                # 如果主要图片服务失败，尝试备用服务
                try:
                    if image_source == 'local':
                        # 本地失败，尝试OSS
                        print("📁 本地图片服务失败，尝试OSS服务")
                        from services.oss_image_service import OSSImageService
                        oss_service = OSSImageService()
                        images = oss_service.get_brand_images(requested_brand_name)
                        if not images and requested_brand_name != product.brand_name:
                            images = oss_service.get_brand_images(product.brand_name)
                        brand_info['images'] = images
                        brand_info['imageCount'] = len(images)
                        print(f"🌐 备用OSS服务获取到 {len(images)} 张图片")
                    else:
                        # OSS失败，尝试本地
                        print("🌐 OSS图片服务失败，尝试本地服务")
                        from services.image_service import ImageService
                        image_service = ImageService()
                        brand_images = image_service.get_brand_images(requested_brand_name)
                        if not brand_images and requested_brand_name != product.brand_name:
                            brand_images = image_service.get_brand_images(product.brand_name)
                        brand_info['images'] = brand_images
                        brand_info['imageCount'] = len(brand_images)
                        print(f"📁 备用本地服务获取到 {len(brand_images)} 张图片")
                except Exception as e2:
                    print(f"备用图片服务也失败: {e2}")
                    brand_info['images'] = []
                    brand_info['imageCount'] = 0
            
            # 获取点赞数 - 使用数据库中的品牌名
            try:
                from models.brand_like import BrandLike
                like_count = BrandLike.get_like_count(product.brand_name)
                brand_info['like_count'] = like_count
            except Exception as e:
                print(f"获取点赞数失败: {e}")
                brand_info['like_count'] = 0
            
            return brand_info
            
        except Exception as e:
            print(f"获取品牌详情失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def create_product(data):
        """创建新产品"""
        try:
            product = Product(
                brand_name=data.get('brand_name'),
                title=data.get('title'),
                year=int(data.get('year')) if data.get('year') else None,
                publish_month=data.get('publish_month'),
                material=data.get('material'),
                theme_series=data.get('theme_series'),
                print_size=data.get('print_size'),
                inspiration_origin=data.get('inspiration_origin'),
                price=float(data.get('price')) if data.get('price') else None,
                stock=int(data.get('stock')) if data.get('stock') else 0,
                is_featured=bool(data.get('is_featured', False))
            )
            
            db.session.add(product)
            db.session.commit()
            
            return product, None
            
        except Exception as e:
            db.session.rollback()
            error_msg = f"创建产品失败: {str(e)}"
            print(error_msg)
            return None, error_msg
    
    @staticmethod
    def update_product(product_id, data):
        """更新产品信息"""
        try:
            product = Product.query.get(product_id)
            if not product:
                return None, "产品不存在"
            
            # 更新字段
            if 'brand_name' in data:
                product.brand_name = data['brand_name']
            if 'title' in data:
                product.title = data['title']
            if 'year' in data:
                product.year = int(data['year']) if data['year'] else None
            if 'publish_month' in data:
                product.publish_month = data['publish_month']
            if 'material' in data:
                product.material = data['material']
            if 'theme_series' in data:
                product.theme_series = data['theme_series']
            if 'print_size' in data:
                product.print_size = data['print_size']
            if 'inspiration_origin' in data:
                product.inspiration_origin = data['inspiration_origin']
            if 'price' in data:
                product.price = float(data['price']) if data['price'] else None
            if 'stock' in data:
                product.stock = int(data['stock']) if data['stock'] else 0
            if 'is_featured' in data:
                product.is_featured = bool(data['is_featured'])
            
            product.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            return product, None
            
        except Exception as e:
            db.session.rollback()
            error_msg = f"更新产品失败: {str(e)}"
            print(error_msg)
            return None, error_msg
    
    @staticmethod
    def delete_product(product_id):
        """删除产品"""
        try:
            product = Product.query.get(product_id)
            if not product:
                return False, "产品不存在"
            
            db.session.delete(product)
            db.session.commit()
            
            return True, None
            
        except Exception as e:
            db.session.rollback()
            error_msg = f"删除产品失败: {str(e)}"
            print(error_msg)
            return False, error_msg
    
    @staticmethod
    def get_filter_options():
        """获取筛选选项"""
        try:
            if not Product:
                print("Product模型未初始化")
                return {
                    'themes': [],
                    'years': [],
                    'materials': [],
                    'print_sizes': []
                }
            
            # 获取各种筛选选项
            themes = db.session.query(Product.theme_series).filter(
                Product.theme_series.isnot(None)
            ).distinct().all()
            
            years = db.session.query(Product.year).filter(
                Product.year.isnot(None)
            ).distinct().order_by(Product.year.desc()).all()
            
            materials = db.session.query(Product.material).filter(
                Product.material.isnot(None)
            ).distinct().all()
            
            print_sizes = db.session.query(Product.print_size).filter(
                Product.print_size.isnot(None)
            ).distinct().all()
            
            return {
                'themes': [t[0] for t in themes],
                'years': [y[0] for y in years],
                'materials': [m[0] for m in materials],
                'print_sizes': [p[0] for p in print_sizes]
            }
            
        except Exception as e:
            print(f"获取筛选选项失败: {str(e)}")
            return {
                'themes': [],
                'years': [],
                'materials': [],
                'print_sizes': []
            }
    
    @staticmethod
    def get_statistics():
        """获取统计信息"""
        try:
            total_products = Product.query.count()
            featured_products = Product.query.filter_by(is_featured=True).count()
            active_products = Product.query.filter_by(state='active').count()
            
            # 按年份统计
            year_stats = db.session.query(
                Product.year,
                db.func.count(Product.id).label('count')
            ).filter(Product.year.isnot(None)).group_by(Product.year).all()
            
            # 按主题系列统计
            theme_stats = db.session.query(
                Product.theme_series,
                db.func.count(Product.id).label('count')
            ).filter(Product.theme_series.isnot(None)).group_by(Product.theme_series).all()
            
            return {
                'total_products': total_products,
                'featured_products': featured_products,
                'active_products': active_products,
                'year_stats': {year: count for year, count in year_stats},
                'theme_stats': {theme: count for theme, count in theme_stats}
            }
            
        except Exception as e:
            print(f"获取统计信息失败: {str(e)}")
            return {}
    
    @staticmethod
    def bulk_update_featured(product_ids, is_featured):
        """批量更新推荐状态"""
        try:
            Product.query.filter(Product.id.in_(product_ids)).update(
                {Product.is_featured: is_featured}, synchronize_session=False
            )
            db.session.commit()
            return True, None
            
        except Exception as e:
            db.session.rollback()
            error_msg = f"批量更新失败: {str(e)}"
            print(error_msg)
            return False, error_msg 