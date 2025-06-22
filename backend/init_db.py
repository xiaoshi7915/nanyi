#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库初始化脚本
确保所有必要的数据库表都已创建
"""

import sys
import os

# 添加项目路径到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app import create_app
from backend.models import db
from backend.models.product import Product
from backend.models.access_log import AccessLog
from backend.models.admin import Admin
from backend.models.brand_like import BrandLike

def init_database():
    """初始化数据库"""
    print("🔧 开始初始化数据库...")
    
    # 创建应用实例
    app = create_app()
    
    with app.app_context():
        try:
            # 创建所有SQLAlchemy表
            print("📊 创建SQLAlchemy表...")
            db.create_all()
            print("✅ SQLAlchemy表创建成功")
            
            # 创建点赞表（使用原生MySQL）
            print("❤️ 创建点赞表...")
            if BrandLike.create_table():
                print("✅ 点赞表创建成功")
            else:
                print("❌ 点赞表创建失败")
            
            print("🎉 数据库初始化完成！")
            
        except Exception as e:
            print(f"❌ 数据库初始化失败: {e}")
            return False
    
    return True

def check_tables():
    """检查表是否存在"""
    app = create_app()
    
    with app.app_context():
        try:
            # 检查SQLAlchemy表
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            print("📋 当前数据库表:")
            for table in sorted(tables):
                print(f"  ✓ {table}")
            
            # 检查必要表是否存在
            required_tables = ['products', 'access_logs', 'admins', 'brand_likes', 'brand_like_stats']
            missing_tables = [table for table in required_tables if table not in tables]
            
            if missing_tables:
                print(f"⚠️ 缺少表: {', '.join(missing_tables)}")
                return False
            else:
                print("✅ 所有必要表都已存在")
                return True
                
        except Exception as e:
            print(f"❌ 检查表失败: {e}")
            return False

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='数据库初始化工具')
    parser.add_argument('--check', action='store_true', help='检查表是否存在')
    parser.add_argument('--init', action='store_true', help='初始化数据库')
    
    args = parser.parse_args()
    
    if args.check:
        check_tables()
    elif args.init:
        init_database()
    else:
        print("使用 --init 初始化数据库，或 --check 检查表状态") 