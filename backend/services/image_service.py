#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片处理服务
"""

import os
import re
from typing import List, Dict, Optional
from flask import current_app

class ImageService:
    """图片处理服务类 - 支持本地和OSS图片源切换"""
    
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
        
        # 获取图片源配置 - 优先从环境变量获取
        import os
        self.image_source = os.environ.get('IMAGE_SOURCE', 'oss').lower()
        
        # 如果在Flask应用上下文中，也尝试从配置获取
        try:
            if current_app:
                self.image_source = current_app.config.get('IMAGE_SOURCE', self.image_source).lower()
        except:
            pass
            
        print(f"🔧 图片服务初始化: 当前图片源 = {self.image_source}")
        
        # 根据配置初始化相应的服务
        if self.image_source == 'oss':
            self._init_oss_service()
        else:
            print(f"📁 使用本地图片源: {self.images_dir}")
    
    def _init_oss_service(self):
        """初始化OSS服务"""
        try:
            from .oss_image_service import OSSImageService
            self.oss_service = OSSImageService()
            print(f"🌐 OSS服务初始化成功: {current_app.config['OSS_BASE_URL']}")
        except Exception as e:
            print(f"❌ OSS服务初始化失败: {e}")
            print("🔄 自动切换到本地图片源")
            self.image_source = 'local'
    
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
        """获取所有图片信息 - 根据配置使用OSS或本地"""
        if self.image_source == 'oss' and hasattr(self, 'oss_service'):
            print("🌐 从OSS获取图片数据")
            return self._get_oss_images_with_urls()
        else:
            print("📁 从本地获取图片数据")
            return self._get_local_images()
    
    def _get_oss_images_with_urls(self) -> List[Dict]:
        """从OSS获取图片信息并添加URL字段"""
        images = self.oss_service.get_all_images_from_oss()
        
        # 为每个图片添加URL信息，保持与本地图片相同的数据结构
        for img in images:
            # 添加本地兼容的URL字段
            img['url'] = img['medium_url']  # 默认使用中等尺寸
            img['thumbnail'] = img['thumbnail_url']
            img['original'] = img['original_url']
            
        print(f"🌐 OSS图片加载完成: 共{len(images)}张图片")
        return images
    
    def _get_local_images(self) -> List[Dict]:
        """从本地获取图片信息"""
        images = []
        
        if not os.path.exists(self.images_dir):
            print(f"⚠️ 本地图片目录不存在: {self.images_dir}")
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
                    if self.is_allowed_file(filename):
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
        
        print(f"📁 本地图片加载完成: 共{len(images)}张图片")
        return sorted(images, key=lambda x: x['brand_name'] or '')
    
    def get_brand_images(self, brand_name: str) -> List[Dict]:
        """获取指定品牌的所有图片 - 支持OSS和本地"""
        if self.image_source == 'oss' and hasattr(self, 'oss_service'):
            print(f"🌐 从OSS获取品牌图片: {brand_name}")
            images = self.oss_service.get_brand_images(brand_name)
            # 添加URL字段
            for img in images:
                img['url'] = img['medium_url']
                img['thumbnail'] = img['thumbnail_url']
                img['original'] = img['original_url']
            return images
        else:
            print(f"📁 从本地获取品牌图片: {brand_name}")
            return self._get_local_brand_images(brand_name)
    
    def _get_local_brand_images(self, brand_name: str) -> List[Dict]:
        """从本地获取指定品牌的所有图片"""
        all_images = self._get_local_images()
        
        print(f"📁 本地图片匹配: 查找品牌 '{brand_name}', 总图片数: {len(all_images)}")
        
        # 首先尝试精确匹配
        exact_matches = [img for img in all_images if img['brand_name'] == brand_name]
        if exact_matches:
            print(f"📁 精确匹配成功: 找到 {len(exact_matches)} 张图片")
            return self.sort_images_by_priority(exact_matches)
        
        # 如果是带颜色的品牌名（包含括号），尝试匹配基础品牌名
        base_brand_name = brand_name
        if '(' in brand_name:
            base_brand_name = brand_name.split('(')[0].strip()
            print(f"📁 提取基础品牌名: '{base_brand_name}'")
            
            # 尝试基础品牌名精确匹配
            base_exact_matches = [img for img in all_images if img['brand_name'] == base_brand_name]
            if base_exact_matches:
                print(f"📁 基础品牌名精确匹配成功: 找到 {len(base_exact_matches)} 张图片")
                return self.sort_images_by_priority(base_exact_matches)
        
        # 尝试模糊匹配 - 查找包含品牌名的图片
        fuzzy_matches = []
        for img in all_images:
            img_brand = img['brand_name']
            
            # 方式1: 图片品牌名包含查询品牌名
            if brand_name in img_brand:
                fuzzy_matches.append(img)
                continue
                
            # 方式2: 查询品牌名包含图片品牌名
            if img_brand in brand_name:
                fuzzy_matches.append(img)
                continue
                
            # 方式3: 基础品牌名匹配（去除括号后的匹配）
            if base_brand_name != brand_name:
                img_base_brand = img_brand.split('(')[0].strip() if '(' in img_brand else img_brand
                if base_brand_name == img_base_brand or base_brand_name in img_brand or img_brand in base_brand_name:
                    fuzzy_matches.append(img)
                    continue
        
        if fuzzy_matches:
            print(f"📁 模糊匹配成功: 找到 {len(fuzzy_matches)} 张图片")
            return self.sort_images_by_priority(fuzzy_matches)
        
        # 最后尝试部分匹配 - 去除所有特殊字符后匹配
        clean_brand = brand_name.replace('(', '').replace(')', '').replace('/', '').replace('-', '').replace('_', '').replace(' ', '')
        partial_matches = []
        
        for img in all_images:
            img_brand = img['brand_name']
            clean_img_brand = img_brand.replace('(', '').replace(')', '').replace('/', '').replace('-', '').replace('_', '').replace(' ', '')
            
            if clean_brand in clean_img_brand or clean_img_brand in clean_brand:
                partial_matches.append(img)
        
        if partial_matches:
            print(f"📁 部分匹配成功: 找到 {len(partial_matches)} 张图片")
            return self.sort_images_by_priority(partial_matches)
        
        print(f"📁 未找到匹配的图片")
        # 打印前10个图片的品牌名用于调试
        sample_brands = [img['brand_name'] for img in all_images[:10]]
        print(f"📁 图片示例品牌名: {sample_brands}")
        
        return []
    
    def sort_images_by_priority(self, images: List[Dict]) -> List[Dict]:
        """按图片类型优先级排序图片
        优先级顺序：概念图 > 设计图 > 成衣图 > 布料图 > 模特图 > 买家秀图 > 其他类型
        """
        # 定义图片类型的优先级，数字越小优先级越高
        priority_map = {
            '概念图': 1,
            '设计图': 2,
            '成衣图': 3,
            '布料图': 4,
            '模特图': 5,
            '买家秀图': 6,
            '其他': 99
        }
        
        # 给每个图片分配优先级
        for img in images:
            image_type = img.get('image_type', '其他')
            img['priority'] = priority_map.get(image_type, 99)
        
        # 按优先级排序，同优先级按文件名排序保证稳定性
        sorted_images = sorted(images, key=lambda x: (x['priority'], x['filename']))
        
        return sorted_images
    
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
        """获取图片统计信息 - 支持OSS和本地"""
        if self.image_source == 'oss' and hasattr(self, 'oss_service'):
            print("🌐 从OSS获取统计信息")
            return self.oss_service.get_statistics()
        else:
            print("📁 从本地获取统计信息")
            images = self._get_local_images()
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
                    # 按/分隔符拆分材质，每个拆分后的材质都算作一种分类
                    material_list = [m.strip() for m in product.material.split('/') if m.strip()]
                    for material in material_list:
                        materials.add(material)
                        filter_stats['materials'][material] = filter_stats['materials'].get(material, 0) + 1
                
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