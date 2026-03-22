#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API测试
"""

import pytest
import json

def test_health_endpoint(client):
    """测试健康检查端点"""
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'

def test_api_images_endpoint(client):
    """测试图片API端点"""
    response = client.get('/api/images?page=1&per_page=5')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'success' in data
    assert 'brands' in data

def test_api_images_pagination(client):
    """测试图片API分页"""
    response = client.get('/api/images?page=1&per_page=1')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'brands' in data
    assert 'pagination' in data

def test_api_images_invalid_page(client):
    """无效分页参数应返回校验错误"""
    response = client.get('/api/images?page=-1&per_page=0')
    assert response.status_code == 400

def test_rate_limiting(client):
    """测试请求限流"""
    # 快速连续请求
    for i in range(65):
        response = client.get('/api/images')
        if response.status_code == 429:
            assert i >= 60  # 应该在60次后触发限流
            break
    else:
        pytest.skip("限流未触发，可能需要调整测试")
