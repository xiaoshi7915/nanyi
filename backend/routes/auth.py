#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""微信网页授权、邮箱密码注册登录、JWT 续期与当前用户 /api/me"""

import re
import secrets
from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import quote, urlencode

from flask import Blueprint, current_app, jsonify, redirect, request, session

from backend.models import User, UserLoginEvent, PasswordResetToken, db
from backend.services.auth_user_service import upsert_user_from_wechat
from backend.services.jwt_service import (
    issue_token_pair,
    verify_access_token,
    verify_refresh_token,
)
from backend.services.mail_service import send_mail
from backend.services.wechat_oauth_service import (
    exchange_code_for_token,
    fetch_wechat_userinfo,
)
from backend.utils.logger import logger

auth_bp = Blueprint("auth", __name__, url_prefix="/api")

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PHONE_RE = re.compile(r"^1[3-9]\d{9}$")


def _wechat_oauth_ready():
    c = current_app.config
    return bool(c.get("WECHAT_APP_ID") and c.get("WECHAT_APP_SECRET"))


def _frontend_redirect_with_tokens(access_token: str, refresh_token: str):
    fe = current_app.config["FRONTEND_URL"].rstrip("/")
    frag = urlencode({"access_token": access_token, "refresh_token": refresh_token})
    return redirect(f"{fe}/#{frag}")


def get_bearer_user_id() -> Optional[int]:
    auth = request.headers.get("Authorization") or ""
    if not auth.lower().startswith("bearer "):
        return None
    token = auth[7:].strip()
    if not token:
        return None
    secret = current_app.config["JWT_SECRET_KEY"]
    return verify_access_token(secret, token)


def _issue_for_user(user: User, method: str = "password"):
    secret = current_app.config["JWT_SECRET_KEY"]
    am = current_app.config["JWT_ACCESS_EXPIRES_MINUTES"]
    rd = current_app.config["JWT_REFRESH_EXPIRES_DAYS"]
    access_jwt, refresh_jwt = issue_token_pair(user.id, secret, am, rd)
    try:
        ev = UserLoginEvent(
            user_id=user.id,
            method=method,
            ip=(request.headers.get("X-Forwarded-For") or request.remote_addr or "")[:64],
            user_agent=(request.headers.get("User-Agent") or "")[:512],
        )
        db.session.add(ev)
        db.session.commit()
    except Exception as e:
        logger.warning("记录登录事件失败: %s", e)
        db.session.rollback()
    return {
        "access_token": access_jwt,
        "refresh_token": refresh_jwt,
        "token_type": "Bearer",
        "expires_in": am * 60,
        "user": user.to_public_dict(),
    }


def _find_account(account: str) -> Optional[User]:
    account = (account or "").strip()
    if not account:
        return None
    if _EMAIL_RE.match(account):
        return User.query.filter_by(email=account.lower()).first()
    if _PHONE_RE.match(account):
        return User.query.filter_by(phone=account).first()
    return User.query.filter(
        (User.email == account.lower()) | (User.phone == account)
    ).first()


