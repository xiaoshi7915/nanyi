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
        return Product, Admin
    except ImportError as e:
        print(f"警告: 模型导入失败 - {e}")
        return None, None

# 延迟导入，避免循环依赖
Product = None
Admin = None

__all__ = ['db', 'Product', 'Admin', 'init_models'] 