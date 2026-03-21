#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库服务模块（适配版）
负责任务的数据库持久化操作，使用主项目的数据库配置
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from contextlib import nullcontext
from sqlalchemy import text
from sqlalchemy import exc
from flask import has_app_context

from backend.config.config import Config
from backend.utils.logger import logger
from backend.models import db


class TryOnDatabaseService:
    """数据库服务类，负责任务的数据库操作（适配主项目）"""

    def __init__(self, config: Config, app=None):
        """
        Args:
            config: 配置
            app: Flask 应用实例；后台线程无请求上下文时用于 push app_context。
                 切勿在模块顶层 import backend.wsgi，否则会与 create_app 形成循环导入。
        """
        self.config = config
        self._flask_app = app
        logger.info("TryOn数据库服务初始化完成（使用主项目数据库连接）")

    def _app_context_if_needed(self):
        if has_app_context():
            return nullcontext()
        if self._flask_app is not None:
            return self._flask_app.app_context()
        return nullcontext()

    def save_task(self, task_dict: Dict[str, Any]) -> bool:
        """保存任务到数据库"""
        ctx = self._app_context_if_needed()
        try:
            with ctx:
                sql = text("""
                INSERT INTO tasks (
                    id, access_token, status, model_type, shot_type, aspect_ratio, style,
                    resolution, ai_model_id, prompt, result_image_url, local_path,
                    error_message, created_at, updated_at
                ) VALUES (
                    :task_id, :access_token, :status, :model_type, :shot_type, :aspect_ratio, :style,
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
                    "access_token": task_dict.get("access_token"),
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
                    "updated_at": task_dict.get("updated_at", datetime.now()),
                }

                db.session.execute(sql, sql_params)
                db.session.commit()
                logger.debug(f"任务保存到数据库成功: task_id={task_dict.get('task_id')}")
                return True

        except exc.SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"保存任务到数据库失败（已回滚）: {str(e)}", exc_info=True)
            return False
        except Exception as e:
            db.session.rollback()
            logger.error(f"保存任务到数据库异常（已回滚）: {str(e)}", exc_info=True)
            return False

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """从数据库获取任务"""
        ctx = self._app_context_if_needed()
        try:
            with ctx:
                with db.engine.connect() as conn:
                    conn.execute(text("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED"))
                    sql = text("""
                    SELECT id, access_token, status, model_type, shot_type, aspect_ratio, style,
                           resolution, ai_model_id, prompt, result_image_url, local_path,
                           error_message, created_at, updated_at
                    FROM tasks
                    WHERE id = :task_id
                    """)
                    result = conn.execute(sql, {"task_id": task_id})
                    row = result.fetchone()

                    if not row:
                        logger.debug(f"get_task: 未找到任务 task_id={task_id}")
                        return None

                    return {
                        "task_id": row[0],
                        "access_token": row[1],
                        "status": row[2],
                        "model_type": row[3],
                        "shot_type": row[4],
                        "aspect_ratio": row[5],
                        "style": row[6],
                        "resolution": row[7],
                        "ai_model_id": row[8],
                        "prompt": row[9],
                        "result_image_url": row[10],
                        "local_path": row[11],
                        "error_message": row[12],
                        "created_at": row[13],
                        "updated_at": row[14],
                    }

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
        """列出任务"""
        try:
            with db.engine.connect() as conn:
                if status:
                    sql = text("""
                    SELECT id, access_token, status, model_type, shot_type, aspect_ratio, style,
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
                    SELECT id, access_token, status, model_type, shot_type, aspect_ratio, style,
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
                        "access_token": row[1],
                        "status": row[2],
                        "model_type": row[3],
                        "shot_type": row[4],
                        "aspect_ratio": row[5],
                        "style": row[6],
                        "resolution": row[7],
                        "ai_model_id": row[8],
                        "prompt": row[9],
                        "result_image_url": row[10],
                        "local_path": row[11],
                        "error_message": row[12],
                        "created_at": row[13],
                        "updated_at": row[14],
                    })
                return tasks

        except exc.SQLAlchemyError as e:
            logger.error(f"从数据库列出任务失败: {str(e)}", exc_info=True)
            return []
        except Exception as e:
            logger.error(f"从数据库列出任务异常: {str(e)}", exc_info=True)
            return []
