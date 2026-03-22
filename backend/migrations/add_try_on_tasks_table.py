#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加 try_on tasks 表迁移脚本
在主项目数据库中创建 tasks 表，用于存储试衣生成任务
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
from sqlalchemy import text


def add_try_on_tasks_table():
    """创建 try_on tasks 表"""
    app = create_app()
    
    with app.app_context():
        try:
            # 检查表是否已存在
            result = db.session.execute(
                text("SHOW TABLES LIKE 'tasks'")
            )
            if result.fetchone():
                print("✅ tasks 表已存在，跳过创建")
                return True
            
            # 创建 tasks 表的 SQL（MySQL 版本）
            create_tasks_table_sql = """
            CREATE TABLE IF NOT EXISTS tasks (
                id VARCHAR(36) PRIMARY KEY COMMENT '任务ID',
                access_token VARCHAR(64) NULL COMMENT '试衣任务访问令牌',
                status VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT '任务状态：pending, processing, completed, failed',
                model_type VARCHAR(10) NOT NULL COMMENT '模特类型：ai, real',
                shot_type VARCHAR(20) NOT NULL COMMENT '拍摄类型：full_body, half_body',
                aspect_ratio VARCHAR(10) NOT NULL COMMENT '图像比例：9:16, 16:9, 1:1',
                style VARCHAR(50) DEFAULT 'portrait_photography' COMMENT '风格',
                resolution VARCHAR(20) COMMENT '分辨率',
                ai_model_id VARCHAR(50) COMMENT 'AI模特ID',
                prompt TEXT COMMENT '自定义提示词',
                result_image_url TEXT COMMENT '生成图片OSS URL',
                local_path TEXT COMMENT '本地存储路径',
                error_message TEXT COMMENT '错误信息',
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                INDEX idx_status (status),
                INDEX idx_created_at (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='试衣生成任务表';
            """
            
            # 执行创建表的 SQL
            db.session.execute(text(create_tasks_table_sql))
            db.session.commit()
            
            print("✅ tasks 表创建成功")
            return True
            
        except Exception as e:
            print(f"❌ 创建 tasks 表失败: {e}")
            db.session.rollback()
            import traceback
            traceback.print_exc()
            return False


if __name__ == '__main__':
    print("开始创建 try_on tasks 表...")
    print()
    
    if add_try_on_tasks_table():
        print("\n✅ 数据库迁移完成！")
    else:
        print("\n❌ 数据库迁移失败！")
        sys.exit(1)
