#!/usr/bin/env python3
"""
从 tasks 表移除 negative_prompt 字段
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


def remove_negative_prompt_field():
    """从 tasks 表移除 negative_prompt 字段"""
    try:
        engine = create_engine(settings.db_url)
        
        with engine.connect() as conn:
            # 检查字段是否存在
            if settings.db_type.lower() == "mysql":
                check_sql = text("""
                SELECT COUNT(*) as count 
                FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = :db_name 
                AND TABLE_NAME = 'tasks' 
                AND COLUMN_NAME = 'negative_prompt'
                """)
                result = conn.execute(check_sql, {"db_name": settings.db_name})
                row = result.fetchone()
                
                if row and row[0] > 0:
                    # 字段存在，删除字段
                    conn.execute(text("ALTER TABLE tasks DROP COLUMN negative_prompt"))
                    logger.info("移除 negative_prompt 字段成功")
                else:
                    logger.info("negative_prompt 字段不存在，跳过")
                
                conn.commit()
            else:
                # PostgreSQL 和 SQLite 的处理
                try:
                    conn.execute(text("ALTER TABLE tasks DROP COLUMN negative_prompt"))
                    logger.info("移除 negative_prompt 字段成功")
                    conn.commit()
                except Exception as e:
                    if "does not exist" in str(e) or "no such column" in str(e).lower():
                        logger.info("negative_prompt 字段不存在，跳过")
                    else:
                        raise
        
        engine.dispose()
        logger.info("✅ 数据库字段移除完成")
        
    except Exception as e:
        logger.error(f"❌ 数据库字段移除失败: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    print("开始移除 negative_prompt 字段...")
    print(f"数据库类型: {settings.db_type}")
    print(f"数据库地址: {settings.db_host}:{settings.db_port}")
    print(f"数据库名称: {settings.db_name}")
    print()
    
    try:
        remove_negative_prompt_field()
        print("✅ 字段移除成功！")
    except Exception as e:
        print(f"❌ 字段移除失败: {str(e)}")
        sys.exit(1)

