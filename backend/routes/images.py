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
from backend.config.config import Config

# 创建蓝图
images_bp = Blueprint('images', __name__, url_prefix='/api')

# 创建控制器实例
image_controller = ImageController()

# 允许通过 view/download 返回的图片扩展名（与试衣上传白名单对齐）
_ALLOWED_IMAGE_EXT = {'jpg', 'jpeg', 'png', 'webp', 'gif', 'bmp'}


def _unsafe_path_component(filepath: str) -> bool:
    """检测路径穿越或非法分段（不依赖 realpath 前的粗略过滤）。"""
    if filepath is None or filepath.strip() == '':
        return True
    norm = filepath.replace('\\', '/').strip()
    if norm.startswith('/'):
        return True
    for part in norm.split('/'):
        if part == '..' or part == '':
            return True
    return False


def _resolve_safe_file_under_dir(base_dir: str, filepath: str):
    """
    将 filepath 解析为 base_dir 下的真实文件路径；含 realpath 与目录边界校验，防护 symlink 逃逸。
    不合法或不存在时返回 None。
    """
    import os

    if _unsafe_path_component(filepath):
        return None
    if not os.path.isdir(base_dir):
        return None
    base_real = os.path.realpath(base_dir)
    joined = os.path.join(base_dir, filepath)
    full_real = os.path.realpath(joined)
    if full_real == base_real:
        return None
    if not full_real.startswith(base_real + os.sep):
        return None
    if not os.path.isfile(full_real):
        return None
    ext = os.path.splitext(full_real)[1].lstrip('.').lower()
    if ext not in _ALLOWED_IMAGE_EXT:
        return None
    return full_real


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

    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    project_root = os.path.dirname(current_dir)
    images_dir = os.path.join(project_root, 'frontend', 'static', 'images')

    from backend.utils.logger import logger
    logger.debug("图片请求(view): %s", filepath)

    full_path = _resolve_safe_file_under_dir(images_dir, filepath)
    if not full_path:
        logger.warning("图片 view 拒绝或不存在: filepath=%s", filepath)
        abort(404)

    logger.debug("返回图片文件: %s", full_path)
    return send_file(full_path)


@images_bp.route('/download/<path:filepath>')
@handle_errors
def download_image(filepath):
    """下载图片"""
    import os

    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    project_root = os.path.dirname(current_dir)
    upload_dir = os.path.join(project_root, Config.UPLOAD_FOLDER)

    from backend.utils.logger import logger
    logger.debug("图片请求(download): %s", filepath)

    full_path = _resolve_safe_file_under_dir(upload_dir, filepath)
    if not full_path:
        abort(404)

    return send_file(full_path, as_attachment=True)
