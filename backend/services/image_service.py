#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片处理服务
"""

import os
import re
from typing import List, Dict, Optional

class ImageService:
    """图片处理服务类"""
    
    def __init__(self, images_dir: str = None):
        """初始化图片服务"""
        if images_dir is None:
            # 获取项目根目录
            import os
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            images_dir = os.path.join(project_root, 'frontend', 'static', 'images')
        
        self.images_dir = images_dir
        self.allowed_extensions = {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'}
    
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
        """获取所有图片信息"""
        images = []
        
        if not os.path.exists(self.images_dir):
            return images
        
        # 扫描根目录下的图片文件
        for filename in os.listdir(self.images_dir):
            if self.is_allowed_file(filename):
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
                        'size': os.path.getsize(filepath)
                    })
        
        # 扫描子文件夹中的图片
        for item in os.listdir(self.images_dir):
            item_path = os.path.join(self.images_dir, item)
            if os.path.isdir(item_path):
                for filename in os.listdir(item_path):
                    if self.is_allowed_file(filename):
                        filepath = os.path.join(item_path, filename)
                        if os.path.isfile(filepath):
                            parsed_info = self.parse_filename(filename)
                            images.append({
                                'filename': filename,
                                'relative_path': f"{item}/{filename}",
                                'brand_name': parsed_info['brand_name'] or item,
                                'image_type': parsed_info['image_type'],
                                'color': parsed_info['color'],
                                'has_color': parsed_info['has_color'],
                                'size': os.path.getsize(filepath)
                            })
        
        return sorted(images, key=lambda x: x['brand_name'] or '')
    
    def get_brand_images(self, brand_name: str) -> List[Dict]:
        """获取指定品牌的所有图片"""
        all_images = self.get_all_images()
        
        # 首先尝试精确匹配
        exact_matches = [img for img in all_images if img['brand_name'] == brand_name]
        if exact_matches:
            return exact_matches
        
        # 如果没有精确匹配，尝试基础品牌名匹配
        # 查找所有以该品牌名开头的图片（包括带颜色的）
        base_matches = []
        for img in all_images:
            img_brand = img['brand_name']
            # 检查是否是同一基础品牌名
            if img_brand.startswith(brand_name):
                # 确保是完整的品牌名匹配，而不是部分匹配
                if img_brand == brand_name or (len(img_brand) > len(brand_name) and img_brand[len(brand_name)] == '('):
                    base_matches.append(img)
        
        return base_matches
    
    def get_image_by_path(self, relative_path: str) -> Optional[str]:
        """根据相对路径获取图片的完整路径"""
        full_path = os.path.join(self.images_dir, relative_path)
        
        if not os.path.exists(full_path):
            return None
        
        # 安全检查
        if not os.path.abspath(full_path).startswith(os.path.abspath(self.images_dir)):
            return None
        
        return full_path
    
    def get_statistics(self) -> Dict[str, int]:
        """获取图片统计信息"""
        images = self.get_all_images()
        brands = set(img['brand_name'] for img in images)
        
        return {
            'total_images': len(images),
            'total_brands': len(brands),
            'design_images': len([img for img in images if img['image_type'] == '设计图']),
            'fabric_images': len([img for img in images if img['image_type'] == '布料图'])
        }
    
    def get_filter_options(self) -> Dict:
        """获取筛选选项和品牌统计"""
        try:
            # 从数据库获取产品信息
            from backend.models import Product
            
            # 获取所有产品
            products = Product.query.all()
            
            if not products:
                # 如果数据库中没有产品，返回默认选项
                return {
                    'filters': {
                        'years': [2024, 2023, 2022, 2021],
                        'materials': ['棉麻', '真丝', '雪纺', '织锦'],
                        'theme_series': ['经典系列', '画韵春秋系列', '长物志系列', '执念系列'],
                        'print_sizes': ['循环印花料', '旗袍定位料']
                    },
                    'brand_counts': {
                        'years': {2024: 10, 2023: 8, 2022: 6, 2021: 4},
                        'materials': {'棉麻': 15, '真丝': 8, '雪纺': 5, '织锦': 4},
                        'theme_series': {'经典系列': 12, '画韵春秋系列': 8, '长物志系列': 6, '执念系列': 4},
                        'print_sizes': {'循环印花料': 20, '旗袍定位料': 8}
                    }
                }
            
            # 从数据库产品中提取筛选选项
            years = set()
            materials = set()
            theme_series = set()
            print_sizes = set()
            
            # 统计每个筛选项的品牌数量
            filter_stats = {
                'years': {},
                'materials': {},
                'theme_series': {},
                'print_sizes': {}
            }
            
            for product in products:
                if product.year:
                    years.add(product.year)
                    filter_stats['years'][product.year] = filter_stats['years'].get(product.year, 0) + 1
                
                if product.material:
                    materials.add(product.material)
                    filter_stats['materials'][product.material] = filter_stats['materials'].get(product.material, 0) + 1
                
                if product.theme_series:
                    theme_series.add(product.theme_series)
                    filter_stats['theme_series'][product.theme_series] = filter_stats['theme_series'].get(product.theme_series, 0) + 1
                
                if product.print_size:
                    print_sizes.add(product.print_size)
                    filter_stats['print_sizes'][product.print_size] = filter_stats['print_sizes'].get(product.print_size, 0) + 1
            
            return {
                'filters': {
                    'years': sorted(list(years), reverse=True) if years else [2024],
                    'materials': sorted(list(materials)) if materials else ['棉麻'],
                    'theme_series': sorted(list(theme_series)) if theme_series else ['经典系列'],
                    'print_sizes': sorted(list(print_sizes)) if print_sizes else ['循环印花料']
                },
                'brand_counts': filter_stats
            }
            
        except Exception as e:
            print(f"获取筛选选项失败: {e}")
            # 返回默认选项
            return {
                'filters': {
                    'years': [2024, 2023, 2022, 2021],
                    'materials': ['棉麻', '真丝', '雪纺', '织锦'],
                    'theme_series': ['经典系列', '画韵春秋系列', '长物志系列', '执念系列'],
                    'print_sizes': ['循环印花料', '旗袍定位料']
                },
                'brand_counts': {
                    'years': {2024: 10, 2023: 8, 2022: 6, 2021: 4},
                    'materials': {'棉麻': 15, '真丝': 8, '雪纺': 5, '织锦': 4},
                    'theme_series': {'经典系列': 12, '画韵春秋系列': 8, '长物志系列': 6, '执念系列': 4},
                    'print_sizes': {'循环印花料': 20, '旗袍定位料': 8}
                }
            }