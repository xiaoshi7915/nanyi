#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具函数包
统一导入常用工具函数和装饰器
"""

from .file_utils import *
from .db_utils import *

# 统一从decorators模块导入装饰器，避免重复定义
try:
    from .decorators import (
        handle_errors,
        require_json,
        validate_params,
        cache_response
    )
except ImportError:
    # 如果decorators模块导入失败，记录警告但不定义回退代码
    # 这样可以确保在开发阶段及时发现导入问题
    import logging
    logger = logging.getLogger(__name__)
    logger.warning("无法导入decorators模块，请检查模块是否正确安装")
    
    # 不定义回退装饰器，强制使用decorators.py中的实现
    handle_errors = None
    require_json = None
    validate_params = None
    cache_response = None

__all__ = [
    # 文件工具函数
    'allowed_file', 'parse_filename', 'secure_filename_custom',
    # 数据库工具函数
    'init_database', 'create_default_admin',
    # 装饰器（统一从decorators模块导入）
    'handle_errors', 'require_json', 'validate_params', 'cache_response'
] 