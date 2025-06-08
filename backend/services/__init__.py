#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务层包
"""

try:
    from .image_service import ImageService
    from .product_service import ProductService
    __all__ = ['ImageService', 'ProductService']
except ImportError as e:
    print(f"警告: 服务导入失败 - {e}")
    # 提供空的服务类以防止导入错误
    class ImageService:
        pass
    
    class ProductService:
        pass
    
    __all__ = ['ImageService', 'ProductService'] 