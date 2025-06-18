#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阿里云OSS图片服务
"""

import os
import re
from typing import List, Dict, Optional
from flask import current_app

class OSSImageService:
    """OSS图片处理服务类"""
    
    def __init__(self):
        """初始化OSS图片服务"""
        self.base_url = current_app.config['OSS_BASE_URL']
        self.thumbnail_params = current_app.config['OSS_THUMBNAIL_PARAMS']
        self.medium_params = current_app.config['OSS_MEDIUM_PARAMS']
        self.allowed_extensions = {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'}
        
        # 图片类型映射
        self.image_type_mapping = {
            'buliaotu': '布料图',
            'shejitu': '设计图',
            'chengyitu': '成衣图',
            'xuanchuantu': '宣传图',
            'motettu': '模特图',
            'maijiashow': '买家秀图'
        }
    
    def parse_oss_filename(self, filename: str) -> Dict[str, str]:
        """解析OSS文件名获取品牌信息"""
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
    
    def generate_oss_url(self, oss_path: str, size: str = 'original') -> str:
        """生成OSS图片URL"""
        base_url = f"{self.base_url}/{oss_path}"
        
        if size == 'thumbnail':
            return base_url + self.thumbnail_params
        elif size == 'medium':
            return base_url + self.medium_params
        else:
            return base_url
    
    def get_all_images_from_oss(self) -> List[Dict]:
        """从OSS获取所有图片信息
        
        基于已知的OSS迁移结构来构建图片列表
        """
        images = []
        
        # 获取OSS图片结构
        oss_image_structure = self._get_oss_image_structure()
        
        for image_info in oss_image_structure:
            oss_path = image_info['oss_path']
            filename = os.path.basename(oss_path)
            
            if self.is_allowed_file(filename):
                parsed_info = self.parse_oss_filename(filename)
                
                # 从OSS路径推断图片类型
                path_parts = oss_path.split('/')
                if len(path_parts) >= 2:
                    type_folder = path_parts[1]  # images/buliaotu/品牌名/文件名
                    image_type = self.image_type_mapping.get(type_folder, parsed_info['image_type'])
                else:
                    image_type = parsed_info['image_type']
                
                images.append({
                    'filename': filename,
                    'relative_path': oss_path,
                    'oss_path': oss_path,
                    'brand_name': parsed_info['brand_name'],
                    'image_type': image_type,
                    'color': parsed_info['color'],
                    'has_color': parsed_info['has_color'],
                    'original_url': self.generate_oss_url(oss_path, 'original'),
                    'medium_url': self.generate_oss_url(oss_path, 'medium'),
                    'thumbnail_url': self.generate_oss_url(oss_path, 'thumbnail'),
                    'size': image_info.get('size', 0)
                })
        
        return sorted(images, key=lambda x: x['brand_name'] or '')
    
    def _get_oss_image_structure(self) -> List[Dict]:
        """获取OSS图片结构
        
        基于本地图片目录推断OSS结构，因为我们已经完成了迁移
        """
        # 尝试从本地图片目录推断OSS结构
        local_images_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'frontend', 'static', 'images'
        )
        
        oss_images = []
        
        if os.path.exists(local_images_dir):
            # 扫描本地图片目录，推断OSS路径
            for filename in os.listdir(local_images_dir):
                if self.is_allowed_file(filename):
                    filepath = os.path.join(local_images_dir, filename)
                    if os.path.isfile(filepath):
                        parsed_info = self.parse_oss_filename(filename)
                        image_type = parsed_info['image_type']
                        
                        # 推断OSS路径
                        type_folder = self._get_type_folder(image_type)
                        brand_folder = parsed_info['brand_name']
                        oss_path = f"images/{type_folder}/{brand_folder}/{filename}"
                        
                        oss_images.append({
                            'oss_path': oss_path,
                            'size': os.path.getsize(filepath)
                        })
            
            # 扫描子文件夹
            for item in os.listdir(local_images_dir):
                item_path = os.path.join(local_images_dir, item)
                if os.path.isdir(item_path):
                    for filename in os.listdir(item_path):
                        if self.is_allowed_file(filename):
                            filepath = os.path.join(item_path, filename)
                            if os.path.isfile(filepath):
                                parsed_info = self.parse_oss_filename(filename)
                                image_type = parsed_info['image_type']
                                
                                # 推断OSS路径
                                type_folder = self._get_type_folder(image_type)
                                brand_folder = parsed_info['brand_name'] or item
                                oss_path = f"images/{type_folder}/{brand_folder}/{filename}"
                                
                                oss_images.append({
                                    'oss_path': oss_path,
                                    'size': os.path.getsize(filepath)
                                })
        
        return oss_images
    
    def _get_type_folder(self, image_type: str) -> str:
        """根据图片类型获取OSS文件夹名"""
        type_folder_mapping = {
            '布料图': 'buliaotu',
            '设计图': 'shejitu',
            '成衣图': 'chengyitu',
            '宣传图': 'xuanchuantu',
            '模特图': 'motettu',
            '买家秀图': 'maijiashow'
        }
        return type_folder_mapping.get(image_type, 'other')
    
    def get_brand_images(self, brand_name: str) -> List[Dict]:
        """获取指定品牌的所有OSS图片"""
        all_images = self.get_all_images_from_oss()
        
        # 首先尝试精确匹配
        exact_matches = [img for img in all_images if img['brand_name'] == brand_name]
        if exact_matches:
            return self.sort_images_by_priority(exact_matches)
        
        # 如果没有精确匹配，尝试基础品牌名匹配
        base_matches = []
        for img in all_images:
            img_brand = img['brand_name']
            if img_brand.startswith(brand_name):
                if img_brand == brand_name or (len(img_brand) > len(brand_name) and img_brand[len(brand_name)] == '('):
                    base_matches.append(img)
        
        return self.sort_images_by_priority(base_matches)
    
    def sort_images_by_priority(self, images: List[Dict]) -> List[Dict]:
        """按图片类型优先级排序图片"""
        priority_map = {
            '宣传图': 1,
            '设计图': 2,
            '成衣图': 3,
            '布料图': 4,
            '模特图': 5,
            '买家秀图': 6,
            '其他': 99
        }
        
        for img in images:
            image_type = img.get('image_type', '其他')
            img['priority'] = priority_map.get(image_type, 99)
        
        return sorted(images, key=lambda x: (x['priority'], x['filename']))
    
    def get_statistics(self) -> Dict[str, int]:
        """获取OSS图片统计信息"""
        images = self.get_all_images_from_oss()
        brands = set(img['brand_name'] for img in images)
        
        return {
            'total_images': len(images),
            'total_brands': len(brands),
            'design_images': len([img for img in images if img['image_type'] == '设计图']),
            'fabric_images': len([img for img in images if img['image_type'] == '布料图'])
        } 