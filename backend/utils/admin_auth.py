#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
管理后台 API 鉴权：通过环境变量 ADMIN_API_TOKEN 校验请求头 X-Admin-Token
"""

from functools import wraps

from flask import current_app, request

from backend.utils.response import APIResponse


def _get_admin_token_from_request() -> str:
    """从 X-Admin-Token 或 Authorization: Bearer <token> 读取管理令牌"""
    token = (request.headers.get("X-Admin-Token") or "").strip()
    if token:
        return token
    auth = request.headers.get("Authorization") or ""
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return ""


def require_admin_api_token(f):
    """要求有效的 ADMIN_API_TOKEN（未配置时拒绝访问）"""

    @wraps(f)
    def decorated(*args, **kwargs):
        expected = (current_app.config.get("ADMIN_API_TOKEN") or "").strip()
        if not expected:
            return APIResponse.error(
                message="管理接口未配置 ADMIN_API_TOKEN",
                error_code="ADMIN_NOT_CONFIGURED",
                status_code=503,
            )
        provided = _get_admin_token_from_request()
        if not provided or provided != expected:
            return APIResponse.error(
                message="无效的管理员令牌",
                error_code="ADMIN_UNAUTHORIZED",
                status_code=401,
            )
        return f(*args, **kwargs)

    return decorated
