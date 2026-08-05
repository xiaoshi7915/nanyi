#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片控制器
处理图片相关的业务逻辑
"""

from typing import Dict, List, Optional, Tuple
from backend.services.image_service import ImageService
from backend.models import db, init_models
from backend.models.product import Product
from backend.models.brand_like import BrandLike
from backend.utils.logger import logger

# 初始化模型
Product, Admin, AccessLog = init_models()


class ImageController:
    """图片控制器类"""

    # 列表接口封面图优先级（与前端 getBrandCoverImage 一致）
    _COVER_TYPE_PRIORITY = (
        '概念图', '设计图', '成衣图', '布料图', '模特图', '买家秀图', '其他'
    )
    
    def __init__(self):
        """初始化图片控制器"""
        self.image_service = ImageService()

    @staticmethod
    def _is_generated_image_source(image: Dict) -> bool:
        """排除 AI 试穿生成目录图片"""
        if not image:
            return False
        path_parts = [
            str(image.get('relative_path') or ''),
            str(image.get('filename') or ''),
            str(image.get('url') or ''),
        ]
        combined = ' '.join(path_parts).lower()
        return (
            '/generated/' in combined
            or 'images/generated' in combined
            or combined.split('/') == ['generated']
        )

    def _pick_cover_image(self, images: List[Dict]) -> Optional[Dict]:
        """为列表接口选取单张封面图元数据"""
        safe = [img for img in (images or []) if img and not self._is_generated_image_source(img)]
        if not safe:
            return None
        for image_type in self._COVER_TYPE_PRIORITY:
            for img in safe:
                if img.get('image_type') == image_type:
                    return img
        return safe[0]

    def _pick_preview_images(self, images: List[Dict]) -> List[Dict]:
        """列表接口：每个分类最多 1 张预览图，供详情弹窗乐观展示"""
        safe = [img for img in (images or []) if img and not self._is_generated_image_source(img)]
        if not safe:
            return []
        by_type: Dict[str, Dict] = {}
        for img in safe:
            image_type = img.get('image_type') or '其他'
            if image_type not in by_type:
                by_type[image_type] = img
        previews: List[Dict] = []
        for image_type in self._COVER_TYPE_PRIORITY:
            if image_type in by_type:
                previews.append(by_type[image_type])
        for image_type, img in by_type.items():
            if image_type not in self._COVER_TYPE_PRIORITY:
                previews.append(img)
        return previews

    def _compact_brand_for_list(self, brand_data: Dict) -> Dict:
        """列表响应只保留封面图，避免每个品牌携带完整 images 数组"""
        images = brand_data.get('images') or []
        cover = self._pick_cover_image(images)
        previews = self._pick_preview_images(images)
        compact = {k: v for k, v in brand_data.items() if k != 'images'}
        compact['images'] = [cover] if cover else []
        compact['preview_images'] = previews
        compact['imageCount'] = brand_data.get('imageCount', len(images))
        return compact
    
    def get_images_with_pagination(
        self,
        page: int = 1,
        per_page: int = 12,
        load_all: bool = False
    ) -> Dict:
        """
        获取图片信息，支持分页
        
        Args:
            page: 页码（默认1）
            per_page: 每页数量（默认12）
            load_all: 是否加载所有数据（默认False）
        
        Returns:
            dict: 包含图片和品牌信息的字典
        """
        # 获取所有图片
        images = self.image_service.get_all_images()
        
        # 从数据库获取产品信息
        brands = {}
        brand_products = {}  # 存储品牌对应的产品信息
        
        # 获取所有产品信息 - 优化：一次性查询所有产品，避免N+1查询
        try:
            # 使用SQLAlchemy查询，避免循环查询
            products = Product.query.all()
            logger.debug(f"数据库查询到 {len(products)} 个产品")
            
            # 批量构建品牌产品映射
            for product in products:
                brand_products[product.brand_name] = product
                # 同时为可能的基础品牌名（去掉颜色部分）建立映射
                if '(' in product.brand_name:
                    base_name = product.brand_name.split('(')[0]
                    if base_name not in brand_products:
                        brand_products[base_name] = product
        except Exception as e:
            logger.error(f"数据库查询错误: {e}")
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
            # 优化：直接从字典查找，避免循环查询
            product_info = brand_products.get(display_brand_name) or \
                           brand_products.get(base_brand_name) or \
                           brand_products.get(brand_images[0]['brand_name'] if brand_images else None)
            
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
        
        # 批量获取所有品牌的点赞数
        try:
            all_like_counts = BrandLike.get_all_like_counts()
        except Exception as e:
            logger.warning(f"获取点赞数失败: {e}")
            all_like_counts = {}
        
        for brand_name, brand_data in brands.items():
            # 获取基础品牌名用于查询点赞数
            base_brand_name = brand_name.split('(')[0] if '(' in brand_name else brand_name
            like_count = all_like_counts.get(base_brand_name, 0)
            
            brand_list.append({
                **brand_data,
                'imageCount': len(brand_data['images']),
                'like_count': like_count  # 添加点赞数
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
        
        # 列表接口仅返回封面图元数据，详情图由 /api/brand/<name> 按需加载
        compact_brands = [self._compact_brand_for_list(b) for b in paginated_brands]

        return {
            'success': True,
            'images': [],
            'brands': compact_brands,
            'pagination': {
                'current_page': current_page,
                'per_page': per_page,
                'total_brands': total_brands,
                'total_pages': total_pages,
                'has_next': has_next,
                'has_prev': has_prev
            },
            'total': total_images
        }
