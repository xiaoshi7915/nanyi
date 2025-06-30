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
        'pool_recycle': 7200,  # 2小时回收连接
        'pool_timeout': 20,    # 增加连接池超时
        'max_overflow': 30,    # 增加溢出连接数
        'pool_size': 15,       # 增加连接池大小
        'echo': False,         # 关闭SQL日志（生产环境）
        'connect_args': {
            'charset': 'utf8mb4',
            'connect_timeout': 15,
            'read_timeout': 30,
            'write_timeout': 30,
            'autocommit': False,  # 改为False以支持事务
            'sql_mode': 'TRADITIONAL',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'"
        }
    }
    
    # 文件上传配置
    UPLOAD_FOLDER = 'static/images'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
    
    # OSS配置
    OSS_ACCESS_KEY_ID = os.environ.get('OSS_ACCESS_KEY_ID') or ''
    OSS_ACCESS_KEY_SECRET = os.environ.get('OSS_ACCESS_KEY_SECRET') or ''
    OSS_ENDPOINT = os.environ.get('OSS_ENDPOINT') or 'oss-cn-hangzhou.aliyuncs.com'
    OSS_BUCKET = os.environ.get('OSS_BUCKET') or 'nanyiqiutang'
    OSS_BASE_URL = f'https://{OSS_BUCKET}.{OSS_ENDPOINT}'
    
    # 图片源配置 - 支持命令行切换
    # 可选值: 'oss', 'local'
    IMAGE_SOURCE = os.environ.get('IMAGE_SOURCE', 'local').lower()
    
    # 图片处理参数
    OSS_THUMBNAIL_PARAMS = '?x-oss-process=image/resize,w_300,h_300,m_lfit/quality,q_80/format,webp'
    OSS_MEDIUM_PARAMS = '?x-oss-process=image/resize,w_800,h_800,m_lfit/quality,q_90/format,webp'
    
    # API配置
    JSON_AS_ASCII = False
    JSONIFY_PRETTYPRINT_REGULAR = True
    
    # CORS配置 - 从环境变量读取
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:8500,http://121.36.205.70:8500,http://chenxiaoshivivid.com.cn:8500,http://www.chenxiaoshivivid.com.cn:8500').split(',')
    
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
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', f'http://{Config.DOMAIN}:8500,http://www.{Config.DOMAIN}:8500').split(',')
    
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