#!/usr/bin/env python3
"""
添加 prompt 和 negative_prompt 字段到 tasks 表
"""
import sys
import os

# 添加项目路径
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from sqlalchemy import create_engine, text
from app.config import settings
from app.utils.logger import setup_logger, get_logger

logger = setup_logger(level=settings.log_level)


def add_prompt_fields():
    """添加 prompt 字段到 tasks 表"""
    try:
        engine = create_engine(settings.db_url)
        
        with engine.connect() as conn:
            # MySQL 不支持 IF NOT EXISTS，需要先检查
            if settings.db_type.lower() == "mysql":
                # 检查字段是否存在
                check_sql = text("""
                SELECT COUNT(*) as count 
                FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = :db_name 
                AND TABLE_NAME = 'tasks' 
                AND COLUMN_NAME = 'prompt'
                """)
                result = conn.execute(check_sql, {"db_name": settings.db_name})
                row = result.fetchone()
                
                if row and row[0] == 0:
                    # 字段不存在，添加字段
                    conn.execute(text("ALTER TABLE tasks ADD COLUMN prompt TEXT COMMENT '自定义提示词'"))
                    logger.info("添加 prompt 字段成功")
                else:
                    logger.info("prompt 字段已存在，跳过")
                
                # 检查 negative_prompt 字段
                check_sql = text("""
                SELECT COUNT(*) as count 
                FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = :db_name 
                AND TABLE_NAME = 'tasks' 
                AND COLUMN_NAME = 'negative_prompt'
                """)
                result = conn.execute(check_sql, {"db_name": settings.db_name})
                row = result.fetchone()
                
                if row and row[0] == 0:
                    conn.execute(text("ALTER TABLE tasks ADD COLUMN negative_prompt TEXT COMMENT '负面提示词'"))
                    logger.info("添加 negative_prompt 字段成功")
                else:
                    logger.info("negative_prompt 字段已存在，跳过")
                
                conn.commit()
            else:
                # PostgreSQL 和 SQLite 的处理
                try:
                    conn.execute(text("ALTER TABLE tasks ADD COLUMN prompt TEXT"))
                    logger.info("添加 prompt 字段成功")
                except Exception as e:
                    if "already exists" in str(e) or "duplicate" in str(e).lower():
                        logger.info("prompt 字段已存在，跳过")
                    else:
                        raise
                
                try:
                    conn.execute(text("ALTER TABLE tasks ADD COLUMN negative_prompt TEXT"))
                    logger.info("添加 negative_prompt 字段成功")
                except Exception as e:
                    if "already exists" in str(e) or "duplicate" in str(e).lower():
                        logger.info("negative_prompt 字段已存在，跳过")
                    else:
                        raise
                
                conn.commit()
        
        engine.dispose()
        logger.info("✅ 数据库字段更新完成")
        
    except Exception as e:
        logger.error(f"❌ 数据库字段更新失败: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    print("开始添加 prompt 字段到 tasks 表...")
    print(f"数据库类型: {settings.db_type}")
    print(f"数据库地址: {settings.db_host}:{settings.db_port}")
    print(f"数据库名称: {settings.db_name}")
    print()
    
    try:
        add_prompt_fields()
        print("✅ 字段添加成功！")
    except Exception as e:
        print(f"❌ 字段添加失败: {str(e)}")
        sys.exit(1)

