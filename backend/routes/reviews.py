#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
品牌评价 API
- POST /api/reviews 提交评价（可选登录，登录时记录 user_id / openid）
- GET  /api/reviews/brand/<brand_name> 公开列表（不含用户 PII）
"""

import hashlib
import urllib.parse

from flask import Blueprint, request

from backend.models.brand_review import BrandReview
from backend.models.user import OAuthBinding
from backend.routes.auth import get_bearer_user_id
from backend.utils.client_ip import get_trusted_client_ip
from backend.utils.decorators import handle_errors, require_json
from backend.utils.rate_limit import rate_limit
from backend.utils.response import APIResponse

reviews_bp = Blueprint("reviews", __name__, url_prefix="/api")


def _session_hash() -> str:
    """未登录用户用 IP + UA 生成会话哈希（与点赞逻辑类似）"""
    client_ip = get_trusted_client_ip()
    user_agent = request.environ.get("HTTP_USER_AGENT", "")
    raw = f"{client_ip}_{user_agent}"
    return hashlib.md5(raw.encode()).hexdigest()


def _user_openid(user_id: int):
    """查询用户微信 openid（审计字段）"""
    if not user_id:
        return None
    binding = OAuthBinding.query.filter_by(user_id=user_id, provider="wechat").first()
    return binding.openid if binding else None


@reviews_bp.route("/reviews", methods=["POST"])
@rate_limit(max_requests=15, per_seconds=60, scope="review_submit")
@require_json
@handle_errors
def submit_review():
    """提交品牌评价"""
    data = request.get_json() or {}
    brand_name = data.get("brand_name")
    rating = data.get("rating")
    content = data.get("content")
    # 前端可传 is_anonymous，默认 True；公开接口始终显示匿名用户
    is_anonymous = data.get("is_anonymous", True)
    if isinstance(is_anonymous, str):
        is_anonymous = is_anonymous.lower() not in ("0", "false", "no")

    user_id = get_bearer_user_id()
    user_openid = _user_openid(user_id) if user_id else None
    session_hash = None if user_id else _session_hash()

    client_ip = get_trusted_client_ip()
    user_agent = request.environ.get("HTTP_USER_AGENT", "")

    success, result = BrandReview.add_review(
        brand_name=brand_name,
        rating=rating,
        content=content,
        is_anonymous=bool(is_anonymous),
        user_id=user_id,
        user_openid=user_openid,
        session_hash=session_hash,
        ip_address=client_ip,
        user_agent=user_agent,
    )

    if success:
        return APIResponse.success(data=result, message="评价提交成功")
    return APIResponse.error(message=str(result), status_code=400)


@reviews_bp.route("/reviews/brand/<path:brand_name>", methods=["GET"])
@rate_limit(max_requests=120, per_seconds=60, scope="review_list")
@handle_errors
def list_brand_reviews(brand_name: str):
    """获取某品牌的公开评价列表（含统计）"""
    decoded = urllib.parse.unquote(brand_name, encoding="utf-8")
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 20, type=int)

    payload = BrandReview.list_by_brand(decoded, page=page, limit=limit)
    return APIResponse.success(data=payload, message="查询成功")
