#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片处理服务 - 本地模式优化版
"""

import os
from urllib.parse import quote, unquote
import re
from typing import List, Dict, Optional, Tuple

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
        self.image_extensions = {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'}
        self.video_extensions = {'mp4', 'webm'}
        self.allowed_extensions = self.image_extensions | self.video_extensions
        
        self.log_info(f"本地图片服务初始化: {self.images_dir}")

    @staticmethod
    def get_media_type(filename: str) -> str:
        """按后缀判断 media_type：image | video"""
        if not filename or '.' not in filename:
            return 'image'
        ext = filename.rsplit('.', 1)[1].lower()
        if ext in {'mp4', 'webm'}:
            return 'video'
        return 'image'

    @staticmethod
    def is_video_media(item: Dict) -> bool:
        """判断媒体项是否为视频文件（不把「视频」类型封面图算作视频）"""
        if not item:
            return False
        if item.get('media_type') == 'video':
            return True
        if item.get('media_type') == 'image':
            return False
        filename = str(item.get('filename') or item.get('relative_path') or item.get('url') or '')
        return ImageService.get_media_type(filename) == 'video'
    
    def parse_filename(self, filename: str) -> Dict[str, str]:
        """解析文件名获取品牌信息"""
        name_without_ext = os.path.splitext(filename)[0]

        # 优先匹配花色格式: 品牌名(颜色)-图片类型-编号
        # （须在无括号规则之前，否则「碧梧(山雪)-视频-01」会被误解析为 brand=碧梧(山雪)）
        pattern_color = r'^([^(]+)\(([^)]+)\)-([^-]+)-(\d+)$'
        match_color = re.match(pattern_color, name_without_ext)
        if match_color:
            return {
                'brand_name': match_color.group(1).strip(),
                'color': match_color.group(2).strip(),
                'image_type': match_color.group(3).strip(),
                'number': match_color.group(4).strip(),
                'has_color': True
            }

        # 无花色: 品牌名-图片类型-编号
        pattern_plain = r'^([^-]+)-([^-]+)-(\d+)$'
        match_plain = re.match(pattern_plain, name_without_ext)
        if match_plain:
            return {
                'brand_name': match_plain.group(1).strip(),
                'image_type': match_plain.group(2).strip(),
                'number': match_plain.group(3).strip(),
                'color': None,
                'has_color': False
            }

        return {
            'brand_name': name_without_ext,
            'image_type': '其他',
            'number': '01',
            'color': None,
            'has_color': False
        }
    
    def is_allowed_file(self, filename: str) -> bool:
        """检查文件是否为允许的图片/视频格式"""
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.allowed_extensions

    def _build_media_entry(self, filename: str, relative_path: str, brand_name: str, parsed_info: Dict, size: int) -> Dict:
        """构建统一媒体条目（含 media_type）"""
        media_type = self.get_media_type(filename)
        image_type = parsed_info.get('image_type') or '其他'
        if media_type == 'video' and image_type == '其他':
            image_type = '视频'
        url = self.encode_static_image_url(relative_path)
        return {
            'filename': filename,
            'relative_path': relative_path,
            'brand_name': brand_name,
            'image_type': image_type,
            'media_type': media_type,
            'color': parsed_info.get('color'),
            'has_color': parsed_info.get('has_color', False),
            'size': size,
            'url': url,
            'thumbnail': url,
            'original': url,
            'poster': None,
        }

    def _attach_video_posters(self, media_list: List[Dict]) -> List[Dict]:
        """为视频挂载同名封面图（品牌名-视频-01.jpg）"""
        if not media_list:
            return media_list
        image_by_stem: Dict[str, Dict] = {}
        for item in media_list:
            if self.is_video_media(item):
                continue
            relative_path = str(item.get('relative_path') or '')
            stem = os.path.splitext(relative_path)[0]
            if stem:
                image_by_stem[stem] = item
        for item in media_list:
            if not self.is_video_media(item):
                continue
            relative_path = str(item.get('relative_path') or '')
            stem = os.path.splitext(relative_path)[0]
            poster_item = image_by_stem.get(stem)
            if poster_item:
                item['poster'] = poster_item.get('url') or poster_item.get('thumbnail')
                poster_item['is_video_poster'] = True
        return media_list

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
        
        # 缓存约 10 分钟；目录改名后请 POST /api/cache/clear（需 admin token）失效
        self.set_cache(cache_key, images, ttl=600)
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
        
        # 扫描根目录下的媒体文件
        for filename in os.listdir(self.images_dir):
            if self.is_allowed_file(filename) and filename.lower() not in social_icons:
                filepath = os.path.join(self.images_dir, filename)
                if os.path.isfile(filepath):
                    parsed_info = self.parse_filename(filename)
                    images.append(self._build_media_entry(
                        filename=filename,
                        relative_path=filename,
                        brand_name=parsed_info['brand_name'],
                        parsed_info=parsed_info,
                        size=os.path.getsize(filepath),
                    ))
        
        # 扫描子文件夹中的媒体文件
        for item in os.listdir(self.images_dir):
            item_path = os.path.join(self.images_dir, item)
            if os.path.isdir(item_path):
                for filename in os.listdir(item_path):
                    if self.is_allowed_file(filename) and filename.lower() not in social_icons:
                        filepath = os.path.join(item_path, filename)
                        if os.path.isfile(filepath):
                            parsed_info = self.parse_filename(filename)
                            relative_path = f"{item}/{filename}"
                            images.append(self._build_media_entry(
                                filename=filename,
                                relative_path=relative_path,
                                brand_name=parsed_info['brand_name'] or item,
                                parsed_info=parsed_info,
                                size=os.path.getsize(filepath),
                            ))

        images = self._attach_video_posters(images)
        image_count = sum(1 for m in images if not self.is_video_media(m))
        video_count = len(images) - image_count
        self.log_info(f"本地媒体扫描完成: 共{len(images)}个（图片{image_count}/视频{video_count}）")
        return sorted(images, key=lambda x: x['brand_name'] or '')
    
    def get_brand_images(self, brand_name: str) -> List[Dict]:
        """获取指定品牌的所有图片 - 带缓存的本地版本"""
        # 使用基础服务的缓存方法（统一命名空间）
        cache_key = f"image:brand:{brand_name}"
        cached_images = self.get_cache(cache_key)
        if cached_images:
            self.log_debug(f"从缓存获取品牌图片: {brand_name} ({len(cached_images)}张)")
            return self.sort_images_by_priority(self._ensure_valid_image_list(cached_images))
        
        self.log_debug(f"查找品牌图片: {brand_name}")
        all_images = self.get_all_images()
        
        # 首先尝试精确匹配
        exact_matches = [img for img in all_images if img['brand_name'] == brand_name]
        if exact_matches:
            self.log_debug(f"精确匹配找到: {len(exact_matches)}张图片")
            fixed = self._ensure_valid_image_list(exact_matches)
            # 缓存结果（2小时，图片很少变化）
            self.set_cache(cache_key, fixed, ttl=7200)
            return self.sort_images_by_priority(fixed)
        
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
            fixed = self._ensure_valid_image_list(fuzzy_matches)
            # 缓存结果（10分钟）
            self.set_cache(cache_key, fixed, ttl=600)
            return self.sort_images_by_priority(fixed)
        
        self.log_debug(f"未找到品牌图片: {brand_name}")
        # 缓存空结果（5分钟）
        self.set_cache(cache_key, [], ttl=300)
        return []
    
    def sort_images_by_priority(self, images: List[Dict]) -> List[Dict]:
        """按图片类型优先级排序"""
        # 定义图片类型优先级（视频排最后，详情由前端单独分区）
        type_priority = {
            '概念图': 1,
            '设计图': 2,
            '布料图': 3,
            '成衣图': 4,
            '模特图': 5,
            '买家秀图': 6,
            '细节图': 7,
            '效果图': 8,
            '其他': 9,
            '视频': 99,
        }
        
        def get_priority(img):
            if self.is_video_media(img):
                return 99
            return type_priority.get(img.get('image_type', '其他'), 9)
        
        return sorted(images, key=get_priority)

    @staticmethod
    def split_images_and_videos(media_list: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """拆分图片与视频列表；同名封面图仅作 poster，不进入图片 gallery"""
        images: List[Dict] = []
        videos: List[Dict] = []
        for item in media_list or []:
            if ImageService.is_video_media(item):
                videos.append(item)
            elif item.get('is_video_poster'):
                continue
            elif (item.get('image_type') or '') == '视频':
                # 未匹配到视频的「视频」类型静图也不进 gallery
                continue
            else:
                images.append(item)
        return images, videos
    

    @staticmethod
    def encode_static_image_url(relative_path: str) -> str:
        """将 relative_path 按路径段编码为 /static/images/...（与前端 encodeURIComponent 分段一致）。"""
        if not relative_path:
            return '/static/images/'
        raw = str(relative_path).replace('\\', '/').lstrip('/')
        # 若已是完整 /static/images/ URL，先取出相对路径再编码，避免双重前缀
        if raw.startswith('static/images/'):
            raw = raw[len('static/images/'):]
        elif raw.startswith('/static/images/'):
            raw = raw[len('/static/images/'):]
        segments = []
        for part in raw.split('/'):
            if part == '':
                continue
            # 先 unquote 再 quote，避免已编码段被二次编码
            segments.append(quote(unquote(part), safe=''))
        return '/static/images/' + '/'.join(segments)

    def get_image_by_path(self, relative_path: str) -> Optional[str]:
        """根据相对路径获取图片的绝对路径"""
        full_path = os.path.join(self.images_dir, relative_path)
        if os.path.exists(full_path) and os.path.isfile(full_path):
            return full_path
        return None

    def _ensure_valid_image_paths(self, img: Dict) -> Dict:
        """修正 relative_path 与磁盘不一致（如目录改名后旧缓存仍用旧文件夹名）"""
        if not img:
            return img
        relative_path = img.get('relative_path') or ''
        filename = img.get('filename') or ''
        brand_name = img.get('brand_name') or ''
        if relative_path and self.get_image_by_path(relative_path):
            return img
        candidates = []
        if brand_name and filename:
            candidates.append(f"{brand_name}/{filename}")
        if filename and '/' not in relative_path:
            candidates.append(filename)
        for candidate in candidates:
            if self.get_image_by_path(candidate):
                fixed = dict(img)
                fixed['relative_path'] = candidate
                fixed['url'] = self.encode_static_image_url(candidate)
                fixed['thumbnail'] = fixed['url']
                fixed['original'] = fixed['url']
                return fixed
        return img

    def _ensure_valid_image_list(self, images: List[Dict]) -> List[Dict]:
        return [self._ensure_valid_image_paths(img) for img in (images or [])]
    
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