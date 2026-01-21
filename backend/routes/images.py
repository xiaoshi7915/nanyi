#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片相关路由
处理图片相关的API请求
"""

from flask import Blueprint, request, send_file, abort
from backend.controllers.image_controller import ImageController
from backend.utils.logger import log_access
from backend.utils.cache_control import smart_cache
from backend.utils.decorators import handle_errors
from backend.utils.rate_limit import rate_limit
from backend.utils.response import APIResponse
from backend.utils.validators import validate_pagination, validate_boolean
from backend.exceptions import ValidationError

# 创建蓝图
images_bp = Blueprint('images', __name__, url_prefix='/api')

# 创建控制器实例
image_controller = ImageController()


@images_bp.route('/images')
@rate_limit(max_requests=60, per_seconds=60)  # 每分钟最多60次请求
@log_access
@smart_cache
@handle_errors
def get_images():
    """
    获取图片信息，支持分页
    
    查询参数:
    - page: 页码（默认1）
    - per_page: 每页数量（默认12，最大50）
    - load_all: 是否加载所有数据（true/false）
    
    返回:
    - success: 是否成功
    - data: 数据对象
      - brands: 品牌列表
      - pagination: 分页信息
    - total: 总图片数
    """
    # 使用validators模块统一参数验证
    try:
        page, per_page = validate_pagination(max_per_page=50)
        load_all = validate_boolean(request.args.get('load_all'), 'load_all', default=False)
    except ValidationError as e:
        return APIResponse.validation_error(
            message=str(e),
            field=e.details.get('field'),
            value=e.details.get('value')
        )
    
    # 调用控制器处理业务逻辑
    result = image_controller.get_images_with_pagination(
        page=page,
        per_page=per_page,
        load_all=load_all
    )
    
    # 使用APIResponse统一响应格式
    # 注意：为了兼容前端代码，images API直接返回扁平结构，而不是嵌套在data中
    if result.get('success'):
        # 直接返回控制器的数据，保持与前端兼容
        from flask import jsonify
        return jsonify(result), 200
    else:
        return APIResponse.error(
            message=result.get('error', '查询失败'),
            status_code=500
        )


@images_bp.route('/view/<path:filepath>')
@handle_errors
def view_image(filepath):
    """查看图片"""
    import os
    
    # 获取前端静态图片目录
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    project_root = os.path.dirname(current_dir)
    images_dir = os.path.join(project_root, 'frontend', 'static', 'images')
    
    # 构建完整路径
    full_path = os.path.join(images_dir, filepath)
    
    from backend.utils.logger import logger
    logger.debug(f"图片请求: {filepath}")
    logger.debug(f"完整路径: {full_path}")
    logger.debug(f"文件存在: {os.path.exists(full_path)}")
    
    # 检查文件是否存在
    if not os.path.exists(full_path):
        logger.warning(f"文件不存在: {full_path}")
        abort(404)
    
    # 检查文件是否在允许的目录内（安全检查）
    if not os.path.abspath(full_path).startswith(os.path.abspath(images_dir)):
        logger.warning(f"安全检查失败: {full_path}")
        abort(403)
    
    logger.debug(f"返回图片文件: {full_path}")
    return send_file(full_path)


@images_bp.route('/download/<path:filepath>')
@handle_errors
def download_image(filepath):
    """下载图片"""
    from backend.config.config import Config
    import os
    
    # 构建完整路径
    full_path = os.path.join(Config.UPLOAD_FOLDER, filepath)
    
    # 检查文件是否存在
    if not os.path.exists(full_path):
        abort(404)
    
    # 检查文件是否在允许的目录内（安全检查）
    if not os.path.abspath(full_path).startswith(os.path.abspath(Config.UPLOAD_FOLDER)):
        abort(403)
    
    return send_file(full_path, as_attachment=True)
