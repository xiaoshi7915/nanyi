#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为 tasks 表增加 access_token 列（试衣任务按任务鉴权）
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from backend.app import create_app
from backend.models import db
from sqlalchemy import text


def add_access_token_column():
    app = create_app()
    with app.app_context():
        try:
            r = db.session.execute(text(
                "SELECT COUNT(*) FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'tasks' AND COLUMN_NAME = 'access_token'"
            ))
            if r.scalar():
                print("✅ tasks.access_token 列已存在，跳过")
                return True
            db.session.execute(text(
                "ALTER TABLE tasks ADD COLUMN access_token VARCHAR(64) NULL "
                "COMMENT '试衣任务访问令牌' AFTER id"
            ))
            db.session.commit()
            print("✅ 已添加 tasks.access_token 列")
            return True
        except Exception as e:
            print(f"❌ 迁移失败: {e}")
            db.session.rollback()
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    if not add_access_token_column():
        sys.exit(1)
