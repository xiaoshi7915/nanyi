#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""迁移：用户邮箱密码、浏览足迹、登录事件、重置令牌。"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from sqlalchemy import text

from backend.app import create_app
from backend.models import db


def _add_col(table: str, col: str, ddl: str) -> None:
    rows = db.session.execute(text(f"SHOW COLUMNS FROM `{table}` LIKE :c"), {"c": col}).fetchall()
    if not rows:
        db.session.execute(text(f"ALTER TABLE `{table}` ADD COLUMN {ddl}"))
        print(f"+ {table}.{col}")
    else:
        print(f"= {table}.{col} exists")


def main():
    app = create_app()
    with app.app_context():
        _add_col("users", "email", "email VARCHAR(191) NULL UNIQUE")
        _add_col("users", "password_hash", "password_hash VARCHAR(255) NULL")
        _add_col("users", "email_verified_at", "email_verified_at DATETIME NULL")
        # 对齐 C 端 User 模型（旧表仅有 username/password）
        _add_col("users", "nickname", "nickname VARCHAR(128) NULL")
        _add_col("users", "avatar_url", "avatar_url VARCHAR(512) NULL")
        _add_col("users", "country", "country VARCHAR(64) NULL")
        _add_col("users", "province", "province VARCHAR(64) NULL")
        _add_col("users", "city", "city VARCHAR(64) NULL")
        _add_col("users", "phone", "phone VARCHAR(32) NULL")
        _add_col("users", "display_id", "display_id VARCHAR(64) NULL")
        _add_col("users", "status", "status VARCHAR(20) NOT NULL DEFAULT 'active'")
        _add_col("users", "updated_at", "updated_at DATETIME NULL")
        try:
            db.session.execute(text("ALTER TABLE users MODIFY COLUMN username VARCHAR(80) NULL"))
            db.session.execute(text("ALTER TABLE users MODIFY COLUMN password VARCHAR(200) NULL"))
            print("~ users.username/password nullable")
        except Exception as e:
            print("skip modify username/password:", e)

        db.session.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS user_browse_events (
                  id INT AUTO_INCREMENT PRIMARY KEY,
                  user_id INT NOT NULL,
                  brand_name VARCHAR(191) NOT NULL,
                  created_at DATETIME NOT NULL,
                  INDEX idx_ube_user (user_id),
                  INDEX idx_ube_brand (brand_name),
                  INDEX idx_ube_time (created_at),
                  CONSTRAINT fk_ube_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )
        )
        db.session.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS user_login_events (
                  id INT AUTO_INCREMENT PRIMARY KEY,
                  user_id INT NOT NULL,
                  method VARCHAR(32) NOT NULL,
                  ip VARCHAR(64) NULL,
                  user_agent VARCHAR(512) NULL,
                  created_at DATETIME NOT NULL,
                  INDEX idx_ule_user (user_id),
                  INDEX idx_ule_time (created_at),
                  CONSTRAINT fk_ule_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )
        )
        db.session.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS password_reset_tokens (
                  id INT AUTO_INCREMENT PRIMARY KEY,
                  user_id INT NOT NULL,
                  token VARCHAR(64) NOT NULL UNIQUE,
                  expires_at DATETIME NOT NULL,
                  used_at DATETIME NULL,
                  created_at DATETIME NOT NULL,
                  INDEX idx_prt_user (user_id),
                  CONSTRAINT fk_prt_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )
        )
        db.session.commit()
        print("migration done")


if __name__ == "__main__":
    main()