@auth_bp.route("/auth/register", methods=["POST"])
def register():
    body = request.get_json(silent=True) or {}
    # 注册仅要求手机号+密码；邮箱/昵称可选（前端已隐藏）
    email = (body.get("email") or "").strip().lower()
    phone = (body.get("phone") or "").strip()
    password = body.get("password") or ""
    nickname = (body.get("nickname") or "").strip() or None
    if not phone:
        return jsonify({"error": "phone_required"}), 400
    if not _PHONE_RE.match(phone):
        return jsonify({"error": "invalid_phone"}), 400
    if email and not _EMAIL_RE.match(email):
        return jsonify({"error": "invalid_email"}), 400
    if len(password) < 6:
        return jsonify({"error": "password_too_short"}), 400
    if email and User.query.filter_by(email=email).first():
        return jsonify({"error": "email_taken"}), 409
    if User.query.filter_by(phone=phone).first():
        return jsonify({"error": "phone_taken"}), 409
    # username 仍有唯一约束：用手机号占位
    uname = phone
    if User.query.filter_by(username=uname).first():
        return jsonify({"error": "account_taken"}), 409
    user = User(
        username=uname,
        email=email or None,
        phone=phone,
        nickname=nickname or phone,
        display_id=phone,
        status="active",
        updated_at=datetime.utcnow(),
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify(_issue_for_user(user, method="register")), 201


@auth_bp.route("/auth/login", methods=["POST"])
def login_password():
    body = request.get_json(silent=True) or {}
    account = body.get("account") or body.get("email") or body.get("phone") or ""
    password = body.get("password") or ""
    user = _find_account(account)
    if not user or not user.check_password(password):
        return jsonify({"error": "invalid_credentials"}), 401
    if user.status != "active":
        return jsonify({"error": "user_disabled"}), 403
    return jsonify(_issue_for_user(user, method="password"))


@auth_bp.route("/auth/forgot-password", methods=["POST"])
def forgot_password():
    body = request.get_json(silent=True) or {}
    email = (body.get("email") or "").strip().lower()
    if not email or not _EMAIL_RE.match(email):
        return jsonify({"error": "invalid_email"}), 400
    user = User.query.filter_by(email=email).first()
    if user and user.password_hash:
        token = secrets.token_urlsafe(32)
        row = PasswordResetToken(
            user_id=user.id,
            token=token,
            expires_at=datetime.utcnow() + timedelta(hours=2),
        )
        db.session.add(row)
        db.session.commit()
        fe = current_app.config["FRONTEND_URL"].rstrip("/")
        link = f"{fe}/?reset_token={quote(token)}#auth-reset"
        send_mail(
            email,
            "南意秋棠 · 重置密码",
            f"您正在重置密码。请在 2 小时内打开链接完成重置：\n{link}\n\n如非本人操作请忽略。",
        )
    return jsonify({"ok": True, "message": "若邮箱已注册，将收到重置邮件"})


@auth_bp.route("/auth/reset-password", methods=["POST"])
def reset_password():
    body = request.get_json(silent=True) or {}
    token = (body.get("token") or "").strip()
    password = body.get("password") or ""
    if not token or len(password) < 6:
        return jsonify({"error": "invalid_request"}), 400
    row = PasswordResetToken.query.filter_by(token=token).first()
    if not row or row.used_at or row.expires_at < datetime.utcnow():
        return jsonify({"error": "token_invalid"}), 400
    user = User.query.get(row.user_id)
    if not user:
        return jsonify({"error": "user_invalid"}), 400
    user.set_password(password)
    row.used_at = datetime.utcnow()
    db.session.commit()
    return jsonify(_issue_for_user(user, method="reset_password"))


@auth_bp.route("/auth/wechat/authorize")
def wechat_authorize():
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
    tokens = _issue_for_user(user, method="wechat_oauth")
    return _frontend_redirect_with_tokens(tokens["access_token"], tokens["refresh_token"])


@auth_bp.route("/auth/refresh", methods=["POST"])
def refresh_session():
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
    return jsonify({
        "access_token": access_jwt,
        "refresh_token": refresh_jwt,
        "token_type": "Bearer",
        "expires_in": am * 60,
    })


@auth_bp.route("/auth/logout", methods=["POST"])
def logout():
    return jsonify({"ok": True})


@auth_bp.route("/me", methods=["GET"])
def me():
    uid = get_bearer_user_id()
    if not uid:
        return jsonify({"error": "unauthorized", "code": "AUTH_REQUIRED"}), 401
    user = User.query.get(uid)
    if not user or user.status != "active":
        return jsonify({"error": "user_invalid", "code": "USER_INVALID"}), 401
    period = datetime.utcnow().strftime("%Y-%m")
    monthly_limit = current_app.config.get("TRY_ON_USER_MONTHLY_QUOTA", 30)
    used = 0
    try:
        from backend.services.try_on_db_service import TryOnDatabaseService
        used = TryOnDatabaseService(current_app.config).count_user_tasks_in_month(user.id, period)
    except Exception as e:
        logger.warning("统计试衣配额失败 user_id=%s: %s", user.id, e)
    return jsonify({
        "user": user.to_public_dict(),
        "auth": {
            "provider": "mixed",
            "login_method": "wechat_or_password",
            "wechat_ready": _wechat_oauth_ready(),
        },
        "try_on_quota": {
            "monthly_limit": monthly_limit,
            "used": used,
            "period": period,
        },
    })
