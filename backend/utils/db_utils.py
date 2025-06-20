#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库工具函数
"""

import pymysql
import os
from backend.models import db, Admin

def get_db_connection():
    """获取数据库连接"""
    # 使用和config.py相同的数据库配置
    host = os.environ.get('DB_HOST', '47.118.250.53')
    port = int(os.environ.get('DB_PORT', 3306))
    user = os.environ.get('DB_USER', 'nanyi')
    password = os.environ.get('DB_PASSWORD', 'admin123456!')
    database = os.environ.get('DB_NAME', 'nanyiqiutang')
    
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

def init_database(app):
    """初始化数据库"""
    with app.app_context():
        try:
            # 创建所有表
            db.create_all()
            print("数据库表创建成功")
            return True
        except Exception as e:
            print(f"数据库初始化失败: {str(e)}")
            return False

def create_default_admin():
    """创建默认管理员账户"""
    try:
        # 检查是否已有管理员
        if Admin.query.first():
            print("管理员账户已存在")
            return False
        
        # 创建默认管理员
        admin = Admin(
            username='admin',
            email='admin@nanyi.com'
        )
        admin.set_password('admin123')
        
        db.session.add(admin)
        db.session.commit()
        
        print("默认管理员账户创建成功: admin/admin123")
        return True
        
    except Exception as e:
        db.session.rollback()
        print(f"创建管理员账户失败: {str(e)}")
        return False

def check_database_connection():
    """检查数据库连接"""
    try:
        # 尝试执行简单查询
        db.session.execute('SELECT 1')
        return True
    except Exception as e:
        print(f"数据库连接失败: {str(e)}")
        return False

def get_database_stats():
    """获取数据库统计信息"""
    try:
        from backend.models import Product
        
        stats = {
            'total_products': Product.query.count(),
            'featured_products': Product.query.filter_by(is_featured=True).count(),
            'active_products': Product.query.filter_by(state='active').count(),
            'total_admins': Admin.query.filter_by(is_active=True).count()
        }
        
        # 按年份统计
        year_stats = db.session.query(
            Product.year,
            db.func.count(Product.id).label('count')
        ).filter(Product.year.isnot(None)).group_by(Product.year).all()
        
        stats['year_distribution'] = {year: count for year, count in year_stats}
        
        # 按主题系列统计
        theme_stats = db.session.query(
            Product.theme_series,
            db.func.count(Product.id).label('count')
        ).filter(Product.theme_series.isnot(None)).group_by(Product.theme_series).all()
        
        stats['theme_distribution'] = {theme: count for theme, count in theme_stats}
        
        return stats
        
    except Exception as e:
        print(f"获取统计信息失败: {str(e)}")
        return {} 