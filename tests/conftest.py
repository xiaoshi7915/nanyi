#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pytest配置文件
"""

import pytest
import os
import sys

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from backend.app import create_app
from backend.models import db

@pytest.fixture
def app():
    """创建测试应用"""
    import os
    # 设置测试环境变量
    os.environ['SECRET_KEY'] = 'test-secret-key-for-pytest'
    os.environ['DB_HOST'] = 'localhost'
    os.environ['DB_USER'] = 'test'
    os.environ['DB_PASSWORD'] = 'test'
    os.environ['DB_NAME'] = 'test_db'
    os.environ['CORS_ORIGINS'] = 'http://localhost:8500'
    
    app = create_app('testing')
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """创建CLI测试运行器"""
    return app.test_cli_runner()
