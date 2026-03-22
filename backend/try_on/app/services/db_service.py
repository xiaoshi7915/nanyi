"""
数据库服务模块
负责任务的数据库持久化操作
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy import exc

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DatabaseService:
    """数据库服务类，负责任务的数据库操作"""
    
    def __init__(self):
        """初始化数据库服务"""
        # 配置连接池参数
        connect_args = {}
        if settings.db_type.lower() == "mysql":
            # MySQL特定配置
            connect_args = {"charset": settings.db_charset}
        
        # 创建数据库引擎，配置连接池参数
        self.engine = create_engine(
            settings.db_url,
            pool_size=settings.db_pool_size,  # 连接池大小
            max_overflow=settings.db_max_overflow,  # 最大溢出连接数
            pool_timeout=settings.db_pool_timeout,  # 获取连接超时时间
            pool_recycle=settings.db_pool_recycle,  # 连接回收时间
            pool_pre_ping=settings.db_pool_pre_ping,  # 连接前ping测试
            connect_args=connect_args
        )
        logger.info(
            f"数据库服务初始化完成 - 连接池配置: "
            f"pool_size={settings.db_pool_size}, "
            f"max_overflow={settings.db_max_overflow}, "
            f"pool_timeout={settings.db_pool_timeout}s, "
            f"pool_recycle={settings.db_pool_recycle}s"
        )
    
    def save_task(self, task_dict: Dict[str, Any]) -> bool:
        """
        保存任务到数据库
        
        Args:
            task_dict: 任务字典（包含 task_id, status, model_type, shot_type 等）
        
        Returns:
            是否保存成功
        """
        try:
            # 使用begin()上下文管理器确保事务一致性
            with self.engine.begin() as conn:
                # 构建 SQL 语句
                if settings.db_type.lower() == "mysql":
                    sql = text("""
                    INSERT INTO tasks (
                        id, status, model_type, shot_type, aspect_ratio, style,
                        resolution, ai_model_id, prompt, result_image_url, local_path,
                        error_message, created_at, updated_at
                    ) VALUES (
                        :task_id, :status, :model_type, :shot_type, :aspect_ratio, :style,
                        :resolution, :ai_model_id, :prompt, :result_image_url, :local_path,
                        :error_message, :created_at, :updated_at
                    ) ON DUPLICATE KEY UPDATE
                        status = VALUES(status),
                        result_image_url = VALUES(result_image_url),
                        local_path = VALUES(local_path),
                        error_message = VALUES(error_message),
                        updated_at = VALUES(updated_at)
                    """)
                else:
                    # PostgreSQL 和 SQLite 使用 UPSERT
                    sql = text("""
                    INSERT INTO tasks (
                        id, status, model_type, shot_type, aspect_ratio, style,
                        resolution, ai_model_id, prompt, result_image_url, local_path,
                        error_message, created_at, updated_at
                    ) VALUES (
                        :task_id, :status, :model_type, :shot_type, :aspect_ratio, :style,
                        :resolution, :ai_model_id, :prompt, :result_image_url, :local_path,
                        :error_message, :created_at, :updated_at
                    ) ON CONFLICT(id) DO UPDATE SET
                        status = EXCLUDED.status,
                        result_image_url = EXCLUDED.result_image_url,
                        local_path = EXCLUDED.local_path,
                        error_message = EXCLUDED.error_message,
                        updated_at = EXCLUDED.updated_at
                    """)
                
                # 执行 SQL（begin()上下文管理器会自动提交或回滚）
                conn.execute(sql, {
                    "task_id": task_dict.get("task_id"),
                    "status": task_dict.get("status"),
                    "model_type": task_dict.get("model_type"),
                    "shot_type": task_dict.get("shot_type"),
                    "aspect_ratio": task_dict.get("aspect_ratio"),
                    "style": task_dict.get("style"),
                    "resolution": task_dict.get("resolution"),
                    "ai_model_id": task_dict.get("ai_model_id"),
                    "prompt": task_dict.get("prompt"),
                    "result_image_url": task_dict.get("result_image_url"),
                    "local_path": task_dict.get("local_path"),
                    "error_message": task_dict.get("error_message"),
                    "created_at": task_dict.get("created_at", datetime.now()),
                    "updated_at": task_dict.get("updated_at", datetime.now())
                })
                # begin()上下文管理器会在成功时自动提交，异常时自动回滚
                logger.debug(f"任务保存到数据库成功: task_id={task_dict.get('task_id')}")
                return True
                
        except exc.SQLAlchemyError as e:
            # begin()上下文管理器会自动回滚事务
            logger.error(f"保存任务到数据库失败（已自动回滚）: {str(e)}", exc_info=True)
            return False
        except Exception as e:
            # begin()上下文管理器会自动回滚事务
            logger.error(f"保存任务到数据库异常（已自动回滚）: {str(e)}", exc_info=True)
            return False
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        从数据库获取任务
        
        Args:
            task_id: 任务ID
        
        Returns:
            任务字典，如果不存在返回 None
        """
        try:
            with self.engine.connect() as conn:
                sql = text("""
                SELECT id, status, model_type, shot_type, aspect_ratio, style,
                       resolution, ai_model_id, prompt, result_image_url, local_path,
                       error_message, created_at, updated_at
                FROM tasks
                WHERE id = :task_id
                """)
                result = conn.execute(sql, {"task_id": task_id})
                row = result.fetchone()
                
                if row:
                    return {
                        "task_id": row[0],
                        "status": row[1],
                        "model_type": row[2],
                        "shot_type": row[3],
                        "aspect_ratio": row[4],
                        "style": row[5],
                        "resolution": row[6],
                        "ai_model_id": row[7],
                        "prompt": row[8],
                        "result_image_url": row[9],
                        "local_path": row[10],
                        "error_message": row[11],
                        "created_at": row[12],
                        "updated_at": row[13]
                    }
                return None
                
        except exc.SQLAlchemyError as e:
            logger.error(f"从数据库获取任务失败: {str(e)}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"从数据库获取任务异常: {str(e)}", exc_info=True)
            return None
    
    def list_tasks(
        self,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        列出任务
        
        Args:
            status: 任务状态过滤（可选）
            limit: 返回数量限制
        
        Returns:
            任务列表
        """
        try:
            with self.engine.connect() as conn:
                if status:
                    sql = text("""
                    SELECT id, status, model_type, shot_type, aspect_ratio, style,
                           resolution, ai_model_id, prompt, result_image_url, local_path,
                           error_message, created_at, updated_at
                    FROM tasks
                    WHERE status = :status
                    ORDER BY created_at DESC
                    LIMIT :limit
                    """)
                    result = conn.execute(sql, {"status": status, "limit": limit})
                else:
                    sql = text("""
                    SELECT id, status, model_type, shot_type, aspect_ratio, style,
                           resolution, ai_model_id, prompt, result_image_url, local_path,
                           error_message, created_at, updated_at
                    FROM tasks
                    ORDER BY created_at DESC
                    LIMIT :limit
                    """)
                    result = conn.execute(sql, {"limit": limit})
                
                tasks = []
                for row in result:
                    tasks.append({
                        "task_id": row[0],
                        "status": row[1],
                        "model_type": row[2],
                        "shot_type": row[3],
                        "aspect_ratio": row[4],
                        "style": row[5],
                        "resolution": row[6],
                        "ai_model_id": row[7],
                        "prompt": row[8],
                        "result_image_url": row[9],
                        "local_path": row[10],
                        "error_message": row[11],
                        "created_at": row[12],
                        "updated_at": row[13]
                    })
                return tasks
                
        except exc.SQLAlchemyError as e:
            logger.error(f"从数据库列出任务失败: {str(e)}", exc_info=True)
            return []
        except Exception as e:
            logger.error(f"从数据库列出任务异常: {str(e)}", exc_info=True)
            return []


# 全局数据库服务实例
db_service = DatabaseService()

