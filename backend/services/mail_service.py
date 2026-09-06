#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""发信：忘记密码 / 可选通知。未配置 SMTP 时仅打日志。"""

from __future__ import annotations

import smtplib
from email.mime.text import MIMEText
from typing import Tuple

from flask import current_app

from backend.utils.logger import logger


def send_mail(to_email: str, subject: str, body: str) -> Tuple[bool, str]:
    host = (current_app.config.get("SMTP_HOST") or "").strip()
    user = (current_app.config.get("SMTP_USER") or "").strip()
    password = current_app.config.get("SMTP_PASSWORD") or ""
    port = int(current_app.config.get("SMTP_PORT") or 465)
    mail_from = (current_app.config.get("SMTP_FROM") or user or "").strip()
    use_ssl = str(current_app.config.get("SMTP_SSL", "true")).lower() in (
        "1",
        "true",
        "yes",
    )

    if not (host and user and to_email):
        logger.warning("SMTP 未配置，邮件未发送 to=%s subject=%s", to_email, subject)
        logger.info("邮件正文预览:\n%s", body[:800])
        return False, "smtp_unconfigured"

    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = mail_from
        msg["To"] = to_email
        if use_ssl:
            with smtplib.SMTP_SSL(host, port, timeout=20) as s:
                s.login(user, password)
                s.sendmail(mail_from, [to_email], msg.as_string())
        else:
            with smtplib.SMTP(host, port, timeout=20) as s:
                s.starttls()
                s.login(user, password)
                s.sendmail(mail_from, [to_email], msg.as_string())
        return True, "sent"
    except Exception as e:  # noqa: BLE001
        logger.exception("发信失败: %s", e)
        return False, str(e)
