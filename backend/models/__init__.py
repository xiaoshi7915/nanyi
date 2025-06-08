#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据模型包
"""

try:
    from flask_sqlalchemy import SQLAlchemy
    # 创建数据库实例
    db = SQLAlchemy()
    
    # 尝试导入模型，如果失败则提供基本功能
    try:
        from .product import Product
        from .admin import Admin
        __all__ = ['db', 'Product', 'Admin']
    except ImportError as e:
        print(f"警告: 模型导入失败 - {e}")
        # 提供基本的数据库对象
        __all__ = ['db']
        
except ImportError as e:
    print(f"错误: Flask-SQLAlchemy导入失败 - {e}")
    # 提供一个空的数据库对象以防止导入错误
    class MockDB:
        def init_app(self, app):
            pass
    
    db = MockDB()
    __all__ = ['db'] 