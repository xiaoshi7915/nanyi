#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加性能优化索引
"""

import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from backend.app import create_app
from backend.models import db

def add_indexes():
    """添加性能优化索引"""
    app = create_app()
    
    with app.app_context():
        try:
            # 检查索引是否已存在，如果不存在则创建
            indexes_to_create = [
                ("idx_product_brand_year", "products", "brand_name, year"),
                ("idx_product_year_month", "products", "year, publish_month"),
                ("idx_product_material", "products", "material"),
                ("idx_product_theme", "products", "theme_series"),
                ("idx_product_print_size", "products", "print_size"),
            ]
            
            created_count = 0
            for index_name, table_name, columns in indexes_to_create:
                try:
                    # 检查索引是否存在
                    result = db.session.execute(
                        f"SHOW INDEX FROM {table_name} WHERE Key_name = '{index_name}'"
                    )
                    if result.fetchone():
                        print(f"✅ 索引 {index_name} 已存在")
                        continue
                    
                    # 创建索引
                    db.session.execute(
                        f"CREATE INDEX {index_name} ON {table_name}({columns})"
                    )
                    created_count += 1
                    print(f"✅ 创建索引: {index_name}")
                except Exception as e:
                    print(f"⚠️  索引 {index_name} 创建失败（可能已存在）: {e}")
            
            db.session.commit()
            print(f"\n✅ 索引创建完成，共创建 {created_count} 个索引")
            return True
            
        except Exception as e:
            print(f"❌ 创建索引失败: {e}")
            db.session.rollback()
            return False

if __name__ == '__main__':
    add_indexes()
