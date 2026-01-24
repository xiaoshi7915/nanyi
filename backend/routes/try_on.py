#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
试衣功能路由
定义AI试衣相关的RESTful API接口
"""

from flask import Blueprint, request
from werkzeug.utils import secure_filename

from backend.controllers.try_on_controller import TryOnController
from backend.utils.decorators import handle_errors
from backend.utils.response import APIResponse
from backend.exceptions import ValidationError

# 创建蓝图
try_on_bp = Blueprint('try_on', __name__, url_prefix='/api/try-on')

# 创建控制器实例
try_on_controller = TryOnController()

# 允许的图片文件扩展名
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp', 'gif', 'bmp'}

# 最大文件大小（20MB，支持AI试衣功能）
MAX_FILE_SIZE = 20 * 1024 * 1024


def allowed_file(filename: str) -> bool:
    """
    检查文件扩展名是否允许
    
    Args:
        filename: 文件名
    
    Returns:
        bool: 是否允许
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@try_on_bp.route('/styles', methods=['GET'])
@handle_errors
def get_styles():
    """
    获取可用的款式列表（品牌+颜色组合）
    
    GET /api/try-on/styles?brand_name=丹若
    
    查询参数:
        brand_name: 可选的基础品牌名，如果提供则只返回该品牌的款式
    
    Returns:
        JSON响应，包含款式列表
    """
    # 获取可选的品牌名参数
    base_brand_name = request.args.get('brand_name')
    
    # 记录请求参数
    from backend.utils.logger import logger
    logger.info(f"获取款式列表请求 - brand_name参数: {base_brand_name}")
    
    # 如果提供了品牌名，提取基础品牌名（去掉颜色信息）
    if base_brand_name:
        # 如果品牌名包含颜色信息，提取基础品牌名
        if '(' in base_brand_name:
            base_brand_name = base_brand_name.split('(')[0].strip()
        logger.info(f"提取的基础品牌名: {base_brand_name}")
    
    # 调用控制器处理业务逻辑
    result = try_on_controller.get_available_styles(base_brand_name=base_brand_name)
    
    # 使用APIResponse统一响应格式
    if result.get('success'):
        return APIResponse.success(
            data={'styles': result.get('styles', [])},
            message='获取款式列表成功'
        )
    else:
        return APIResponse.error(
            message=result.get('error', '获取款式列表失败'),
            status_code=500
        )


@try_on_bp.route('/start', methods=['POST'])
@handle_errors
def start_try_on():
    """
    启动AI试衣任务
    
    POST /api/try-on/start
    请求格式: multipart/form-data
    - brand_name: 选定的款式名称（品牌+颜色，如"丹若(玉绿)"）
    - user_image: 用户上传的照片文件
    
    Returns:
        JSON响应，包含task_id和状态信息
    """
    # 检查请求是否包含文件
    if 'user_image' not in request.files:
        return APIResponse.validation_error(
            message='请上传用户照片',
            field='user_image'
        )
    
    user_image_file = request.files['user_image']
    
    # 检查文件是否为空
    if user_image_file.filename == '':
        return APIResponse.validation_error(
            message='请选择要上传的照片',
            field='user_image'
        )
    
    # 检查文件扩展名
    if not allowed_file(user_image_file.filename):
        return APIResponse.validation_error(
            message=f'不支持的文件格式，仅支持: {", ".join(ALLOWED_EXTENSIONS)}',
            field='user_image',
            value=user_image_file.filename
        )
    
    # 检查文件大小
    user_image_file.seek(0, 2)  # 移动到文件末尾
    file_size = user_image_file.tell()
    user_image_file.seek(0)  # 重置文件指针
    
    if file_size > MAX_FILE_SIZE:
        return APIResponse.validation_error(
            message=f'文件大小超过限制（最大{MAX_FILE_SIZE // 1024 // 1024}MB）',
            field='user_image',
            value=f'{file_size} bytes'
        )
    
    # 获取品牌名称
    brand_name = request.form.get('brand_name')
    if not brand_name:
        return APIResponse.validation_error(
            message='请选择款式（品牌+颜色）',
            field='brand_name'
        )
    
    # 读取文件内容
    try:
        user_image_data = user_image_file.read()
        user_image_filename = secure_filename(user_image_file.filename)
        
        # 调用控制器处理业务逻辑
        result = try_on_controller.start_try_on_task(
            brand_name=brand_name,
            user_image_file=user_image_data,
            user_image_filename=user_image_filename
        )
        
        # 使用APIResponse统一响应格式
        if result.get('success'):
            return APIResponse.success(
                data={
                    'task_id': result.get('task_id'),
                    'status': result.get('status'),
                    'estimated_time': result.get('estimated_time')
                },
                message='试衣任务已启动'
            )
        else:
            return APIResponse.error(
                message=result.get('error', '启动试衣任务失败'),
                status_code=500
            )
            
    except ValidationError as e:
        return APIResponse.validation_error(
            message=e.message,
            field=e.details.get('field'),
            value=e.details.get('value')
        )
    except Exception as e:
        return APIResponse.error(
            message=f'启动试衣任务失败: {str(e)}',
            status_code=500
        )


@try_on_bp.route('/status/<task_id>', methods=['GET'])
@handle_errors
def get_task_status(task_id: str):
    """
    查询AI试衣任务状态
    
    GET /api/try-on/status/<task_id>
    
    Args:
        task_id: 任务ID
    
    Returns:
        JSON响应，包含任务状态和结果信息
    """
    try:
        # 调用控制器处理业务逻辑
        result = try_on_controller.get_task_status(task_id)
        
        # 使用APIResponse统一响应格式
        if result.get('success'):
            return APIResponse.success(
                data={
                    'status': result.get('status'),
                    'result_image_url': result.get('result_image_url'),
                    'progress': result.get('progress', 0),
                    'error': result.get('error')
                },
                message='查询任务状态成功'
            )
        else:
            return APIResponse.error(
                message=result.get('error', '查询任务状态失败'),
                status_code=500
            )
            
    except ValidationError as e:
        return APIResponse.validation_error(
            message=e.message,
            field=e.details.get('field'),
            value=e.details.get('value')
        )
    except ServiceError as e:
        # ServiceError是预期的业务异常，返回友好的错误信息
        from backend.utils.logger import logger
        logger.warning(f"查询任务状态业务异常: {e.message}", exc_info=True)
        return APIResponse.error(
            message=e.message,
            status_code=503,  # 使用503表示服务暂时不可用
            details=e.details
        )
    except Exception as e:
        # 未预期的异常，记录详细日志
        from backend.utils.logger import logger
        logger.error(f"查询任务状态异常: {task_id}", exc_info=True)
        return APIResponse.error(
            message='查询任务状态失败，请稍后重试',
            status_code=500
        )
