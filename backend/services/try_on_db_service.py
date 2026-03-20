#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库服务模块（适配版）
负责任务的数据库持久化操作，使用主项目的数据库配置
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
import time
from contextlib import nullcontext
from sqlalchemy import text
from sqlalchemy import exc
from flask import has_app_context

try:
    # 复用主程序通过 wsgi 创建的 application，避免在后台线程缺少 app context
    from backend.wsgi import application as flask_app
except Exception:
    flask_app = None

from backend.config.config import Config
from backend.utils.logger import logger
from backend.models import db

# 获取日志记录器
# 注意：使用主项目的 logger，而不是 try_on 服务的 logger


class TryOnDatabaseService:
    """数据库服务类，负责任务的数据库操作（适配主项目）"""
    
    def __init__(self, config: Config):
        """
        初始化数据库服务
        
        Args:
            config: 主项目的配置对象
        """
        self.config = config
        # 使用主项目的数据库连接（Flask-SQLAlchemy 的 db 对象）
        # 不需要创建新的引擎，直接使用主项目的 db.engine
        logger.info("TryOn数据库服务初始化完成（使用主项目数据库连接）")
    
    def save_task(self, task_dict: Dict[str, Any]) -> bool:
        """
        保存任务到数据库
        
        Args:
            task_dict: 任务字典（包含 task_id, status, model_type, shot_type 等）
        
        Returns:
            是否保存成功
        """
        # #region agent log
        import json
        with open('/opt/hanfu/products/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"try_on_db_service.py:35","message":"save_task调用-BEFORE执行","data":{"task_id":task_dict.get("task_id"),"status":task_dict.get("status"),"result_image_url":task_dict.get("result_image_url"),"local_path":task_dict.get("local_path")},"timestamp":int(time.time()*1000)}) + '\n')
        # #endregion
        
        # 如果当前没有 Flask application context，则补一个，避免 Flask-SQLAlchemy 抛出 No application found
        ctx = flask_app.app_context() if (flask_app is not None and not has_app_context()) else nullcontext()
        try:
            with ctx:
                # 使用主项目的数据库连接（Flask-SQLAlchemy 的 db）
                # 使用 db.session 确保事务一致性，并立即提交
                # 构建 SQL 语句（MySQL 使用 ON DUPLICATE KEY UPDATE）
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
                
                sql_params = {
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
                }
                
                # #region agent log
                with open('/opt/hanfu/products/.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"try_on_db_service.py:68","message":"SQL参数-BEFORE执行","data":{"task_id":sql_params.get("task_id"),"status":sql_params.get("status"),"result_image_url":sql_params.get("result_image_url"),"local_path":sql_params.get("local_path")},"timestamp":int(time.time()*1000)}) + '\n')
                # #endregion
                
                # 执行 SQL 并立即提交，确保其他查询能立即看到最新数据
                result = db.session.execute(sql, sql_params)
                db.session.commit()  # 立即提交，确保数据立即可见
                
                # #region agent log
                with open('/opt/hanfu/products/.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"try_on_db_service.py:85","message":"SQL执行成功并已提交","data":{"task_id":task_dict.get("task_id"),"rowcount":result.rowcount if hasattr(result, 'rowcount') else 'N/A'},"timestamp":int(time.time()*1000)}) + '\n')
                # #endregion
                
                logger.debug(f"任务保存到数据库成功: task_id={task_dict.get('task_id')}")
                return True
                
        except exc.SQLAlchemyError as e:
            # 回滚事务
            db.session.rollback()
            # #region agent log
            import json
            import traceback
            with open('/opt/hanfu/products/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"try_on_db_service.py:88","message":"SQLAlchemy异常","data":{"task_id":task_dict.get("task_id"),"error":str(e),"traceback":traceback.format_exc()},"timestamp":int(time.time()*1000)}) + '\n')
            # #endregion
            logger.error(f"保存任务到数据库失败（已回滚）: {str(e)}", exc_info=True)
            return False
        except Exception as e:
            # 回滚事务
            db.session.rollback()
            # #region agent log
            import json
            import traceback
            with open('/opt/hanfu/products/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"try_on_db_service.py:95","message":"数据库保存通用异常","data":{"task_id":task_dict.get("task_id"),"error":str(e),"traceback":traceback.format_exc()},"timestamp":int(time.time()*1000)}) + '\n')
            # #endregion
            logger.error(f"保存任务到数据库异常（已回滚）: {str(e)}", exc_info=True)
            return False
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        从数据库获取任务
        
        Args:
            task_id: 任务ID
        
        Returns:
            任务字典，如果不存在返回 None
        """
        # #region agent log
        import json
        import time
        with open('/opt/hanfu/products/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"G","location":"try_on_db_service.py:129","message":"get_task调用-BEFORE查询","data":{"task_id":task_id},"timestamp":int(time.time()*1000)}) + '\n')
        # #endregion
        
        # 如果当前没有 Flask application context，则补一个，避免 Flask-SQLAlchemy 抛出 No application found
        ctx = flask_app.app_context() if (flask_app is not None and not has_app_context()) else nullcontext()
        try:
            with ctx:
                # 关键修复：使用独立的数据库连接，设置 READ COMMITTED 隔离级别
                # 这样可以避免 MySQL 的 REPEATABLE READ 隔离级别导致的读取旧数据问题
                # 使用 db.engine.connect() 创建新连接，确保读取最新已提交的数据
                with db.engine.connect() as conn:
                    # 设置隔离级别为 READ COMMITTED，确保读取最新已提交的数据
                    # 注意：必须在每个连接上单独设置，使用 autocommit 模式
                    conn.execute(text("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED"))
                    # 对于只读查询，不需要 commit，直接执行查询
                    
                    sql = text("""
                    SELECT id, status, model_type, shot_type, aspect_ratio, style,
                           resolution, ai_model_id, prompt, result_image_url, local_path,
                           error_message, created_at, updated_at
                    FROM tasks
                    WHERE id = :task_id
                    """)
                    result = conn.execute(sql, {"task_id": task_id})
                    row = result.fetchone()
                
                    # #region agent log
                    with open('/opt/hanfu/products/.cursor/debug.log', 'a') as f:
                        import json
                        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H","location":"try_on_db_service.py:156","message":"get_task-查询执行后(READ_COMMITTED)","data":{"task_id":task_id,"row_exists":row is not None,"status":row[1] if row else None},"timestamp":int(time.time()*1000)}) + '\n')
                    # #endregion
                    
                    task_dict = {
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
                    
                    # #region agent log
                    with open('/opt/hanfu/products/.cursor/debug.log', 'a') as f:
                        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H","location":"try_on_db_service.py:165","message":"get_task-查询结果(READ_COMMITTED)","data":{"task_id":task_id,"status":task_dict.get("status"),"result_image_url":task_dict.get("result_image_url")},"timestamp":int(time.time()*1000)}) + '\n')
                    # #endregion
                    
                    return task_dict
                
                # #region agent log
                with open('/opt/hanfu/products/.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H","location":"try_on_db_service.py:172","message":"get_task-任务不存在","data":{"task_id":task_id},"timestamp":int(time.time()*1000)}) + '\n')
                # #endregion
                
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
            with db.engine.connect() as conn:
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
