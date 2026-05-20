#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户、OAuth 绑定与资产模型（微信登录与试衣相册等）
"""

from datetime import datetime
from . import db


class User(db.Model):
    """站内用户"""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nickname = db.Column(db.String(128), nullable=True)
    avatar_url = db.Column(db.String(512), nullable=True)
    country = db.Column(db.String(64), nullable=True)
    province = db.Column(db.String(64), nullable=True)
    city = db.Column(db.String(64), nullable=True)
    phone = db.Column(db.String(32), nullable=True, unique=True, index=True)
    display_id = db.Column(db.String(64), nullable=True, index=True)
    status = db.Column(db.String(20), nullable=False, default="active", index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    oauth_bindings = db.relationship(
        "OAuthBinding", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )
    assets = db.relationship(
        "UserAsset", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )

    def to_public_dict(self):
        """供 /api/me 返回的安全字段"""
        return {
            "id": self.id,
            "nickname": self.nickname,
            "avatar_url": self.avatar_url,
            "country": self.country,
            "province": self.province,
            "city": self.city,
            "phone": self.phone,
            "display_id": self.display_id,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class OAuthBinding(db.Model):
    """第三方 OAuth 与站内用户绑定"""

    __tablename__ = "oauth_bindings"
    __table_args__ = (
        db.UniqueConstraint("provider", "openid", name="uk_oauth_provider_openid"),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider = db.Column(db.String(32), nullable=False, index=True)
    openid = db.Column(db.String(64), nullable=False)
    unionid = db.Column(db.String(64), nullable=True, index=True)
    raw_payload = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class UserAsset(db.Model):
    """用户上传图 / 试衣结果等元数据"""

    __tablename__ = "user_assets"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type = db.Column(db.String(32), nullable=False, index=True)
    # 对应 tasks.id（VARCHAR(36)）；表级外键由迁移脚本维护
    task_id = db.Column(db.String(36), nullable=True, index=True)
    storage_key = db.Column(db.String(512), nullable=True)
    url = db.Column(db.Text, nullable=True)
    mime = db.Column(db.String(128), nullable=True)
    size = db.Column(db.BigInteger, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
