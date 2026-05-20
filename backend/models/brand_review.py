#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
品牌评价数据模型（MySQL 原生表，与 brand_like 一致）
公开接口不返回用户 PII，后台留存 user_id / openid 等供审计
"""

from datetime import datetime
import logging
from typing import Any, Dict, List, Optional, Tuple

from backend.utils.db_connection import get_db_connection

logger = logging.getLogger(__name__)

# 评价正文最大长度
MAX_CONTENT_LENGTH = 2000


class BrandReview:
    """布料评价"""

    @staticmethod
    def create_table() -> bool:
        """创建 brand_reviews 表"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS brand_reviews (
                id INT AUTO_INCREMENT PRIMARY KEY,
                brand_name VARCHAR(255) NOT NULL COMMENT '品牌名称（完整款名，可含颜色）',
                rating TINYINT NULL COMMENT '评分 1-5，可选',
                content TEXT NULL COMMENT '评价正文',
                is_anonymous TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否匿名展示',
                user_id INT NULL COMMENT '登录用户 ID（审计用，不对外暴露）',
                user_openid VARCHAR(64) NULL COMMENT '微信 openid（审计用）',
                session_hash VARCHAR(64) NULL COMMENT '未登录时会话哈希',
                ip_address VARCHAR(45) NULL COMMENT 'IP 地址',
                user_agent TEXT NULL COMMENT 'User-Agent',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                INDEX idx_brand_name (brand_name),
                INDEX idx_created_at (created_at),
                INDEX idx_user_id (user_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
              COMMENT='品牌评价表'
            """
            )
            connection.commit()
            logger.info("✅ 评价数据表 brand_reviews 创建成功")
            return True
        except Exception as e:
            logger.error("❌ 创建评价数据表失败: %s", e)
            return False
        finally:
            if "connection" in locals():
                connection.close()

    @staticmethod
    def _normalize_brand_name(brand_name: str) -> str:
        """去除首尾空白"""
        return (brand_name or "").strip()

    @staticmethod
    def _validate_rating(rating: Any) -> Optional[int]:
        """校验评分，无效返回 None；有效返回 1-5 整数"""
        if rating is None or rating == "":
            return None
        try:
            r = int(rating)
        except (TypeError, ValueError):
            raise ValueError("评分必须是 1 到 5 的整数")
        if r < 1 or r > 5:
            raise ValueError("评分必须是 1 到 5 的整数")
        return r

    @staticmethod
    def _format_created_at(created) -> Optional[str]:
        """将 created_at 转为 ISO 字符串"""
        if isinstance(created, datetime):
            return created.isoformat()
        if created:
            return str(created)
        return None

    @staticmethod
    def _admin_row(row: Dict) -> Dict:
        """管理后台完整评价记录（含审计字段）"""
        return {
            "id": row["id"],
            "brand_name": row["brand_name"],
            "rating": row.get("rating"),
            "content": row.get("content") or "",
            "is_anonymous": bool(row.get("is_anonymous", 1)),
            "user_id": row.get("user_id"),
            "user_openid": row.get("user_openid"),
            "session_hash": row.get("session_hash"),
            "ip_address": row.get("ip_address"),
            "user_agent": row.get("user_agent"),
            "created_at": BrandReview._format_created_at(row.get("created_at")),
        }

    @staticmethod
    def _public_row(row: Dict) -> Dict:
        """转为对外安全的评价对象（不含用户身份）"""
        created_str = BrandReview._format_created_at(row.get("created_at"))
        display_name = "匿名用户"
        if not row.get("is_anonymous", 1):
            display_name = "匿名用户"
        return {
            "id": row["id"],
            "brand_name": row["brand_name"],
            "rating": row.get("rating"),
            "content": row.get("content") or "",
            "display_name": display_name,
            "created_at": created_str,
        }

    @staticmethod
    def add_review(
        brand_name: str,
        rating: Any = None,
        content: str = None,
        is_anonymous: bool = True,
        user_id: Optional[int] = None,
        user_openid: Optional[str] = None,
        session_hash: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Tuple[bool, Any]:
        """
        新增评价
        Returns: (success, review_dict_or_error_message)
        """
        brand_name = BrandReview._normalize_brand_name(brand_name)
        if not brand_name:
            return False, "品牌名称不能为空"

        try:
            rating_val = BrandReview._validate_rating(rating)
        except ValueError as e:
            return False, str(e)

        text = (content or "").strip()
        if len(text) > MAX_CONTENT_LENGTH:
            return False, f"评价内容不能超过 {MAX_CONTENT_LENGTH} 字"

        if rating_val is None and not text:
            return False, "请至少填写评分或评价内容"

        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO brand_reviews (
                    brand_name, rating, content, is_anonymous,
                    user_id, user_openid, session_hash,
                    ip_address, user_agent
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    brand_name,
                    rating_val,
                    text or None,
                    1 if is_anonymous else 0,
                    user_id,
                    user_openid,
                    session_hash,
                    ip_address,
                    user_agent,
                ),
            )
            review_id = cursor.lastrowid
            connection.commit()

            cursor.execute(
                "SELECT * FROM brand_reviews WHERE id = %s",
                (review_id,),
            )
            row = cursor.fetchone()
            return True, BrandReview._public_row(row)
        except Exception as e:
            logger.error("添加评价失败: %s", e)
            return False, "提交评价失败，请稍后重试"
        finally:
            if "connection" in locals():
                connection.close()

    @staticmethod
    def list_by_brand(
        brand_name: str,
        page: int = 1,
        limit: int = 20,
    ) -> Dict:
        """分页查询某品牌评价及统计"""
        brand_name = BrandReview._normalize_brand_name(brand_name)
        page = max(1, int(page or 1))
        limit = min(50, max(1, int(limit or 20)))
        offset = (page - 1) * limit

        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            cursor.execute(
                "SELECT COUNT(*) AS cnt FROM brand_reviews WHERE brand_name = %s",
                (brand_name,),
            )
            total = (cursor.fetchone() or {}).get("cnt", 0)

            cursor.execute(
                """
                SELECT id, brand_name, rating, content, is_anonymous, created_at
                FROM brand_reviews
                WHERE brand_name = %s
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
                """,
                (brand_name, limit, offset),
            )
            rows = cursor.fetchall() or []
            reviews = [BrandReview._public_row(r) for r in rows]

            cursor.execute(
                """
                SELECT AVG(rating) AS avg_rating, COUNT(rating) AS rated_count
                FROM brand_reviews
                WHERE brand_name = %s AND rating IS NOT NULL
                """,
                (brand_name,),
            )
            stat_row = cursor.fetchone() or {}
            avg_raw = stat_row.get("avg_rating")
            avg_rating = round(float(avg_raw), 2) if avg_raw is not None else None

            return {
                "brand_name": brand_name,
                "reviews": reviews,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "has_more": offset + len(reviews) < total,
                },
                "stats": {
                    "count": total,
                    "avg_rating": avg_rating,
                    "rated_count": stat_row.get("rated_count") or 0,
                },
            }
        except Exception as e:
            logger.error("查询评价列表失败: %s", e)
            return {
                "brand_name": brand_name,
                "reviews": [],
                "pagination": {"page": page, "limit": limit, "total": 0, "has_more": False},
                "stats": {"count": 0, "avg_rating": None, "rated_count": 0},
            }
        finally:
            if "connection" in locals():
                connection.close()

    @staticmethod
    def list_admin(
        page: int = 1,
        limit: int = 50,
        brand_name: Optional[str] = None,
    ) -> Dict:
        """管理后台：分页列出评价（含 user_id、openid 等审计字段）"""
        page = max(1, int(page or 1))
        limit = min(100, max(1, int(limit or 50)))
        offset = (page - 1) * limit

        where_sql = ""
        params: List = []
        if brand_name:
            where_sql = " WHERE brand_name LIKE %s"
            params.append(f"%{brand_name}%")

        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            cursor.execute(
                f"SELECT COUNT(*) AS cnt FROM brand_reviews{where_sql}",
                tuple(params),
            )
            total = (cursor.fetchone() or {}).get("cnt", 0)

            cursor.execute(
                f"""
                SELECT id, brand_name, rating, content, is_anonymous,
                       user_id, user_openid, session_hash,
                       ip_address, user_agent, created_at
                FROM brand_reviews
                {where_sql}
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
                """,
                tuple(params) + (limit, offset),
            )
            rows = cursor.fetchall() or []
            reviews = [BrandReview._admin_row(r) for r in rows]

            return {
                "reviews": reviews,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "has_more": offset + len(reviews) < total,
                },
                "filters": {"brand_name": brand_name} if brand_name else {},
            }
        except Exception as e:
            logger.error("管理后台查询评价失败: %s", e)
            return {
                "reviews": [],
                "pagination": {"page": page, "limit": limit, "total": 0, "has_more": False},
                "filters": {"brand_name": brand_name} if brand_name else {},
            }
        finally:
            if "connection" in locals():
                connection.close()
