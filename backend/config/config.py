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
    
    def __init__(self, config_name='development'):
        """初始化配置，验证必需的环境变量"""
        # 安全配置 - 强制从环境变量读取，不允许默认值
        self.SECRET_KEY = os.environ.get('SECRET_KEY')
        if not self.SECRET_KEY:
            raise ValueError("SECRET_KEY环境变量未设置，请在.env文件中配置")
        
        # 数据库配置 - 强制从环境变量读取，不允许默认值
        self.DB_HOST = os.environ.get('DB_HOST')
        if not self.DB_HOST:
            raise ValueError("DB_HOST环境变量未设置，请在.env文件中配置")
        
        self.DB_PORT = int(os.environ.get('DB_PORT') or 3306)  # 端口号可以使用默认值
        
        self.DB_USER = os.environ.get('DB_USER')
        if not self.DB_USER:
            raise ValueError("DB_USER环境变量未设置，请在.env文件中配置")
        
        self.DB_PASSWORD = os.environ.get('DB_PASSWORD')
        if not self.DB_PASSWORD:
            raise ValueError("DB_PASSWORD环境变量未设置，请在.env文件中配置")
        
        self.DB_NAME = os.environ.get('DB_NAME')
        if not self.DB_NAME:
            raise ValueError("DB_NAME环境变量未设置，请在.env文件中配置")
        
        self.SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4'
        self.SQLALCHEMY_TRACK_MODIFICATIONS = False
        self.SQLALCHEMY_ENGINE_OPTIONS = {
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
        self.UPLOAD_FOLDER = 'static/images'
        self.MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
        self.ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
        
        # OSS配置 - 如果使用OSS，则必须配置
        self.OSS_ACCESS_KEY_ID = os.environ.get('OSS_ACCESS_KEY_ID') or ''
        self.OSS_ACCESS_KEY_SECRET = os.environ.get('OSS_ACCESS_KEY_SECRET') or ''
        self.OSS_ENDPOINT = os.environ.get('OSS_ENDPOINT') or 'oss-cn-hangzhou.aliyuncs.com'  # 端点可以使用默认值
        self.OSS_BUCKET = os.environ.get('OSS_BUCKET') or 'nanyiqiutang'  # 如果使用OSS，建议从环境变量读取
        self.OSS_BASE_URL = f'https://{self.OSS_BUCKET}.{self.OSS_ENDPOINT}'
        
        # 图片源配置 - 支持命令行切换
        # 可选值: 'oss', 'local'
        self.IMAGE_SOURCE = os.environ.get('IMAGE_SOURCE', 'local').lower()
        
        # 图片处理参数
        self.OSS_THUMBNAIL_PARAMS = '?x-oss-process=image/resize,w_300,h_300,m_lfit/quality,q_80/format,webp'
        self.OSS_MEDIUM_PARAMS = '?x-oss-process=image/resize,w_800,h_800,m_lfit/quality,q_90/format,webp'
        
        # API配置
        self.JSON_AS_ASCII = False
        self.JSONIFY_PRETTYPRINT_REGULAR = True
        
        # CORS配置 - 强制从环境变量读取，仅允许HTTPS域名
        cors_origins_str = os.environ.get('CORS_ORIGINS')
        if not cors_origins_str:
            raise ValueError("CORS_ORIGINS环境变量未设置，请在.env文件中配置允许的HTTPS域名")
        
        # 验证所有域名必须是HTTPS（开发环境localhost和IP地址除外）
        self.CORS_ORIGINS = []
        for origin in cors_origins_str.split(','):
            origin = origin.strip()
            if origin:
                # 允许localhost和127.0.0.1用于开发环境
                if origin.startswith('http://localhost') or origin.startswith('http://127.0.0.1'):
                    self.CORS_ORIGINS.append(origin)
                # 允许IP地址用于开发环境（临时方案）
                elif origin.startswith('http://') and any(char.isdigit() for char in origin.split('://')[1].split(':')[0]):
                    # IP地址格式，允许HTTP（仅用于开发环境）
                    if config_name == 'development':
                        self.CORS_ORIGINS.append(origin)
                        import warnings
                        warnings.warn(f"开发环境允许HTTP IP地址: {origin}，生产环境应使用HTTPS域名")
                    else:
                        raise ValueError(f"生产环境CORS域名必须使用HTTPS: {origin}")
                elif origin.startswith('https://'):
                    self.CORS_ORIGINS.append(origin)
                else:
                    raise ValueError(f"CORS域名格式不正确: {origin}（必须使用HTTPS或localhost）")
        
        # 服务配置 - 从环境变量读取（端口和域名可以使用默认值）
        self.BACKEND_PORT = int(os.environ.get('BACKEND_PORT') or 5432)
        self.FRONTEND_PORT = int(os.environ.get('FRONTEND_PORT') or 8500)
        self.DOMAIN = os.environ.get('DOMAIN') or 'localhost'
        self.BACKEND_URL = os.environ.get('BACKEND_URL') or f'http://localhost:{self.BACKEND_PORT}'
        self.FRONTEND_URL = os.environ.get('FRONTEND_URL') or f'http://localhost:{self.FRONTEND_PORT}'
        
        # CSRF保护配置
        self.WTF_CSRF_ENABLED = True
        self.WTF_CSRF_TIME_LIMIT = 3600  # CSRF token有效期1小时

class DevelopmentConfig(Config):
    """开发环境配置"""
    
    def __init__(self, config_name='development'):
        super().__init__(config_name=config_name)
        self.DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
        # 开发环境使用本地数据库或备用配置
        if os.environ.get('USE_LOCAL_DB', 'false').lower() == 'true':
            self.SQLALCHEMY_DATABASE_URI = 'sqlite:///nanyi_dev.db'
    
class ProductionConfig(Config):
    """生产环境配置"""
    
    # 生产环境强制使用HTTPS域名
    def __init__(self, config_name='production'):
        super().__init__(config_name=config_name)
        self.DEBUG = False
        # 生产环境不允许HTTP域名（包括localhost）
        cors_origins_str = os.environ.get('CORS_ORIGINS')
        if cors_origins_str:
            self.CORS_ORIGINS = []
            for origin in cors_origins_str.split(','):
                origin = origin.strip()
                if origin:
                    # 生产环境不允许HTTP（包括localhost）
                    if origin.startswith('https://'):
                        self.CORS_ORIGINS.append(origin)
                    else:
                        raise ValueError(f"生产环境CORS域名必须使用HTTPS: {origin}")
        else:
            raise ValueError("生产环境必须配置CORS_ORIGINS环境变量")
    
class TestingConfig(Config):
    """测试环境配置"""
    
    def __init__(self):
        super().__init__()
        self.TESTING = True
        self.SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

# 配置映射
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
} 