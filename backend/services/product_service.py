#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
产品处理服务
"""

from backend.models import db, init_models
from backend.services.base_service import BaseService
from backend.exceptions import DatabaseError, ServiceError
from datetime import datetime
from urllib.parse import unquote

# 初始化模型
Product, Admin, AccessLog = init_models()

class ProductService(BaseService):
    """产品处理服务类"""
    
    def __init__(self):
        """初始化产品服务"""
        super().__init__(service_name='ProductService')
    
    def get_all_products(self, page=1, per_page=20, search=None, filters=None):
        """获取所有产品（支持分页和筛选）"""
        try:
            if not Product:
                self.handle_service_error("Product模型未初始化")
                
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
            self.handle_database_error("query", e)
    
    def get_product_by_id(self, product_id):
        """根据ID获取产品"""
        try:
            return Product.query.get(product_id)
        except Exception as e:
            self.handle_database_error("query", e)
    
    def get_product_by_brand_name(self, brand_name):
        """根据品牌名获取产品"""
        try:
            return Product.query.filter_by(brand_name=brand_name).first()
        except Exception as e:
            self.handle_database_error("query", e)
    
    def get_brand_detail(self, brand_name):
        """获取品牌详细信息 - 优化版本，移除全表扫描，使用基础服务缓存"""
        try:
            # 使用基础服务的缓存方法
            cache_key = f"brand_detail_{brand_name}"
            cached_result = self.get_cache(cache_key)
            if cached_result:
                self.log_debug(f"从缓存获取品牌详情: {brand_name}")
                return cached_result
            
            from urllib.parse import unquote
            
            # URL解码品牌名
            decoded_brand_name = unquote(brand_name)
            self.log_debug(f"正在查询品牌: {brand_name} -> 解码后: {decoded_brand_name}")
            
            # 保存原始请求的品牌名（可能包含颜色信息）
            requested_brand_name = decoded_brand_name
            
            # 优化的三级查询策略（移除全表扫描）
            product = None
            
            # 第一级：精确匹配
            product = Product.query.filter_by(brand_name=decoded_brand_name).first()
            
            if not product:
                # 第二级：基础品牌名匹配（去除括号内容）
                base_brand = decoded_brand_name.split('(')[0].strip() if '(' in decoded_brand_name else decoded_brand_name
                self.log_debug(f"精确匹配失败，尝试基础品牌名匹配: {base_brand}")
                product = Product.query.filter_by(brand_name=base_brand).first()
            
            if not product:
                # 第三级：特殊字符匹配（保留您要求的逻辑）
                clean_brand = decoded_brand_name.split('(')[0] if '(' in decoded_brand_name else decoded_brand_name
                clean_brand = clean_brand.strip().replace(' ', '').replace('-', '').replace('_', '')
                self.log_debug(f"基础匹配失败，尝试特殊字符匹配: {clean_brand}")
                
                # 使用有限的模糊查询而不是全表扫描
                potential_matches = Product.query.filter(
                    db.or_(
                        Product.brand_name.like(f'{clean_brand}%'),
                        Product.brand_name.like(f'%{clean_brand}')
                    )
                ).limit(10).all()  # 限制结果数量，避免全表扫描
                
                for p in potential_matches:
                    clean_p_name = p.brand_name.split('(')[0] if '(' in p.brand_name else p.brand_name
                    clean_p_name = clean_p_name.replace(' ', '').replace('-', '').replace('_', '')
                    if clean_brand == clean_p_name or clean_brand in clean_p_name or clean_p_name in clean_brand:
                        product = p
                        self.log_debug(f"找到匹配品牌: {p.brand_name} (通过特殊字符匹配)")
                        break
            
            if not product:
                self.log_warning(f"所有匹配方式都失败，未找到品牌: {decoded_brand_name}")
                # 缓存空结果，避免重复查询
                self.set_cache(cache_key, None, ttl=60)  # 空结果缓存1分钟
                return None
            
            self.log_debug(f"找到匹配的品牌: {product.brand_name}")
            
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
            
            # 获取图片数据 - 统一使用本地图片服务
            self.log_debug("使用本地图片服务")
            try:
                from backend.services.image_service import ImageService
                image_service = ImageService()
                
                # 优化：使用缓存的图片列表，避免重复扫描
                # 使用请求的品牌名获取图片（可能包含颜色信息）
                brand_images = image_service.get_brand_images(requested_brand_name)
                
                # 如果使用完整品牌名没找到图片，尝试使用基础品牌名
                if not brand_images and requested_brand_name != product.brand_name:
                    self.log_debug(f"使用完整品牌名未找到图片，尝试基础品牌名: {product.brand_name}")
                    brand_images = image_service.get_brand_images(product.brand_name)
                
                brand_info['images'] = brand_images
                brand_info['imageCount'] = len(brand_images)
                self.log_debug(f"本地图片服务获取到 {len(brand_images)} 张图片")
                
            except Exception as e:
                self.log_error("获取本地图片失败", error=e)
                brand_info['images'] = []
                brand_info['imageCount'] = 0
            
            # 缓存结果（30分钟，图片很少变化）
            self.set_cache(cache_key, brand_info, ttl=1800)
            self.log_debug(f"品牌详情已缓存: {brand_name}")
            
            return brand_info
            
        except Exception as e:
            self.log_error("获取品牌详情失败", error=e, brand_name=brand_name)
            return None
    
    def create_product(self, data):
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
            self.handle_database_error("insert", e)
    
    def update_product(self, product_id, data):
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
            self.handle_database_error("update", e)
    
    def delete_product(self, product_id):
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
            self.handle_database_error("delete", e)
    
    def get_filter_options(self):
        """获取筛选选项"""
        try:
            if not Product:
                self.log_error("Product模型未初始化")
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
            self.log_error("获取筛选选项失败", error=e)
            return {
                'themes': [],
                'years': [],
                'materials': [],
                'print_sizes': []
            }
    
    def get_statistics(self):
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
            self.log_error("获取统计信息失败", error=e)
            return {}
    
    def bulk_update_featured(self, product_ids, is_featured):
        """批量更新推荐状态"""
        try:
            Product.query.filter(Product.id.in_(product_ids)).update(
                {Product.is_featured: is_featured}, synchronize_session=False
            )
            db.session.commit()
            return True, None
            
        except Exception as e:
            db.session.rollback()
            self.handle_database_error("update", e) 