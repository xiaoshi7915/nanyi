#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据模型测试
"""

import pytest
from backend.models.admin import Admin
from backend.models.product import Product
from datetime import datetime

def test_admin_password_strength(app):
    """测试管理员密码强度验证"""
    admin = Admin(username='test', email='test@test.com')
    
    # 测试弱密码
    with pytest.raises(ValueError, match="密码强度不足"):
        admin.set_password('weak')
    
    # 测试强密码
    admin.set_password('StrongP@ss123')
    assert admin.password_hash is not None
    assert admin.password_changed_at is not None

def test_admin_check_password(app):
    """测试密码验证"""
    admin = Admin(username='test', email='test@test.com')
    admin.set_password('StrongP@ss123')
    
    assert admin.check_password('StrongP@ss123') == True
    assert admin.check_password('wrong') == False

def test_product_model(app):
    """测试产品模型"""
    product = Product(
        brand_name='测试品牌',
        year=2024,
        material='棉麻',
        theme_series='经典系列'
    )
    
    assert product.brand_name == '测试品牌'
    assert product.year == 2024
    assert product.material == '棉麻'

def test_product_to_dict(app):
    """测试产品转字典"""
    product = Product(
        brand_name='测试品牌',
        year=2024
    )
    
    data = product.to_dict()
    assert 'brand_name' in data
    assert 'year' in data
    assert data['brand_name'] == '测试品牌'
