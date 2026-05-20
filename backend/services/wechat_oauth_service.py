#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信 OAuth2 网页授权：code 换 access_token 与拉取 userinfo
"""

from typing import Any, Dict, Optional, Tuple

import requests

from backend.utils.logger import logger


WECHAT_TOKEN_URL = "https://api.weixin.qq.com/sns/oauth2/access_token"
WECHAT_USERINFO_URL = "https://api.weixin.qq.com/sns/userinfo"


def exchange_code_for_token(
    app_id: str, app_secret: str, code: str
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    用 code 换取 access_token 与 openid（第二步请求不含 redirect_uri）。
    成功返回 (data, None)，失败返回 (None, error_message)。
    """
    params = {
        "appid": app_id,
        "secret": app_secret,
        "code": code,
        "grant_type": "authorization_code",
    }
    try:
        r = requests.get(WECHAT_TOKEN_URL, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        logger.error("微信 access_token 请求失败: %s", e, exc_info=True)
        return None, "wechat_token_request_failed"

    if data.get("errcode"):
        err = data.get("errmsg", "unknown")
        logger.warning("微信 access_token 返回错误: %s", data)
        return None, err

    return data, None


def fetch_wechat_userinfo(access_token: str, openid: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """拉取 snsapi_userinfo 用户信息"""
    params = {"access_token": access_token, "openid": openid, "lang": "zh_CN"}
    try:
        r = requests.get(WECHAT_USERINFO_URL, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        logger.error("微信 userinfo 请求失败: %s", e, exc_info=True)
        return None, "wechat_userinfo_request_failed"

    if data.get("errcode"):
        err = data.get("errmsg", "unknown")
        logger.warning("微信 userinfo 返回错误: %s", data)
        return None, err

    return data, None
