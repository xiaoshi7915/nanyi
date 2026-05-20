#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建 brand_reviews 表（品牌评价）
运行: products_env/bin/python backend/migrations/add_brand_reviews_table.py
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from backend.models.brand_review import BrandReview


def main():
    ok = BrandReview.create_table()
    if ok:
        print("✅ brand_reviews 表已就绪")
        return 0
    print("❌ brand_reviews 表创建失败")
    return 1


if __name__ == "__main__":
    sys.exit(main())
