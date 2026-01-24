#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
试衣控制器
处理AI试衣相关的业务逻辑，包括获取款式列表、启动试衣任务、查询任务状态等
"""

import os
import re
from typing import Dict, List, Optional
from flask import request

from backend.services.try_on_service import TryOnService
from backend.services.image_service import ImageService
from backend.utils.logger import logger
from backend.exceptions import ValidationError, NotFoundError, ServiceError


class TryOnController:
    """试衣控制器类"""
    
    def __init__(self):
        """初始化试衣控制器"""
        self.try_on_service = TryOnService()
        self.image_service = ImageService()
        
        # 获取图片目录路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        self.images_dir = os.path.join(project_root, 'frontend', 'static', 'images')
    
    def get_available_styles(self, base_brand_name: Optional[str] = None) -> Dict:
        """
        获取可用的款式列表（品牌+颜色组合）
        
        Args:
            base_brand_name: 可选的基础品牌名，如果提供则只返回该品牌的款式
        
        Returns:
            dict: 包含款式列表的字典
        """
        try:
            # 如果指定了品牌名，只获取该品牌的图片
            if base_brand_name:
                logger.info(f"获取指定品牌的款式列表: {base_brand_name}")
                # 获取所有图片，然后过滤出该基础品牌的所有变体
                all_brand_images = self.image_service.get_all_images()
                all_images = []
                
                for img in all_brand_images:
                    brand_name = img.get('brand_name')
                    if not brand_name:
                        continue
                    
                    # 提取基础品牌名
                    if '(' in brand_name:
                        img_base_brand = brand_name.split('(')[0].strip()
                    else:
                        img_base_brand = brand_name
                    
                    # 如果基础品牌名匹配，添加到列表
                    if img_base_brand == base_brand_name:
                        all_images.append(img)
                        logger.debug(f"找到匹配的款式: {brand_name} (基础品牌: {img_base_brand})")
                
                logger.info(f"找到 {len(all_images)} 张图片属于品牌 '{base_brand_name}'")
            else:
                # 获取所有图片
                logger.info("获取所有品牌的款式列表")
                all_images = self.image_service.get_all_images()
            
            # 提取所有唯一的品牌+颜色组合
            styles_map = {}
            
            for img in all_images:
                brand_name = img.get('brand_name')
                if not brand_name:
                    continue
                
                # 解析品牌名，提取基础品牌和颜色
                # 格式1: "丹若(玉绿)" -> base_brand="丹若", color="玉绿"
                # 格式2: "丹若" -> base_brand="丹若", color=None
                if '(' in brand_name and ')' in brand_name:
                    # 有颜色信息
                    match = re.match(r'^([^(]+)\(([^)]+)\)$', brand_name)
                    if match:
                        base_brand = match.group(1).strip()
                        color = match.group(2).strip()
                        has_color = True
                    else:
                        base_brand = brand_name
                        color = None
                        has_color = False
                else:
                    # 没有颜色信息
                    base_brand = brand_name
                    color = None
                    has_color = False
                
                # 如果指定了品牌名，只包含该品牌的款式
                if base_brand_name:
                    # 精确匹配基础品牌名
                    if base_brand != base_brand_name:
                        continue
                    logger.debug(f"匹配品牌: {base_brand} == {base_brand_name}, 品牌名: {brand_name}")
                
                # 使用品牌名（包含颜色）作为唯一标识
                style_key = brand_name
                
                if style_key not in styles_map:
                    # 获取该款式的预览图（优先使用布料图或成衣图）
                    preview_image = self._get_preview_image_for_brand(brand_name)
                    
                    styles_map[style_key] = {
                        'brand_name': brand_name,
                        'base_brand': base_brand,
                        'color': color,
                        'has_color': has_color,
                        'preview_image': preview_image
                    }
            
            # 转换为列表并排序
            styles = list(styles_map.values())
            styles.sort(key=lambda x: (x['base_brand'], x['color'] or ''))
            
            logger.info(f"获取可用款式列表: 共{len(styles)}个款式" + (f" (品牌: {base_brand_name})" if base_brand_name else ""))
            
            return {
                'success': True,
                'styles': styles
            }
            
        except Exception as e:
            logger.error(f"获取款式列表失败: {e}", exc_info=True)
            return {
                'success': False,
                'error': f'获取款式列表失败: {str(e)}'
            }
    
    def _get_preview_image_for_brand(self, brand_name: str) -> Optional[str]:
        """
        获取指定品牌的预览图URL
        
        Args:
            brand_name: 品牌名称
        
        Returns:
            str: 预览图URL，如果找不到则返回None
        """
        try:
            # 获取该品牌的所有图片
            brand_images = self.image_service.get_brand_images(brand_name)
            
            if not brand_images:
                return None
            
            # 优先查找布料图
            fabric_image = next(
                (img for img in brand_images if img.get('image_type') == '布料图'),
                None
            )
            
            # 如果没有布料图，使用成衣图
            if not fabric_image:
                fabric_image = next(
                    (img for img in brand_images if img.get('image_type') == '成衣图'),
                    None
                )
            
            # 如果还没有，使用第一张图片
            if not fabric_image:
                fabric_image = brand_images[0]
            
            # 返回图片URL
            if fabric_image.get('url'):
                return fabric_image['url']
            elif fabric_image.get('relative_path'):
                return f"/static/images/{fabric_image['relative_path']}"
            elif fabric_image.get('filename'):
                return f"/static/images/{fabric_image['filename']}"
            
            return None
            
        except Exception as e:
            logger.warning(f"获取品牌预览图失败: {brand_name}, {e}")
            return None
    
    def start_try_on_task(
        self,
        brand_name: str,
        user_image_file: bytes,
        user_image_filename: str
    ) -> Dict:
        """
        启动AI试衣任务
        
        Args:
            brand_name: 选定的款式名称（品牌+颜色，如"丹若(玉绿)"）
            user_image_file: 用户上传的照片文件内容（bytes）
            user_image_filename: 用户上传的照片文件名
        
        Returns:
            dict: 包含task_id和状态信息的字典
        
        Raises:
            ValidationError: 参数验证失败
            NotFoundError: 布料图不存在
            ServiceError: AI试衣服务调用失败
        """
        # 参数验证
        if not brand_name:
            raise ValidationError(
                message='品牌名称不能为空',
                field='brand_name'
            )
        
        if not user_image_file:
            raise ValidationError(
                message='用户照片不能为空',
                field='user_image'
            )
        
        if not user_image_filename:
            raise ValidationError(
                message='用户照片文件名不能为空',
                field='user_image_filename'
            )
        
        try:
            # 获取该款式的布料图路径
            fabric_image_path = self._get_fabric_image_path(brand_name)
            
            if not fabric_image_path:
                raise NotFoundError(
                    message=f'未找到款式"{brand_name}"的布料图',
                    resource_type='fabric_image',
                    resource_id=brand_name
                )
            
            logger.info(f"启动AI试衣任务: brand_name={brand_name}, fabric_image={fabric_image_path}")
            
            # 调用试衣服务
            result = self.try_on_service.generate_try_on(
                fabric_image_path=fabric_image_path,
                user_image_file=user_image_file,
                user_image_filename=user_image_filename
            )
            
            return result
            
        except (ValidationError, NotFoundError, ServiceError):
            # 重新抛出这些异常，让路由层处理
            raise
        except Exception as e:
            logger.error(f"启动试衣任务失败: {e}", exc_info=True)
            raise ServiceError(
                message=f'启动试衣任务失败: {str(e)}',
                service_name='TryOnController',
                details={'brand_name': brand_name, 'error': str(e)}
            )
    
    def _get_fabric_image_path(self, brand_name: str) -> Optional[str]:
        """
        获取指定款式的布料图本地文件路径
        
        Args:
            brand_name: 品牌名称（包含颜色，如"丹若(玉绿)"，或只有基础品牌名如"紫阳"）
        
        Returns:
            str: 布料图的本地文件路径，如果找不到则返回None
        """
        try:
            # 获取该品牌的所有图片（支持模糊匹配）
            brand_images = self.image_service.get_brand_images(brand_name)
            
            if not brand_images:
                logger.warning(f"未找到品牌图片: {brand_name}")
                return None
            
            logger.debug(f"找到 {len(brand_images)} 张品牌图片: {brand_name}")
            
            # 优先查找布料图
            fabric_images = [img for img in brand_images if img.get('image_type') == '布料图']
            
            # 如果找到多个布料图，优先选择与品牌名匹配的（如果品牌名包含颜色）
            if fabric_images:
                # 如果品牌名包含颜色信息，尝试精确匹配
                if '(' in brand_name:
                    exact_match = next(
                        (img for img in fabric_images if img.get('brand_name') == brand_name),
                        None
                    )
                    if exact_match:
                        fabric_image = exact_match
                    else:
                        # 使用第一张布料图
                        fabric_image = fabric_images[0]
                else:
                    # 品牌名没有颜色信息，使用第一张布料图
                    fabric_image = fabric_images[0]
            else:
                fabric_image = None
            
            # 如果没有布料图，使用成衣图作为备选
            if not fabric_image:
                garment_images = [img for img in brand_images if img.get('image_type') == '成衣图']
                if garment_images:
                    # 同样优先匹配颜色
                    if '(' in brand_name:
                        exact_match = next(
                            (img for img in garment_images if img.get('brand_name') == brand_name),
                            None
                        )
                        fabric_image = exact_match if exact_match else garment_images[0]
                    else:
                        fabric_image = garment_images[0]
            
            if not fabric_image:
                logger.warning(f"未找到布料图或成衣图: {brand_name} (共找到{len(brand_images)}张图片)")
                return None
            
            # 获取图片的相对路径
            relative_path = fabric_image.get('relative_path') or fabric_image.get('filename')
            
            if not relative_path:
                logger.warning(f"图片没有相对路径: {brand_name}")
                return None
            
            # 构建完整路径
            fabric_path = os.path.join(self.images_dir, relative_path)
            
            # 检查文件是否存在
            if not os.path.exists(fabric_path):
                logger.warning(f"布料图文件不存在: {fabric_path}")
                return None
            
            logger.info(f"找到布料图: {fabric_path} (品牌: {fabric_image.get('brand_name')})")
            return fabric_path
            
        except Exception as e:
            logger.error(f"获取布料图路径失败: {brand_name}, {e}", exc_info=True)
            return None
    
    def get_task_status(self, task_id: str) -> Dict:
        """
        查询AI试衣任务状态
        
        Args:
            task_id: 任务ID
        
        Returns:
            dict: 包含任务状态和结果信息的字典
        
        Raises:
            ValidationError: 参数验证失败
            ServiceError: AI试衣服务调用失败
        """
        # 参数验证
        if not task_id:
            raise ValidationError(
                message='任务ID不能为空',
                field='task_id'
            )
        
        try:
            # 调用试衣服务查询状态
            result = self.try_on_service.get_task_status(task_id)
            
            return result
            
        except (ValidationError, ServiceError):
            # 重新抛出这些异常，让路由层处理
            raise
        except Exception as e:
            logger.error(f"查询任务状态失败: {e}", exc_info=True)
            raise ServiceError(
                message=f'查询任务状态失败: {str(e)}',
                service_name='TryOnController',
                details={'task_id': task_id, 'error': str(e)}
            )
