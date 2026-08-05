#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信网页授权、JWT 续期与当前用户 /api/me
"""

import secrets
from datetime import datetime
from typing import Optional
from urllib.parse import quote, urlencode

from flask import Blueprint, current_app, jsonify, redirect, request, session

from backend.models import User
from backend.services.auth_user_service import upsert_user_from_wechat
from backend.services.jwt_service import (
    issue_token_pair,
    verify_access_token,
    verify_refresh_token,
)
from backend.services.wechat_oauth_service import (
    exchange_code_for_token,
    fetch_wechat_userinfo,
)
from backend.utils.logger import logger

auth_bp = Blueprint("auth", __name__, url_prefix="/api")


def _wechat_oauth_ready():
    c = current_app.config
    return bool(c.get("WECHAT_APP_ID") and c.get("WECHAT_APP_SECRET"))


def _frontend_redirect_with_tokens(access_token: str, refresh_token: str):
    """授权成功后回到前端，token 放在 URL fragment，避免进入访问日志 query"""
    fe = current_app.config["FRONTEND_URL"].rstrip("/")
    frag = urlencode({"access_token": access_token, "refresh_token": refresh_token})
    return redirect(f"{fe}/#{frag}")


def get_bearer_user_id() -> Optional[int]:
    """从 Authorization: Bearer 解析当前用户 id"""
    auth = request.headers.get("Authorization") or ""
    if not auth.lower().startswith("bearer "):
        return None
    token = auth[7:].strip()
    if not token:
        return None
    secret = current_app.config["JWT_SECRET_KEY"]
    return verify_access_token(secret, token)


@auth_bp.route("/auth/wechat/authorize")
def wechat_authorize():
    """重定向到微信授权页（需配置 WECHAT_APP_ID / SECRET）"""
    if not _wechat_oauth_ready():
        return jsonify({"error": "wechat_oauth_not_configured"}), 503
    state = secrets.token_urlsafe(24)
    session["wx_oauth_state"] = state
    app_id = current_app.config["WECHAT_APP_ID"]
    redirect_uri = quote(current_app.config["WECHAT_OAUTH_REDIRECT_URI"], safe="")
    auth_url = (
        "https://open.weixin.qq.com/connect/oauth2/authorize"
        f"?appid={app_id}&redirect_uri={redirect_uri}&response_type=code"
        f"&scope=snsapi_userinfo&state={state}#wechat_redirect"
    )
    return redirect(auth_url)


@auth_bp.route("/auth/wechat/callback")
def wechat_callback():
    """微信回调：换 token、拉用户信息、签发 JWT、重定向回前端（fragment 带 token）"""
    code = request.args.get("code")
    state = request.args.get("state")
    err = request.args.get("error")
    if err:
        logger.warning("微信授权用户拒绝或失败: %s", request.args)
        fe = current_app.config["FRONTEND_URL"].rstrip("/")
        return redirect(f"{fe}/#wechat_oauth_error={quote(err)}")
    if not code:
        return jsonify({"error": "missing_code"}), 400
    if not state or state != session.get("wx_oauth_state"):
        return jsonify({"error": "invalid_state"}), 400
    session.pop("wx_oauth_state", None)

    if not _wechat_oauth_ready():
        return jsonify({"error": "wechat_oauth_not_configured"}), 503

    app_id = current_app.config["WECHAT_APP_ID"]
    app_secret = current_app.config["WECHAT_APP_SECRET"]

    token_data, terr = exchange_code_for_token(app_id, app_secret, code)
    if not token_data:
        return jsonify({"error": "wechat_token_failed", "detail": terr}), 400

    access_token_wx = token_data.get("access_token")
    openid = token_data.get("openid")
    unionid = token_data.get("unionid")
    if not access_token_wx or not openid:
        return jsonify({"error": "wechat_token_incomplete"}), 400

    profile, uerr = fetch_wechat_userinfo(access_token_wx, openid)
    if not profile:
        return jsonify({"error": "wechat_userinfo_failed", "detail": uerr}), 400

    user, _binding = upsert_user_from_wechat(openid, unionid, profile)

    secret = current_app.config["JWT_SECRET_KEY"]
    am = current_app.config["JWT_ACCESS_EXPIRES_MINUTES"]
    rd = current_app.config["JWT_REFRESH_EXPIRES_DAYS"]
    access_jwt, refresh_jwt = issue_token_pair(user.id, secret, am, rd)
    return _frontend_redirect_with_tokens(access_jwt, refresh_jwt)


@auth_bp.route("/auth/refresh", methods=["POST"])
def refresh_session():
    """用 refresh_token 换取新的 access + refresh（静默续期，无需再打开微信授权）"""
    body = request.get_json(silent=True) or {}
    refresh_tok = body.get("refresh_token")
    if not refresh_tok:
        return jsonify({"error": "missing_refresh_token", "code": "REFRESH_REQUIRED"}), 400

    secret = current_app.config["JWT_SECRET_KEY"]
    uid = verify_refresh_token(secret, refresh_tok)
    if not uid:
        return jsonify({"error": "invalid_refresh_token", "code": "REFRESH_INVALID"}), 401

    user = User.query.get(uid)
    if not user or user.status != "active":
        return jsonify({"error": "user_invalid", "code": "USER_INVALID"}), 401

    am = current_app.config["JWT_ACCESS_EXPIRES_MINUTES"]
    rd = current_app.config["JWT_REFRESH_EXPIRES_DAYS"]
    access_jwt, refresh_jwt = issue_token_pair(user.id, secret, am, rd)
    return jsonify(
        {
            "access_token": access_jwt,
            "refresh_token": refresh_jwt,
            "token_type": "Bearer",
            "expires_in": am * 60,
        }
    )


@auth_bp.route("/me", methods=["GET"])
def me():
    """当前登录用户资料（依赖 Bearer access token；回访只带本地 token 即可，无需微信）"""
    uid = get_bearer_user_id()
    if not uid:
        return jsonify({"error": "unauthorized", "code": "AUTH_REQUIRED"}), 401

    user = User.query.get(uid)
    if not user or user.status != "active":
        return jsonify({"error": "user_invalid", "code": "USER_INVALID"}), 401

    period = datetime.utcnow().strftime("%Y-%m")
    monthly_limit = current_app.config.get("TRY_ON_USER_MONTHLY_QUOTA", 30)

    # 按 tasks.user_id + 自然月统计；无 user_id 的历史/匿名任务不计入
    used = 0
    try:
        from backend.services.try_on_db_service import TryOnDatabaseService

        used = TryOnDatabaseService(current_app.config).count_user_tasks_in_month(
            user.id, period
        )
    except Exception as e:
        logger.warning("统计试衣配额失败 user_id=%s: %s", user.id, e)
        used = 0

    return jsonify(
        {
            "user": user.to_public_dict(),
            "auth": {
                "provider": "wechat_mp",
                "login_method": "wechat_oauth",
                "note": "回访免授权依赖本地 JWT + refresh，非微信自动跳过授权页",
            },
            "try_on_quota": {
                "monthly_limit": monthly_limit,
                "used": used,
                "period": period,
            },
        }
    )
