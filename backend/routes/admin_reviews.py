#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
管理后台 - 品牌评价审计 API（含 user_id、openid 等，仅管理员可访问）
"""

import urllib.parse

from flask import Blueprint, request

from backend.models.brand_review import BrandReview
from backend.utils.admin_auth import require_admin_api_token
from backend.utils.decorators import handle_errors
from backend.utils.response import APIResponse

admin_reviews_bp = Blueprint("admin_reviews", __name__, url_prefix="/api/admin")


@admin_reviews_bp.route("/reviews", methods=["GET"])
@require_admin_api_token
@handle_errors
def list_reviews_admin():
    """
    分页列出全部评价（含审计字段）
    Query: page, limit, brand_name（可选，模糊匹配）
    """
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 50, type=int)
    brand_name = request.args.get("brand_name", type=str)
    if brand_name:
        brand_name = urllib.parse.unquote(brand_name, encoding="utf-8").strip() or None

    payload = BrandReview.list_admin(page=page, limit=limit, brand_name=brand_name)
    return APIResponse.success(data=payload, message="查询成功")
