#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据模型包
"""

from flask_sqlalchemy import SQLAlchemy

# 创建数据库实例
db = SQLAlchemy()

# 导入所有模型 - 在数据库实例创建后导入
def init_models():
    """初始化模型，避免循环导入"""
    try:
        from .product import Product
        from .admin import Admin
        from .access_log import AccessLog
        return Product, Admin, AccessLog
    except ImportError as e:
        # 延迟导入logger，避免循环导入
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"警告: 模型导入失败 - {e}")
        return None, None, None

# 延迟导入，避免循环依赖
Product = None
Admin = None
AccessLog = None

from .user import (
    User,
    OAuthBinding,
    UserAsset,
    UserBrowseEvent,
    UserLoginEvent,
    PasswordResetToken,
)

__all__ = [
    'db',
    'Product',
    'Admin',
    'AccessLog',
    'User',
    'OAuthBinding',
    'UserAsset',
    'UserBrowseEvent',
    'UserLoginEvent',
    'PasswordResetToken',
    'init_models',
]
 