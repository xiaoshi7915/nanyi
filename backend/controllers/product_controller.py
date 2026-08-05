#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
产品控制器
处理产品相关的业务逻辑
"""

import re
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
        获取筛选选项 - 优化版本：使用数据库聚合查询 + 缓存
        
        Returns:
            dict: 筛选选项数据
        """
        # 使用缓存键（统一命名空间）
        cache_key = "product:filter:options"
        
        # 尝试从缓存获取
        try:
            from backend.services.cache_service import cache_service
            cached_result = cache_service.get(cache_key)
            if cached_result:
                logger.debug("筛选选项从缓存获取")
                return cached_result
        except Exception as e:
            logger.warning(f"获取缓存失败: {e}")
        
        try:
            # 使用数据库聚合查询替代Python循环统计，大幅提升性能
            from backend.models import db
            
            # 年份统计 - 使用数据库GROUP BY
            year_stats = db.session.query(
                Product.year,
                db.func.count(Product.id).label('count')
            ).filter(Product.year.isnot(None)).group_by(Product.year).order_by(Product.year.desc()).all()
            years = {str(year): count for year, count in year_stats}
            
            # 主题系列统计 - 使用数据库GROUP BY
            theme_stats = db.session.query(
                Product.theme_series,
                db.func.count(Product.id).label('count')
            ).filter(Product.theme_series.isnot(None)).group_by(Product.theme_series).all()
            theme_series = {theme: count for theme, count in theme_stats}
            
            # 印制尺寸统计 - 使用数据库GROUP BY
            print_size_stats = db.session.query(
                Product.print_size,
                db.func.count(Product.id).label('count')
            ).filter(Product.print_size.isnot(None)).group_by(Product.print_size).all()
            print_sizes = {size: count for size, count in print_size_stats}
            
            # 材质统计 - 由于材质可能包含/分隔符，需要特殊处理
            # 先获取所有材质，然后在应用层处理分隔符
            material_stats = db.session.query(
                Product.material,
                db.func.count(Product.id).label('count')
            ).filter(Product.material.isnot(None)).group_by(Product.material).all()
            
            # 处理材质分隔符（支持/分隔的材质）
            materials = {}
            for material, count in material_stats:
                if material:
                    # 按/分隔符拆分材质，每个拆分后的材质都算作一种分类
                    material_list = [m.strip() for m in material.split('/') if m.strip()]
                    for m in material_list:
                        materials[m] = materials.get(m, 0) + count
            
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
            
            result = {
                'success': True,
                'filters': filter_data,
                **filter_data
            }
            
            # 缓存结果（1小时，筛选选项变化不频繁）
            try:
                from backend.services.cache_service import cache_service
                cache_service.set(cache_key, result, ttl=3600)
                logger.debug("筛选选项已缓存")
            except Exception as e:
                logger.warning(f"设置缓存失败: {e}")
            
            return result
            
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
    
    def _resolve_image_type(self, img: Dict) -> str:
        """解析图片类型（与前端 getCategorizedImages / try_on 逻辑一致）。"""
        if img.get('image_type'):
            return img['image_type']
        filename = img.get('filename') or ''
        if '-概念图-' in filename or '概念图' in filename:
            return '概念图'
        if '-设计图-' in filename or '设计图' in filename:
            return '设计图'
        if '-成衣图-' in filename or '成衣图' in filename:
            return '成衣图'
        if '-布料图-' in filename or '布料图' in filename:
            return '布料图'
        if '-买家秀图-' in filename or '买家秀' in filename:
            return '买家秀图'
        if '-模特图-' in filename or '模特图' in filename:
            return '模特图'
        return '其他'

    def _extract_image_color(self, img: Dict) -> str:
        """从图片元数据或文件名括号中提取花色。"""
        if img.get('color'):
            return str(img['color']).strip()
        for field in ('filename', 'relative_path', 'brand_name'):
            text = str(img.get(field) or '')
            match = re.search(r'\(([^)]+)\)', text)
            if match:
                return match.group(1).strip()
        return '默认色'

    def _image_sort_key(self, img: Dict) -> int:
        """按文件名编号排序，便于分享卡片稳定选图。"""
        filename = str(img.get('filename') or '')
        match = re.search(r'-(\d+)\.', filename)
        return int(match.group(1)) if match else 0

    def _pick_share_images_by_type(
        self,
        images: List[Dict],
        img_type: str,
        limit: Optional[int] = None,
        per_color_limit: Optional[int] = None,
    ) -> List[Dict]:
        """按类型选图：支持全量、总量上限、按花色各取上限。"""
        matched = [img for img in images if self._resolve_image_type(img) == img_type]
        matched.sort(key=self._image_sort_key)

        if per_color_limit is not None:
            by_color: Dict[str, List[Dict]] = {}
            for img in matched:
                color = self._extract_image_color(img)
                by_color.setdefault(color, []).append(img)
            picked: List[Dict] = []
            for color in sorted(by_color.keys()):
                picked.extend(by_color[color][:per_color_limit])
            return picked

        if limit is not None:
            return matched[:limit]
        return matched

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
            
            # 分享卡片选图：概念/设计全取；布料/模特按花色各最多2张；成衣/买家秀各最多2张
            images = brand_detail.get('images', [])
            share_card_order = ['概念图', '设计图', '布料图', '成衣图', '买家秀图', '模特图']

            def append_card_image(img: Dict, img_type: str) -> None:
                img_url = ''
                if img.get('url'):
                    img_url = img['url']
                elif img.get('relative_path'):
                    img_url = f"/static/images/{img['relative_path']}"
                else:
                    img_url = f"/static/images/{img.get('filename', 'placeholder.jpg')}"
                card_data['images'].append({
                    'image_type': img_type,
                    'url': img_url,
                    'relative_path': img.get('relative_path'),
                    'filename': img.get('filename')
                })

            for img_type in share_card_order:
                if img_type in ('概念图', '设计图'):
                    selected = self._pick_share_images_by_type(images, img_type)
                elif img_type in ('布料图', '模特图'):
                    selected = self._pick_share_images_by_type(images, img_type, per_color_limit=2)
                else:
                    selected = self._pick_share_images_by_type(images, img_type, limit=2)
                for img in selected:
                    append_card_image(img, img_type)
            
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
