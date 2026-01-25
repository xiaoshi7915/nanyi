#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片处理服务 - 本地模式优化版
"""

import os
import re
from typing import List, Dict, Optional

from backend.services.base_service import BaseService

class ImageService(BaseService):
    """图片处理服务类 - 专注本地图片处理，性能优化版"""
    
    def __init__(self, images_dir: str = None):
        """初始化图片服务"""
        super().__init__(service_name='ImageService')
        
        if images_dir is None:
            # 获取项目根目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            images_dir = os.path.join(project_root, 'frontend', 'static', 'images')
        
        self.images_dir = images_dir
        self.allowed_extensions = {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'}
        
        self.log_info(f"本地图片服务初始化: {self.images_dir}")
    
    def parse_filename(self, filename: str) -> Dict[str, str]:
        """解析文件名获取品牌信息"""
        name_without_ext = os.path.splitext(filename)[0]
        
        # 匹配格式1: 品牌名-图片类型-编号
        pattern1 = r'^([^-]+)-([^-]+)-(\d+)$'
        match1 = re.match(pattern1, name_without_ext)
        
        if match1:
            return {
                'brand_name': match1.group(1).strip(),
                'image_type': match1.group(2).strip(),
                'number': match1.group(3).strip(),
                'color': None,
                'has_color': False
            }
        
        # 匹配格式2: 品牌名(颜色)-图片类型-编号
        pattern2 = r'^([^(]+)\(([^)]+)\)-([^-]+)-(\d+)$'
        match2 = re.match(pattern2, name_without_ext)
        
        if match2:
            return {
                'brand_name': match2.group(1).strip(),
                'color': match2.group(2).strip(),
                'image_type': match2.group(3).strip(),
                'number': match2.group(4).strip(),
                'has_color': True
            }
        
        return {
            'brand_name': name_without_ext,
            'image_type': '其他',
            'number': '01',
            'color': None,
            'has_color': False
        }
    
    def is_allowed_file(self, filename: str) -> bool:
        """检查文件是否为允许的图片格式"""
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    def get_all_images(self) -> List[Dict]:
        """获取所有图片信息 - 带缓存的本地版本"""
        # 使用基础服务的缓存方法（统一命名空间）
        cache_key = "image:list:all"
        cached_images = self.get_cache(cache_key)
        if cached_images:
            self.log_debug(f"从缓存获取所有图片: {len(cached_images)}张")
            return cached_images
        
        self.log_debug("扫描本地图片目录...")
        images = self._scan_local_images()
        
        # 缓存结果（15分钟）
        self.set_cache(cache_key, images, ttl=900)
        self.log_debug(f"图片数据已缓存: {len(images)}张图片")
        
        return images
    
    def _scan_local_images(self) -> List[Dict]:
        """扫描本地图片文件"""
        images = []
        
        if not os.path.exists(self.images_dir):
            self.log_warning(f"本地图片目录不存在: {self.images_dir}")
            return images
        
        # 定义需要排除的社交图标文件
        social_icons = {
            'taobao.png', 'taobao.jpg', 'taobao.jpeg',
            'xiaohongshu.png', 'xiaohongshu.jpg', 'xiaohongshu.jpeg',
            'weidian.png', 'weidian.jpg', 'weidian.jpeg',
            'wechat.png', 'wechat.jpg', 'wechat.jpeg',
            'logo.png', 'logo.jpg', 'logo.jpeg', 'logo.svg'  # 也排除logo文件
        }
        
        # 扫描根目录下的图片文件
        for filename in os.listdir(self.images_dir):
            if self.is_allowed_file(filename) and filename.lower() not in social_icons:
                filepath = os.path.join(self.images_dir, filename)
                if os.path.isfile(filepath):
                    parsed_info = self.parse_filename(filename)
                    images.append({
                        'filename': filename,
                        'relative_path': filename,
                        'brand_name': parsed_info['brand_name'],
                        'image_type': parsed_info['image_type'],
                        'color': parsed_info['color'],
                        'has_color': parsed_info['has_color'],
                        'size': os.path.getsize(filepath),
                        # 本地图片URL
                        'url': f"/static/images/{filename}",
                        'thumbnail': f"/static/images/{filename}",
                        'original': f"/static/images/{filename}"
                    })
        
        # 扫描子文件夹中的图片
        for item in os.listdir(self.images_dir):
            item_path = os.path.join(self.images_dir, item)
            if os.path.isdir(item_path):
                for filename in os.listdir(item_path):
                    if self.is_allowed_file(filename) and filename.lower() not in social_icons:
                        filepath = os.path.join(item_path, filename)
                        if os.path.isfile(filepath):
                            parsed_info = self.parse_filename(filename)
                            relative_path = f"{item}/{filename}"
                            images.append({
                                'filename': filename,
                                'relative_path': relative_path,
                                'brand_name': parsed_info['brand_name'] or item,
                                'image_type': parsed_info['image_type'],
                                'color': parsed_info['color'],
                                'has_color': parsed_info['has_color'],
                                'size': os.path.getsize(filepath),
                                # 本地图片URL
                                'url': f"/static/images/{relative_path}",
                                'thumbnail': f"/static/images/{relative_path}",
                                'original': f"/static/images/{relative_path}"
                            })
        
        self.log_info(f"本地图片扫描完成: 共{len(images)}张图片")
        return sorted(images, key=lambda x: x['brand_name'] or '')
    
    def get_brand_images(self, brand_name: str) -> List[Dict]:
        """获取指定品牌的所有图片 - 带缓存的本地版本"""
        # 使用基础服务的缓存方法（统一命名空间）
        cache_key = f"image:brand:{brand_name}"
        cached_images = self.get_cache(cache_key)
        if cached_images:
            self.log_debug(f"从缓存获取品牌图片: {brand_name} ({len(cached_images)}张)")
            return cached_images
        
        self.log_debug(f"查找品牌图片: {brand_name}")
        all_images = self.get_all_images()
        
        # 首先尝试精确匹配
        exact_matches = [img for img in all_images if img['brand_name'] == brand_name]
        if exact_matches:
            self.log_debug(f"精确匹配找到: {len(exact_matches)}张图片")
            # 缓存结果（2小时，图片很少变化）
            self.set_cache(cache_key, exact_matches, ttl=7200)
            return self.sort_images_by_priority(exact_matches)
        
        # 如果精确匹配失败，尝试模糊匹配
        self.log_debug(f"精确匹配失败，尝试模糊匹配: {brand_name}")
        fuzzy_matches = []
        
        # 去除括号内容进行匹配
        clean_brand = brand_name.split('(')[0].strip() if '(' in brand_name else brand_name
        
        for img in all_images:
            img_brand = img['brand_name']
            clean_img_brand = img_brand.split('(')[0].strip() if '(' in img_brand else img_brand
            
            # 多种匹配策略
            if (clean_brand == clean_img_brand or 
                clean_brand in img_brand or 
                img_brand in clean_brand or
                clean_img_brand in clean_brand):
                fuzzy_matches.append(img)
        
        if fuzzy_matches:
            self.log_debug(f"模糊匹配找到: {len(fuzzy_matches)}张图片")
            # 缓存结果（10分钟）
            self.set_cache(cache_key, fuzzy_matches, ttl=600)
            return self.sort_images_by_priority(fuzzy_matches)
        
        self.log_debug(f"未找到品牌图片: {brand_name}")
        # 缓存空结果（5分钟）
        self.set_cache(cache_key, [], ttl=300)
        return []
    
    def sort_images_by_priority(self, images: List[Dict]) -> List[Dict]:
        """按图片类型优先级排序"""
        # 定义图片类型优先级
        type_priority = {
            '概念图': 1,
            '设计图': 2,
            '布料图': 3,
            '细节图': 4,
            '效果图': 5,
            '其他': 6
        }
        
        def get_priority(img):
            return type_priority.get(img.get('image_type', '其他'), 6)
        
        return sorted(images, key=get_priority)
    
    def get_image_by_path(self, relative_path: str) -> Optional[str]:
        """根据相对路径获取图片的绝对路径"""
        full_path = os.path.join(self.images_dir, relative_path)
        if os.path.exists(full_path) and os.path.isfile(full_path):
            return full_path
        return None
    
    def get_statistics(self) -> Dict[str, int]:
        """获取图片统计信息 - 带缓存"""
        # 使用基础服务的缓存方法（统一命名空间）
        cache_key = "image:statistics"
        cached_stats = self.get_cache(cache_key)
        if cached_stats:
            return cached_stats
        
        images = self.get_all_images()
        
        # 统计各种信息
        stats = {
            'total_images': len(images),
            'total_brands': len(set(img['brand_name'] for img in images if img['brand_name'])),
            'image_types': {}
        }
        
        # 统计图片类型分布
        for img in images:
            img_type = img.get('image_type', '其他')
            stats['image_types'][img_type] = stats['image_types'].get(img_type, 0) + 1
        
        # 缓存统计结果（10分钟）
        self.set_cache(cache_key, stats, ttl=600)
        return stats
    
    def get_filter_options(self) -> Dict:
        """获取筛选选项 - 带缓存"""
        # 使用基础服务的缓存方法（统一命名空间）
        cache_key = "image:filter:options"
        cached_options = self.get_cache(cache_key)
        if cached_options:
            return cached_options
        
        images = self.get_all_images()
        
        # 收集所有唯一值
        brands = sorted(set(img['brand_name'] for img in images if img['brand_name']))
        image_types = sorted(set(img['image_type'] for img in images if img['image_type']))
        colors = sorted(set(img['color'] for img in images if img['color']))
        
        options = {
            'brands': brands,
            'image_types': image_types,
            'colors': colors
        }
        
        # 缓存筛选选项（10分钟）
        self.set_cache(cache_key, options, ttl=600)
        return options