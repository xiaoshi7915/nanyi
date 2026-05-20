#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信用户信息落库：用户 upsert 与 OAuth 绑定
"""

from typing import Any, Dict, Optional, Tuple

from backend.models import db
from backend.models.user import OAuthBinding, User


def _mask_openid(oid: str) -> str:
    """openid 脱敏展示（非微信官方微信号）"""
    if not oid:
        return ""
    if len(oid) <= 8:
        return oid[:2] + "***"
    return f"{oid[:4]}…{oid[-4:]}"


def upsert_user_from_wechat(
    openid: str,
    unionid: Optional[str],
    profile: Dict[str, Any],
) -> Tuple[User, OAuthBinding]:
    """
    根据微信 userinfo 写入或更新用户与 oauth_bindings。
    同一 (provider, openid) 已存在则更新资料。
    """
    provider = "wechat_mp"
    binding = OAuthBinding.query.filter_by(provider=provider, openid=openid).first()

    nickname = profile.get("nickname") or profile.get("nick_name")
    avatar_url = profile.get("headimgurl") or profile.get("head_img_url")
    country = profile.get("country")
    province = profile.get("province")
    city = profile.get("city")

    if binding:
        user = binding.user
        user.nickname = nickname or user.nickname
        user.avatar_url = avatar_url or user.avatar_url
        user.country = country or user.country
        user.province = province or user.province
        user.city = city or user.city
        user.display_id = user.display_id or _mask_openid(openid)
        if unionid:
            binding.unionid = unionid
        binding.raw_payload = profile
    else:
        user = User(
            nickname=nickname,
            avatar_url=avatar_url,
            country=country,
            province=province,
            city=city,
            display_id=_mask_openid(openid),
            status="active",
        )
        db.session.add(user)
        db.session.flush()
        binding = OAuthBinding(
            user_id=user.id,
            provider=provider,
            openid=openid,
            unionid=unionid,
            raw_payload=profile,
        )
        db.session.add(binding)

    db.session.commit()
    db.session.refresh(user)
    db.session.refresh(binding)
    return user, binding
