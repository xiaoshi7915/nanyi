#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
客户端 IP：避免直接使用可伪造的 X-Forwarded-For。
若部署在受信反代后，应在应用中启用 ProxyFix（或等价配置），
以便 Werkzeug 将 request.remote_addr 解析为真实客户端地址。
"""

from flask import request


def get_trusted_client_ip() -> str:
    """返回当前请求的客户端 IP（不信任客户端自行传入的 X-Forwarded-For）。"""
    return request.remote_addr or 'unknown'
