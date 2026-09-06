#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""登录用户中心：浏览足迹、我的试穿。"""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from backend.models import UserAsset, UserBrowseEvent, db
from backend.routes.auth import get_bearer_user_id

user_bp = Blueprint("user_center", __name__, url_prefix="/api")


@user_bp.route("/me/browse", methods=["POST"])
def record_browse():
    uid = get_bearer_user_id()
    if not uid:
        return jsonify({"error": "unauthorized"}), 401
    body = request.get_json(silent=True) or {}
    brand = (body.get("brand_name") or body.get("brand") or "").strip()
    if not brand:
        return jsonify({"error": "brand_required"}), 400
    ev = UserBrowseEvent(user_id=uid, brand_name=brand[:191])
    db.session.add(ev)
    db.session.commit()
    return jsonify({"ok": True})


@user_bp.route("/me/browse", methods=["GET"])
def list_browse():
    uid = get_bearer_user_id()
    if not uid:
        return jsonify({"error": "unauthorized"}), 401
    limit = min(int(request.args.get("limit") or 30), 100)
    rows = (
        UserBrowseEvent.query.filter_by(user_id=uid)
        .order_by(UserBrowseEvent.created_at.desc())
        .limit(limit)
        .all()
    )
    # 去重保留最近
    seen = set()
    items = []
    for r in rows:
        if r.brand_name in seen:
            continue
        seen.add(r.brand_name)
        items.append(
            {
                "brand_name": r.brand_name,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
        )
    return jsonify({"items": items})


@user_bp.route("/me/try-on-assets", methods=["GET"])
def list_try_on_assets():
    uid = get_bearer_user_id()
    if not uid:
        return jsonify({"error": "unauthorized"}), 401
    limit = min(int(request.args.get("limit") or 40), 100)
    rows = (
        UserAsset.query.filter_by(user_id=uid)
        .order_by(UserAsset.created_at.desc())
        .limit(limit)
        .all()
    )
    items = [
        {
            "id": r.id,
            "type": r.type,
            "task_id": r.task_id,
            "url": r.url,
            "storage_key": r.storage_key,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]
    return jsonify({"items": items})
