#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
产品控制器
处理产品相关的业务逻辑
"""

from typing import Dict, List, Optional
from flask import request
from backend.services.product_service import ProductService
from backend.models import db, init_models
from backend.models.product import Product
from backend.utils.logger import logger

# 初始化模型
Product, Admin, AccessLog = init_models()


class ProductController:
    """产品控制器类"""
    
    def __init__(self):
        """初始化产品控制器"""
        self.product_service = ProductService()
    
    def get_products(
        self,
        page: int = 1,
        per_page: int = 20,
        search: str = '',
        filters: Dict = None
    ) -> Dict:
        """
        获取产品列表（用于管理界面）
        
        Args:
            page: 页码
            per_page: 每页数量
            search: 搜索关键词
            filters: 筛选条件
        
        Returns:
            dict: 产品列表和分页信息
        """
        products = self.product_service.get_all_products(
            page=page, per_page=per_page, search=search, filters=filters or {}
        )
        
        if products is None:
            return {
                'success': False,
                'error': '获取产品列表失败'
            }
        
        return {
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
        }
    
    def get_statistics(self) -> Dict:
        """
        获取统计信息
        
        Returns:
            dict: 统计信息
        """
        stats = self.product_service.get_statistics()
        
        return {
            'success': True,
            'statistics': stats
        }
    
    def get_filter_options(self) -> Dict:
        """
        获取筛选选项
        
        Returns:
            dict: 筛选选项数据
        """
        try:
            # 从数据库获取所有产品信息
            products = Product.query.all()
            logger.debug(f"筛选API: 查询到 {len(products)} 个产品")
            
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
            
            logger.debug(f"筛选API: 返回真实数据 - 年份:{len(years)}, 材质:{len(materials)}, 主题:{len(theme_series)}")
            
            return {
                'success': True,
                'filters': filter_data,
                **filter_data
            }
            
        except Exception as e:
            logger.error(f"获取筛选选项错误: {e}", exc_info=True)
            # 如果数据库查询失败，返回默认选项
            return {
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
            }
    
    def generate_share_card(self, brand_name: str, frontend_host: str, request_protocol: str = 'http') -> Dict:
        """
        生成分享卡片数据
        
        Args:
            brand_name: 品牌名称（URL编码）
            frontend_host: 前端主机地址
        
        Returns:
            dict: 分享卡片数据
        """
        try:
            import urllib.parse
            decoded_brand_name = urllib.parse.unquote(brand_name, encoding='utf-8')
            
            # 提取基础品牌名（去掉颜色部分）
            base_brand_name = decoded_brand_name.split('(')[0] if '(' in decoded_brand_name else decoded_brand_name
            
            # 获取品牌详情（已优化，带5分钟缓存）
            brand_detail = self.product_service.get_brand_detail(decoded_brand_name)
            if not brand_detail:
                return {
                    'success': False,
                    'error': '未找到该品牌信息'
                }
            
            # 构建卡片数据
            card_data = {
                'brand_name': decoded_brand_name,
                'base_brand_name': base_brand_name,
                'year': brand_detail.get('year', 2024),
                'material': brand_detail.get('material', '棉麻'),
                'theme_series': brand_detail.get('theme_series', '经典系列'),
                'print_size': brand_detail.get('print_size', '循环印花料'),
                'inspiration_origin': brand_detail.get('inspiration_origin', f'{decoded_brand_name}的设计灵感来源于传统文化与现代美学的融合。'),
                'images': []
            }
            
            # 优化图片处理：选择必要的图片类型，布料图显示2张，其他类型1张
            images = brand_detail.get('images', [])
            
            # 定义图片类型和数量限制
            image_config = {
                '概念图': 1,
                '设计图': 1, 
                '布料图': 2  # 布料图允许2张
            }
            
            type_image_map = {}
            
            for img in images:
                img_type = img['image_type']
                if img_type in image_config:
                    if img_type not in type_image_map:
                        type_image_map[img_type] = []
                    
                    # 检查当前类型是否还能添加更多图片
                    if len(type_image_map[img_type]) < image_config[img_type]:
                        # 优先使用本地URL，提高加载速度
                        img_url = ''
                        if img.get('url'):
                            img_url = img['url']
                        elif img.get('relative_path'):
                            img_url = f"/static/images/{img['relative_path']}"
                        else:
                            img_url = f"/static/images/{img.get('filename', 'placeholder.jpg')}"
                        
                        type_image_map[img_type].append({
                            'image_type': img['image_type'],
                            'url': img_url,
                            'relative_path': img.get('relative_path'),
                            'filename': img.get('filename')
                        })
            
            # 按指定顺序添加图片
            for img_type in image_config.keys():
                if img_type in type_image_map:
                    card_data['images'].extend(type_image_map[img_type])
            
            # 生成卡片URL - 指向前端服务器（使用请求的协议）
            # 协议信息已从路由层传递过来
            
            # 处理frontend_host，移除端口号（如果有）
            host_without_port = frontend_host.split(':')[0] if ':' in frontend_host else frontend_host
            
            # 构建URL，根据协议决定是否添加端口
            if request_protocol == 'https':
                # HTTPS通常不需要端口（443）
                frontend_url = f"{request_protocol}://{host_without_port}/card.html?brand={urllib.parse.quote(decoded_brand_name)}"
            else:
                # HTTP使用8500端口
                frontend_url = f"{request_protocol}://{host_without_port}:8500/card.html?brand={urllib.parse.quote(decoded_brand_name)}"
            
            card_data['card_url'] = frontend_url
            
            # 获取点赞数（直接从数据库获取最新数据，不使用缓存）
            try:
                from backend.models.brand_like import BrandLike
                # 直接从数据库获取最新点赞数，确保实时性
                like_count = BrandLike.get_like_count(base_brand_name)
                card_data['like_count'] = like_count
            except Exception as e:
                logger.warning(f"获取点赞数失败: {e}")
                card_data['like_count'] = 0
            
            return {
                'success': True,
                'card_data': card_data,
                'card_url': frontend_url
            }
            
        except Exception as e:
            logger.error(f"生成分享卡片失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
