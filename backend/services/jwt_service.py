#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JWT 签发与校验：access token + refresh token（无状态，续期靠 refresh）
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple

import jwt


def issue_token_pair(
    user_id: int,
    secret: str,
    access_minutes: int,
    refresh_days: int,
) -> Tuple[str, str]:
    """生成 access 与 refresh 两个 JWT"""
    now = datetime.utcnow()
    access_payload: Dict[str, Any] = {
        "sub": str(user_id),
        "typ": "access",
        "iat": now,
        "exp": now + timedelta(minutes=access_minutes),
    }
    refresh_payload: Dict[str, Any] = {
        "sub": str(user_id),
        "typ": "refresh",
        "iat": now,
        "exp": now + timedelta(days=refresh_days),
    }
    access_token = jwt.encode(access_payload, secret, algorithm="HS256")
    refresh_token = jwt.encode(refresh_payload, secret, algorithm="HS256")
    if isinstance(access_token, bytes):
        access_token = access_token.decode("utf-8")
    if isinstance(refresh_token, bytes):
        refresh_token = refresh_token.decode("utf-8")
    return access_token, refresh_token


def decode_token(secret: str, token: str) -> Dict[str, Any]:
    """解码并校验 JWT，失败抛 jwt.PyJWTError"""
    return jwt.decode(token, secret, algorithms=["HS256"])


def verify_access_token(secret: str, token: str) -> Optional[int]:
    """校验 access token，返回 user_id；类型或过期则返回 None"""
    try:
        payload = decode_token(secret, token)
        if payload.get("typ") != "access":
            return None
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError, TypeError):
        return None


def verify_refresh_token(secret: str, token: str) -> Optional[int]:
    """校验 refresh token，返回 user_id"""
    try:
        payload = decode_token(secret, token)
        if payload.get("typ") != "refresh":
            return None
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError, TypeError):
        return None
