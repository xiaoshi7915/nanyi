#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
品牌控制器
处理品牌相关的业务逻辑
"""

from typing import Dict, List, Optional
from urllib.parse import unquote
from backend.services.product_service import ProductService
from backend.models.brand_like import BrandLike
from backend.utils.logger import logger


class BrandController:
    """品牌控制器类"""
    
    def __init__(self):
        """初始化品牌控制器"""
        self.product_service = ProductService()

    @staticmethod
    def _brand_images_cache_valid(images: List[Dict]) -> bool:
        """校验缓存图片路径在磁盘上存在，避免目录改名后返回 404 路径"""
        if not images:
            return False
        from backend.services.image_service import ImageService
        image_service = ImageService()
        for img in images:
            relative_path = img.get('relative_path') or ''
            if not relative_path:
                return False
            if not image_service.get_image_by_path(relative_path):
                fixed = image_service._ensure_valid_image_paths(img)
                if not image_service.get_image_by_path(fixed.get('relative_path') or ''):
                    return False
        return True
    
    def get_brand_detail(self, brand_name: str) -> Dict:
        """
        获取品牌详细信息（带缓存）
        
        Args:
            brand_name: 品牌名称（URL编码）
        
        Returns:
            dict: 品牌详细信息，如果不存在则返回None
        """
        # 使用缓存服务
        from backend.services.cache_service import cache_service
        
        # 生成缓存键
        cache_key = cache_service.generate_key('brand_detail', brand_name=brand_name)
        
        # 尝试从缓存获取
        cached_result = cache_service.get(cache_key)
        if cached_result:
            cached_images = cached_result.get('images') or cached_result.get('brand_info', {}).get('images') or []
            if self._brand_images_cache_valid(cached_images):
                logger.debug(f"从缓存获取品牌详情: {brand_name}")
                return cached_result
            logger.info(f"品牌详情缓存路径失效，重新加载: {brand_name}")
            cache_service.delete(cache_key)
        
        # URL解码品牌名
        decoded_brand_name = unquote(brand_name)
        logger.debug(f"API请求品牌详情: {brand_name} -> 解码后: {decoded_brand_name}")
        
        # 从品牌名中提取基础品牌名（去掉花色信息）
        base_brand_name = decoded_brand_name
        if '(' in decoded_brand_name:
            base_brand_name = decoded_brand_name.split('(')[0]
        
        logger.debug(f"基础品牌名: {base_brand_name}")
        
        # 使用产品服务获取品牌信息
        brand_info = self.product_service.get_brand_detail(decoded_brand_name)
        
        # 如果使用完整品牌名没找到，尝试使用基础品牌名
        if not brand_info and base_brand_name != decoded_brand_name:
            logger.debug(f"使用完整品牌名未找到，尝试基础品牌名: {base_brand_name}")
            brand_info = self.product_service.get_brand_detail(base_brand_name)
        
        if not brand_info:
            logger.warning(f"品牌不存在: {decoded_brand_name}")
            return None
        
        # 从brand_info中获取images
        brand_images = brand_info.get('images', [])
        
        # 构建品牌信息字典
        brand_info_dict = {
            'name': decoded_brand_name,  # 返回解码后的品牌名
            'base_name': base_brand_name,  # 返回基础品牌名
            **brand_info  # 包含所有品牌信息
        }
        
        # 添加点赞数
        try:
            like_count = BrandLike.get_like_count(base_brand_name)
            brand_info_dict['like_count'] = like_count
            logger.debug(f"获取点赞数成功: {like_count}")
        except Exception as e:
            logger.warning(f"获取点赞数失败: {e}")
            brand_info_dict['like_count'] = 0
        
        logger.debug(f"返回品牌详情成功: {brand_info.get('name', '未知')}, 图片数量: {len(brand_images)}")
        
        # 构建返回结果
        result = {
            'success': True,
            'brand_info': brand_info_dict,
            'images': brand_images,
            'imageCount': len(brand_images)
        }
        
        # 缓存结果（24 小时，图片与元数据变更频率低）
        cache_service.set(cache_key, result, ttl=86400)
        logger.debug(f"品牌详情已缓存: {brand_name}")
        
        return result

    def get_brand_images_only(self, brand_name: str) -> Optional[Dict]:
        """
        仅返回品牌图片列表（跳过 DB 产品查询与点赞统计，供详情弹窗快速加载）
        """
        from backend.services.cache_service import cache_service
        from backend.services.image_service import ImageService

        cache_key = cache_service.generate_key('brand_images', brand_name=brand_name)
        cached_result = cache_service.get(cache_key)
        if cached_result:
            cached_images = cached_result.get('images') or []
            if self._brand_images_cache_valid(cached_images):
                logger.debug(f"从缓存获取品牌图片: {brand_name}")
                return cached_result
            logger.info(f"品牌图片缓存路径失效，重新加载: {brand_name}")
            cache_service.delete(cache_key)

        decoded_brand_name = unquote(brand_name)
        base_brand_name = decoded_brand_name.split('(')[0] if '(' in decoded_brand_name else decoded_brand_name

        image_service = ImageService()
        brand_images = image_service.get_brand_images(decoded_brand_name)
        if not brand_images and base_brand_name != decoded_brand_name:
            brand_images = image_service.get_brand_images(base_brand_name)

        if not brand_images:
            logger.warning(f"品牌图片不存在: {decoded_brand_name}")
            return None

        result = {
            'success': True,
            'images': brand_images,
            'imageCount': len(brand_images),
        }
        cache_service.set(cache_key, result, ttl=86400)
        return result
    
    def toggle_like(self, brand_name: str, unique_id: str, client_ip: str, user_agent: str) -> Dict:
        """
        切换品牌点赞状态（点赞/取消点赞）
        
        Args:
            brand_name: 品牌名称（URL编码）
            unique_id: 唯一标识（用于防重复点赞）
            client_ip: 客户端IP
            user_agent: 用户代理
        
        Returns:
            dict: 点赞操作结果
        """
        import urllib.parse
        decoded_brand_name = urllib.parse.unquote(brand_name, encoding='utf-8')
        
        # 提取基础品牌名（去掉颜色部分）
        base_brand_name = decoded_brand_name.split('(')[0] if '(' in decoded_brand_name else decoded_brand_name
        
        # 使用数据库存储点赞记录
        try:
            success, like_count, is_liked = BrandLike.toggle_like(
                base_brand_name, unique_id, client_ip, user_agent
            )
            
            if not success:
                # 返回错误字典（路由层会使用APIResponse包装）
                return {
                    'success': False,
                    'message': like_count,
                    'liked': not is_liked,  # 如果操作失败，状态保持原样
                    'like_count': BrandLike.get_like_count(base_brand_name)
                }
            
            message = '点赞成功！' if is_liked else '取消点赞成功！'
            # 返回成功字典（路由层会使用APIResponse包装）
            return {
                'success': True,
                'message': message,
                'liked': is_liked,
                'like_count': like_count
            }
            
        except Exception as db_error:
            # 禁止 DB 失败后写内存计数：会与库内 like_count 分叉
            logger.error(f"数据库点赞失败: {db_error}")
            return {
                'success': False,
                'message': '点赞服务暂时不可用，请稍后重试',
                'liked': False,
                'like_count': 0,
            }
    
    def get_like_status(self, brand_name: str, unique_id: str) -> Dict:
        """
        获取品牌点赞状态
        
        Args:
            brand_name: 品牌名称（URL编码）
            unique_id: 唯一标识
        
        Returns:
            dict: 点赞状态信息
        """
        import urllib.parse
        decoded_brand_name = urllib.parse.unquote(brand_name, encoding='utf-8')
        
        # 提取基础品牌名（去掉颜色部分）
        base_brand_name = decoded_brand_name.split('(')[0] if '(' in decoded_brand_name else decoded_brand_name
        
        # 使用数据库查询点赞状态
        try:
            has_liked = BrandLike.check_user_liked(base_brand_name, unique_id)
            like_count = BrandLike.get_like_count(base_brand_name)
            
            # 返回成功字典（路由层会使用APIResponse包装）
            return {
                'success': True,
                'liked': has_liked,
                'like_count': like_count
            }
            
        except Exception as db_error:
            logger.warning(f"数据库查询失败，回退到缓存: {db_error}")
            # 数据库失败时回退到缓存
            from backend.services.cache_service import cache_service
            
            cache_key = f"like_{unique_id}"
            cache_count_key = f"like_count_{base_brand_name}"
            
            has_liked = bool(cache_service.get(cache_key))
            like_count = cache_service.get(cache_count_key) or 0
            
            # 返回成功字典（路由层会使用APIResponse包装）
            return {
                'success': True,
                'liked': has_liked,
                'like_count': like_count
            }
