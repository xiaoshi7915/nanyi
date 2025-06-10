#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目配置文件
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """基础配置"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'nanyi_secret_key_2024'
    
    # 数据库配置 - 从环境变量读取
    DB_HOST = os.environ.get('DB_HOST') or '47.118.250.53'
    DB_PORT = int(os.environ.get('DB_PORT') or 3306)
    DB_USER = os.environ.get('DB_USER') or 'nanyi'
    DB_PASSWORD = os.environ.get('DB_PASSWORD') or 'admin123456!'
    DB_NAME = os.environ.get('DB_NAME') or 'nanyiqiutang'
    
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 3600,
        'pool_timeout': 10,
        'max_overflow': 20,
        'pool_size': 10,
        'connect_args': {
            'charset': 'utf8mb4',
            'connect_timeout': 10,
            'read_timeout': 10,
            'write_timeout': 10,
            'autocommit': True
        }
    }
    
    # 文件上传配置
    UPLOAD_FOLDER = 'static/images'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
    
    # API配置
    JSON_AS_ASCII = False
    JSONIFY_PRETTYPRINT_REGULAR = True
    
    # CORS配置 - 从环境变量读取
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:8500,http://121.36.205.70:8500').split(',')
    
    # 服务配置 - 从环境变量读取
    BACKEND_PORT = int(os.environ.get('BACKEND_PORT') or 5001)
    FRONTEND_PORT = int(os.environ.get('FRONTEND_PORT') or 8500)
    DOMAIN = os.environ.get('DOMAIN') or 'localhost'
    BACKEND_URL = os.environ.get('BACKEND_URL') or f'http://localhost:{BACKEND_PORT}'
    FRONTEND_URL = os.environ.get('FRONTEND_URL') or f'http://localhost:{FRONTEND_PORT}'

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    def __init__(self):
        super().__init__()
        # 开发环境使用本地数据库或备用配置
        if os.environ.get('USE_LOCAL_DB', 'false').lower() == 'true':
            self.SQLALCHEMY_DATABASE_URI = 'sqlite:///nanyi_dev.db'
    
class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    
    # 生产环境可以添加更严格的CORS配置
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', f'http://{Config.DOMAIN}:8500').split(',')
    
class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

# 配置映射
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
} 