#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库工具函数
"""

import os
from backend.models import db, Admin
from backend.utils.db_connection import get_db_connection

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
        import secrets
        # 生成随机密码，避免使用弱密码
        default_password = secrets.token_urlsafe(16)
        admin = Admin(
            username='admin',
            email='admin@nanyi.com'
        )
        admin.set_password(default_password)
        
        db.session.add(admin)
        db.session.commit()
        
        print(f"默认管理员账户创建成功")
        print(f"用户名: admin")
        print(f"密码: {default_password}")
        print(f"⚠️  请立即登录并修改密码！")
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