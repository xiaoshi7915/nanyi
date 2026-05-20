#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建 users / oauth_bindings / user_assets，并为 tasks、brand_likes 增加 user_id 及索引
可重复执行：已存在的对象会跳过
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


def _column_exists(conn, table: str, column: str) -> bool:
    r = conn.execute(
        text(
            """
            SELECT COUNT(*) FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :t AND COLUMN_NAME = :c
            """
        ),
        {"t": table, "c": column},
    )
    return r.scalar() > 0


def _table_exists(conn, table: str) -> bool:
    r = conn.execute(
        text(
            """
            SELECT COUNT(*) FROM information_schema.TABLES
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :t
            """
        ),
        {"t": table},
    )
    return r.scalar() > 0


def _index_exists(conn, table: str, index_name: str) -> bool:
    r = conn.execute(
        text(
            """
            SELECT COUNT(*) FROM information_schema.STATISTICS
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :t AND INDEX_NAME = :i
            """
        ),
        {"t": table, "i": index_name},
    )
    return r.scalar() > 0


def _fk_exists(conn, table: str, constraint_name: str) -> bool:
    r = conn.execute(
        text(
            """
            SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :t AND CONSTRAINT_NAME = :c
            """
        ),
        {"t": table, "c": constraint_name},
    )
    return r.scalar() > 0


def run_migration():
    app = create_app()
    with app.app_context():
        with db.engine.connect() as conn:
            trans = conn.begin()
            try:
                # 1) users
                if not _table_exists(conn, "users"):
                    conn.execute(
                        text(
                            """
                            CREATE TABLE users (
                                id INT AUTO_INCREMENT PRIMARY KEY,
                                nickname VARCHAR(128) NULL,
                                avatar_url VARCHAR(512) NULL,
                                country VARCHAR(64) NULL,
                                province VARCHAR(64) NULL,
                                city VARCHAR(64) NULL,
                                phone VARCHAR(32) NULL,
                                display_id VARCHAR(64) NULL,
                                status VARCHAR(20) NOT NULL DEFAULT 'active',
                                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                                UNIQUE KEY uk_users_phone (phone),
                                INDEX idx_users_display_id (display_id),
                                INDEX idx_users_status (status)
                            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                            COMMENT='站内用户'
                            """
                        )
                    )

                # 2) oauth_bindings
                if not _table_exists(conn, "oauth_bindings"):
                    conn.execute(
                        text(
                            """
                            CREATE TABLE oauth_bindings (
                                id INT AUTO_INCREMENT PRIMARY KEY,
                                user_id INT NOT NULL,
                                provider VARCHAR(32) NOT NULL,
                                openid VARCHAR(64) NOT NULL,
                                unionid VARCHAR(64) NULL,
                                raw_payload JSON NULL,
                                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                                UNIQUE KEY uk_oauth_provider_openid (provider, openid),
                                INDEX idx_oauth_user_id (user_id),
                                INDEX idx_oauth_provider (provider),
                                INDEX idx_oauth_unionid (unionid),
                                CONSTRAINT fk_oauth_user FOREIGN KEY (user_id)
                                    REFERENCES users(id) ON DELETE CASCADE
                            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                            COMMENT='第三方账号绑定'
                            """
                        )
                    )

                # 3) user_assets（任务表须已存在）
                if not _table_exists(conn, "user_assets"):
                    conn.execute(
                        text(
                            """
                            CREATE TABLE user_assets (
                                id INT AUTO_INCREMENT PRIMARY KEY,
                                user_id INT NOT NULL,
                                type VARCHAR(32) NOT NULL,
                                task_id VARCHAR(36) NULL,
                                storage_key VARCHAR(512) NULL,
                                url TEXT NULL,
                                mime VARCHAR(128) NULL,
                                size BIGINT NULL,
                                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                                INDEX idx_user_assets_user (user_id),
                                INDEX idx_user_assets_type (type),
                                INDEX idx_user_assets_task (task_id),
                                INDEX idx_user_assets_created (created_at),
                                CONSTRAINT fk_user_assets_user FOREIGN KEY (user_id)
                                    REFERENCES users(id) ON DELETE CASCADE
                            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                            COMMENT='用户上传与试衣结果元数据'
                            """
                        )
                    )

                # 4) tasks.user_id
                if _table_exists(conn, "tasks") and not _column_exists(conn, "tasks", "user_id"):
                    conn.execute(
                        text(
                            """
                            ALTER TABLE tasks
                            ADD COLUMN user_id INT NULL COMMENT '登录用户 ID，历史任务可为空'
                            AFTER access_token
                            """
                        )
                    )
                if _table_exists(conn, "tasks") and not _index_exists(conn, "tasks", "idx_tasks_user_id"):
                    conn.execute(text("CREATE INDEX idx_tasks_user_id ON tasks(user_id)"))
                if _table_exists(conn, "tasks") and not _fk_exists(conn, "tasks", "fk_tasks_user"):
                    conn.execute(
                        text(
                            """
                            ALTER TABLE tasks
                            ADD CONSTRAINT fk_tasks_user FOREIGN KEY (user_id)
                                REFERENCES users(id) ON DELETE SET NULL
                            """
                        )
                    )

                # 5) brand_likes.user_id（保留原 unique_user_brand，登录态去重在应用层或后续迁移）
                if _table_exists(conn, "brand_likes") and not _column_exists(
                    conn, "brand_likes", "user_id"
                ):
                    conn.execute(
                        text(
                            """
                            ALTER TABLE brand_likes
                            ADD COLUMN user_id INT NULL COMMENT '登录用户点赞时写入'
                            AFTER user_hash
                            """
                        )
                    )
                if _table_exists(conn, "brand_likes") and not _index_exists(
                    conn, "brand_likes", "idx_brand_likes_user_id"
                ):
                    conn.execute(
                        text("CREATE INDEX idx_brand_likes_user_id ON brand_likes(user_id)")
                    )
                if _table_exists(conn, "brand_likes") and not _index_exists(
                    conn, "brand_likes", "idx_brand_likes_brand_user"
                ):
                    conn.execute(
                        text(
                            "CREATE INDEX idx_brand_likes_brand_user ON brand_likes(brand_name, user_id)"
                        )
                    )
                if _table_exists(conn, "brand_likes") and not _fk_exists(
                    conn, "brand_likes", "fk_brand_likes_user"
                ):
                    conn.execute(
                        text(
                            """
                            ALTER TABLE brand_likes
                            ADD CONSTRAINT fk_brand_likes_user FOREIGN KEY (user_id)
                                REFERENCES users(id) ON DELETE SET NULL
                            """
                        )
                    )

                trans.commit()
                print("✅ 迁移执行成功：users / oauth_bindings / user_assets / tasks.user_id / brand_likes.user_id")
                return True
            except Exception as e:
                trans.rollback()
                print(f"❌ 迁移失败: {e}")
                import traceback

                traceback.print_exc()
                return False


if __name__ == "__main__":
    print("开始执行用户与 OAuth 相关表结构迁移...")
    if not run_migration():
        sys.exit(1)
