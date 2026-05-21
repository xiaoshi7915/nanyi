#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
试衣控制器
处理AI试衣相关的业务逻辑，包括获取款式列表、启动试衣任务、查询任务状态等
"""

import os
import re
from typing import Dict, List, Optional, TYPE_CHECKING
from flask import request, current_app
from werkzeug.datastructures import FileStorage

from backend.services.image_service import ImageService

if TYPE_CHECKING:
    from backend.services.try_on_image_service import TryOnImageService
from backend.utils.logger import logger
from backend.exceptions import ValidationError, NotFoundError, ServiceError


class TryOnController:
    """试衣控制器类"""
    
    def __init__(self):
        """初始化试衣控制器"""
        # 使用集成的 TryOnImageService（不再使用 HTTP 调用的 TryOnService）
        # 注意：TryOnImageService 需要在应用上下文中初始化，这里延迟初始化
        self._try_on_image_service: Optional["TryOnImageService"] = None
        self.image_service = ImageService()
        
        # 获取图片目录路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        self.images_dir = os.path.join(project_root, 'frontend', 'static', 'images')
    
    def _get_try_on_service(self) -> "TryOnImageService":
        """
        获取 TryOnImageService 实例（从应用对象获取已初始化的实例）
        
        Returns:
            TryOnImageService 实例
        
        Raises:
            ServiceError: 如果服务未初始化
        """
        if self._try_on_image_service is None:
            # 从应用对象获取已初始化的服务实例（在 app.py 中初始化）
            if hasattr(current_app, 'try_on_image_service') and current_app.try_on_image_service is not None:
                self._try_on_image_service = current_app.try_on_image_service
                logger.debug("使用应用已初始化的 TryOnImageService 实例")
            else:
                # 如果应用中没有初始化，抛出异常
                error_msg = "TryOnImageService 未在应用启动时初始化，请检查应用启动日志"
                logger.error(error_msg)
                raise ServiceError(
                    message=error_msg,
                    service_name='TryOnController',
                    details={'hint': 'TryOnImageService 应该在 app.py 的 create_app 函数中初始化'}
                )
        return self._try_on_image_service
    
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
                    # 获取该款式的预览图（设计图/概念图按数量择优，见 _get_preview_image_for_brand）
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
    
    def _resolve_image_type(self, img: Dict) -> str:
        """
        解析图片类型（与前端 getCategorizedImages 逻辑一致）。
        优先使用 image_type 字段，缺失时从文件名推断。
        """
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
        return '其他'

    def _pick_first_by_filename(self, images: List[Dict]) -> Optional[Dict]:
        """从列表中按文件名排序后取第一张代表图。"""
        if not images:
            return None
        return sorted(images, key=lambda x: x.get('filename') or '')[0]

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
            
            # 款式卡片预览：在「设计图」与「概念图」中选数量更多的类型；并列时优先设计图
            design_images = [
                img for img in brand_images if self._resolve_image_type(img) == '设计图'
            ]
            concept_images = [
                img for img in brand_images if self._resolve_image_type(img) == '概念图'
            ]
            design_count = len(design_images)
            concept_count = len(concept_images)

            preview_image = None
            if design_count > 0 or concept_count > 0:
                if design_count > concept_count:
                    preview_image = self._pick_first_by_filename(design_images)
                elif concept_count > design_count:
                    preview_image = self._pick_first_by_filename(concept_images)
                else:
                    # 数量相同：优先设计图，若无则概念图
                    preview_image = self._pick_first_by_filename(
                        design_images if design_images else concept_images
                    )

            # 兜底：布料图 -> 成衣图 -> 任意第一张
            if not preview_image:
                for fallback_type in ('布料图', '成衣图'):
                    candidates = [
                        img for img in brand_images
                        if self._resolve_image_type(img) == fallback_type
                    ]
                    preview_image = self._pick_first_by_filename(candidates)
                    if preview_image:
                        break

            if not preview_image:
                preview_image = self._pick_first_by_filename(brand_images)
            
            # 返回图片URL
            if preview_image.get('url'):
                return preview_image['url']
            elif preview_image.get('relative_path'):
                return f"/static/images/{preview_image['relative_path']}"
            elif preview_image.get('filename'):
                return f"/static/images/{preview_image['filename']}"
            
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
        启动AI试衣任务（使用集成的服务，不再使用 HTTP 调用）
        
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
            
            # 获取集成的试衣服务实例
            try_on_service = self._get_try_on_service()
            
            # 读取布料图文件
            with open(fabric_image_path, 'rb') as f:
                fabric_image_data = f.read()
            
            # 创建 FileStorage 对象（模拟 Flask 上传文件对象）
            from io import BytesIO
            fabric_file = FileStorage(
                stream=BytesIO(fabric_image_data),
                filename=os.path.basename(fabric_image_path),
                content_type='image/jpeg'
            )
            user_image_file_obj = FileStorage(
                stream=BytesIO(user_image_file),
                filename=user_image_filename,
                content_type='image/jpeg'
            )
            
            # 调用集成的试衣服务创建任务
            # 使用固定参数（与原来的 TryOnService 保持一致）
            fixed_prompt = (os.getenv("TRY_ON_FIXED_PROMPT") or "").strip()
            # 固定图生图 prompt：若环境变量未配置，则传空字符串，后端会回退到原有模板逻辑。
            task_id, access_token = try_on_service.create_task(
                fabric_images=[fabric_file],  # 布料图列表
                model_type='real',  # 使用真人照片
                shot_type='half_body',  # 注意：真人图模式会强制生成全身照，但API需要这个参数
                aspect_ratio='9:16',  # 竖屏，适合手机
                style='portrait_photography',  # 人像摄影风格
                real_person_image=user_image_file_obj,  # 用户上传的真人照片
                prompt=fixed_prompt,  # 图生图固定 prompt（来自环境变量）
                model_provider='seedream'  # 模型提供商
            )
            
            logger.info(f"AI试衣任务创建成功: task_id={task_id}")
            
            return {
                'success': True,
                'task_id': task_id,
                'access_token': access_token,
                'status': 'processing',  # 任务初始回传为 processing，避免前端只显示 processing 的情况
                'estimated_time': 10  # 预计处理时间（秒）
            }
            
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
            
            # 按优先级选择参考图：设计图 -> 布料图 -> 成衣图
            # 注意：函数名仍保留为 _get_fabric_image_path，但实际返回的是“参考图”的本地路径。
            fabric_image = None
            type_priority = ['设计图', '布料图', '成衣图']
            
            for image_type in type_priority:
                images_of_type = [img for img in brand_images if img.get('image_type') == image_type]
                if not images_of_type:
                    continue
                
                # 如果品牌名包含颜色信息，尝试精确匹配到同一颜色变体
                if '(' in brand_name:
                    exact_match = next(
                        (img for img in images_of_type if img.get('brand_name') == brand_name),
                        None
                    )
                    if exact_match:
                        fabric_image = exact_match
                    else:
                        # 精确匹配失败时，使用该类型下的第一张作为兜底
                        fabric_image = images_of_type[0]
                else:
                    # 品牌名不含颜色信息时，直接取该类型下第一张
                    fabric_image = images_of_type[0]
                
                # 找到就跳出循环，保证优先级生效
                break
            
            if not fabric_image:
                logger.warning(f"未找到参考图（设计图/布料图/成衣图）: {brand_name} (共找到{len(brand_images)}张图片)")
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
    
    def get_task_status(self, task_id: str, access_token: Optional[str] = None) -> Dict:
        """
        查询AI试衣任务状态（使用集成的服务，从本地数据库查询）
        
        Args:
            task_id: 任务ID
            access_token: 创建任务时返回的访问令牌（必填，通过 query 或调用方传入）
        
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
            # 获取集成的试衣服务实例
            logger.debug(f"查询任务状态: task_id={task_id}")
            try_on_service = self._get_try_on_service()
            
            # 从本地数据库查询任务状态（不再调用外部 HTTP 服务）
            task_dict = try_on_service.get_task_status(task_id, access_token)
            
            # 转换状态格式以兼容原有 API 响应格式
            status = task_dict.get('status', 'pending')
            result_image_url = task_dict.get('result_image_url')
            error_message = task_dict.get('error_message')
            
            # 计算进度（根据状态估算）
            if status == 'completed':
                progress = 100
            elif status == 'processing':
                progress = 50  # 处理中，估算为50%
            elif status == 'failed':
                progress = 0
            else:
                progress = 0  # pending 状态
            
            logger.debug(f"任务状态查询成功: task_id={task_id}, status={status}")
            return {
                'success': True,
                'status': status,
                'result_image_url': result_image_url,
                'progress': progress,
                'error': error_message
            }
            
        except NotFoundError:
            # NotFoundError 直接重新抛出
            raise
        except ValidationError:
            # ValidationError 直接重新抛出
            raise
        except ServiceError:
            # ServiceError 直接重新抛出
            raise
        except Exception as e:
            # 检查是否是任务不存在的异常
            error_msg = str(e).lower()
            error_type = type(e).__name__
            if 'not found' in error_msg or '不存在' in error_msg or 'TaskNotFoundError' in error_type or 'NotFoundError' in error_type:
                logger.warning(f"任务不存在: task_id={task_id}, error={str(e)}")
                raise NotFoundError(
                    message=f'任务不存在: {task_id}',
                    resource_type='task',
                    resource_id=task_id
                )
            # 其他未知异常
            logger.error(f"查询任务状态失败: task_id={task_id}, error={str(e)}", exc_info=True)
            raise ServiceError(
                message=f'查询任务状态失败: {str(e)}',
                service_name='TryOnController',
                details={'task_id': task_id, 'error': str(e)}
            )
