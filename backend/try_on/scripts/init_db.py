"""
数据库初始化脚本
创建必要的数据库表结构
"""
import sys
import os

# 添加项目根目录到路径
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
project_root = os.path.dirname(backend_dir)
sys.path.insert(0, backend_dir)

# 确保可以导入.env文件
os.chdir(project_root)

from sqlalchemy import create_engine, text
from app.config import settings
from app.utils.logger import setup_logger, get_logger

# 设置日志
logger = setup_logger(level=settings.log_level)


def init_database():
    """
    初始化数据库
    创建必要的表结构
    """
    try:
        # 创建数据库连接（不指定数据库名，用于创建数据库）
        if settings.db_type.lower() == "mysql":
            # MySQL需要先连接到mysql系统数据库
            admin_url = f"mysql+pymysql://{settings.db_user}:{settings.db_password}@{settings.db_host}:{settings.db_port}/mysql"
        elif settings.db_type.lower() == "postgresql":
            # PostgreSQL连接到默认数据库
            admin_url = f"postgresql://{settings.db_user}:{settings.db_password}@{settings.db_host}:{settings.db_port}/postgres"
        else:
            # SQLite不需要创建数据库
            logger.info("SQLite数据库，跳过数据库创建步骤")
            return
        
        admin_engine = create_engine(admin_url)
        
        # 创建数据库（如果不存在）
        with admin_engine.connect() as conn:
            if settings.db_type.lower() == "mysql":
                # MySQL创建数据库
                conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{settings.db_name}` CHARACTER SET {settings.db_charset} COLLATE {settings.db_charset}_unicode_ci"))
                logger.info(f"数据库 {settings.db_name} 创建成功（如果不存在）")
            elif settings.db_type.lower() == "postgresql":
                # PostgreSQL创建数据库
                conn.execute(text("COMMIT"))  # 结束事务
                conn.execute(text(f"CREATE DATABASE {settings.db_name}"))
                logger.info(f"数据库 {settings.db_name} 创建成功（如果不存在）")
        
        admin_engine.dispose()
        
        # 连接到目标数据库
        engine = create_engine(settings.db_url)
        
        # 创建表结构
        with engine.connect() as conn:
            # 创建任务表
            create_tasks_table_sql = """
            CREATE TABLE IF NOT EXISTS tasks (
                id VARCHAR(36) PRIMARY KEY COMMENT '任务ID',
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
            
            # 根据数据库类型调整SQL
            if settings.db_type.lower() == "postgresql":
                create_tasks_table_sql = """
                CREATE TABLE IF NOT EXISTS tasks (
                    id VARCHAR(36) PRIMARY KEY,
                    status VARCHAR(20) NOT NULL DEFAULT 'pending',
                    model_type VARCHAR(10) NOT NULL,
                    shot_type VARCHAR(20) NOT NULL,
                    aspect_ratio VARCHAR(10) NOT NULL,
                    style VARCHAR(50) DEFAULT 'portrait_photography',
                    resolution VARCHAR(20),
                    ai_model_id VARCHAR(50),
                    prompt TEXT,
                    result_image_url TEXT,
                    local_path TEXT,
                    error_message TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_status ON tasks(status);
                CREATE INDEX IF NOT EXISTS idx_created_at ON tasks(created_at);
                """
            elif settings.db_type.lower() == "sqlite":
                create_tasks_table_sql = """
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    status TEXT NOT NULL DEFAULT 'pending',
                    model_type TEXT NOT NULL,
                    shot_type TEXT NOT NULL,
                    aspect_ratio TEXT NOT NULL,
                    style TEXT DEFAULT 'portrait_photography',
                    resolution TEXT,
                    ai_model_id TEXT,
                    prompt TEXT,
                    result_image_url TEXT,
                    local_path TEXT,
                    error_message TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_status ON tasks(status);
                CREATE INDEX IF NOT EXISTS idx_created_at ON tasks(created_at);
                """
            
            conn.execute(text(create_tasks_table_sql))
            conn.commit()
            logger.info("任务表创建成功")
        
        engine.dispose()
        logger.info("数据库初始化完成")
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    print("开始初始化数据库...")
    print(f"数据库类型: {settings.db_type}")
    print(f"数据库地址: {settings.db_host}:{settings.db_port}")
    print(f"数据库名称: {settings.db_name}")
    print()
    
    try:
        init_database()
        print("✅ 数据库初始化成功！")
    except Exception as e:
        print(f"❌ 数据库初始化失败: {str(e)}")
        sys.exit(1)

