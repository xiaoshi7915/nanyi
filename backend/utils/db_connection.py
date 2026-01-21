#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一数据库连接工具模块
避免在多个文件中重复定义数据库连接函数
"""

import os
import pymysql
from backend.config.config import Config

def get_db_connection():
    """
    获取数据库连接（使用pymysql）
    注意：优先使用SQLAlchemy ORM，此函数仅用于特殊场景（如BrandLike模型）
    """
    # 从环境变量读取数据库配置，确保使用统一配置
    host = os.environ.get('DB_HOST')
    port = int(os.environ.get('DB_PORT') or 3306)
    user = os.environ.get('DB_USER')
    password = os.environ.get('DB_PASSWORD')
    database = os.environ.get('DB_NAME')
    
    # 验证必需的配置项
    if not all([host, user, password, database]):
        raise ValueError("数据库配置不完整，请检查环境变量: DB_HOST, DB_USER, DB_PASSWORD, DB_NAME")
    
    return pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        charset='utf8mb4',
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor
    )
