#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
产品处理服务
"""

from backend.models import db, init_models
from datetime import datetime

# 初始化模型
Product, Admin = init_models()

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