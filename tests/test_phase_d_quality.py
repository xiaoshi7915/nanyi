#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase D 质量网：JWT 烟雾、reviews wechat_mp、图片括号编码、share_meta warning、点赞 DB 失败。
缓存 clear 鉴权见 test_security_phase4（已覆盖）。
"""

from __future__ import annotations

import json
import logging
from unittest.mock import MagicMock, patch

import pytest

from backend.services.jwt_service import (
    issue_token_pair,
    verify_access_token,
    verify_refresh_token,
)
from backend.services.image_service import ImageService


class TestJwtSmoke:
    """JWT 签发/校验烟雾（不依赖微信 env）。"""

    def test_issue_and_verify_access(self, app):
        with app.app_context():
            secret = app.config["JWT_SECRET_KEY"]
            access, refresh = issue_token_pair(42, secret, 15, 7)
            assert verify_access_token(secret, access) == 42
            assert verify_refresh_token(secret, refresh) == 42
            assert verify_access_token(secret, refresh) is None
            assert verify_refresh_token(secret, access) is None

    def test_me_with_valid_jwt(self, client, app):
        with app.app_context():
            secret = app.config["JWT_SECRET_KEY"]
            access, _ = issue_token_pair(7, secret, 30, 7)

        with patch("backend.routes.auth.User") as UserMock:
            user = MagicMock()
            user.status = "active"
            user.id = 7
            user.to_public_dict.return_value = {"id": 7, "nickname": "jwt-smoke"}
            UserMock.query.get.return_value = user

            with patch(
                "backend.services.try_on_db_service.TryOnDatabaseService.count_user_tasks_in_month",
                return_value=0,
            ):
                r = client.get(
                    "/api/me",
                    headers={"Authorization": f"Bearer {access}"},
                )

        assert r.status_code == 200
        body = json.loads(r.data)
        assert body.get("user", {}).get("id") == 7
        assert "try_on_quota" in body
        assert body.get("auth", {}).get("provider") == "wechat_mp"

    def test_me_rejects_tampered_token(self, client, app):
        with app.app_context():
            secret = app.config["JWT_SECRET_KEY"]
            access, _ = issue_token_pair(1, secret, 30, 7)
        bad = access[:-4] + ("xxxx" if not access.endswith("xxxx") else "yyyy")
        r = client.get("/api/me", headers={"Authorization": f"Bearer {bad}"})
        assert r.status_code == 401


class TestReviewsProviderWechatMp:
    """评价提交取 openid 时 provider 应为 wechat_mp。"""

    def test_user_openid_queries_wechat_mp(self, app):
        from backend.routes import reviews as reviews_mod

        with app.app_context():
            with patch.object(reviews_mod, "OAuthBinding") as Binding:
                Binding.query.filter_by.return_value.first.return_value = None
                reviews_mod._user_openid(99)
                Binding.query.filter_by.assert_called_with(
                    user_id=99, provider="wechat_mp"
                )


class TestImageUrlParentheses:
    """括号路径出站编码（与 Phase A 一致，再钉一层 product 路径）。"""

    def test_encode_parentheses_in_nested_path(self):
        url = ImageService.encode_static_image_url(
            "品牌(色号)/品牌(色号)-成衣图-02.jpg"
        )
        assert url.startswith("/static/images/")
        assert "%28" in url and "%29" in url
        assert "(" not in url and ")" not in url

    def test_share_meta_absolute_image_encodes_parens(self):
        from frontend.share_meta import _absolute_image_url

        abs_url = _absolute_image_url(
            {"relative_path": "牡丹亭(灰紫)/cover.jpg"},
            "https",
            "example.com",
        )
        assert "%28" in abs_url and "%29" in abs_url
        assert "(" not in abs_url


class TestShareMetaWarningPath:
    """SSR 拉取分享卡失败时应打 warning 并回退原 HTML。"""

    def test_load_card_warns_on_backend_failure(self, tmp_path, caplog):
        from frontend.share_meta import load_card_html_with_share_meta

        html_path = tmp_path / "card.html"
        html_path.write_text(
            "<html><head></head><body>plain</body></html>", encoding="utf-8"
        )

        mock_resp = MagicMock()
        mock_resp.ok = False
        mock_resp.status_code = 503

        with caplog.at_level(logging.WARNING):
            with patch(
                "frontend.share_meta._get_backend_api_base",
                return_value="http://127.0.0.1:5432",
            ), patch("frontend.share_meta.requests.get", return_value=mock_resp):
                out = load_card_html_with_share_meta(
                    str(html_path),
                    "测试品牌",
                    "https://example.com/card.html?brand=x",
                    "https",
                    "example.com",
                )

        assert "plain" in out
        assert "og:title" not in out
        assert any("SSR share card request failed" in r.message for r in caplog.records)

    def test_load_card_warns_on_exception(self, tmp_path, caplog):
        from frontend.share_meta import load_card_html_with_share_meta

        html_path = tmp_path / "card.html"
        html_path.write_text(
            "<html><head></head><body>fallback</body></html>", encoding="utf-8"
        )

        with caplog.at_level(logging.WARNING):
            with patch(
                "frontend.share_meta._get_backend_api_base",
                return_value="http://127.0.0.1:5432",
            ), patch(
                "frontend.share_meta.requests.get",
                side_effect=ConnectionError("refused"),
            ):
                out = load_card_html_with_share_meta(
                    str(html_path),
                    "品牌",
                    "https://example.com/c",
                    "https",
                    "example.com",
                )

        assert "fallback" in out
        assert any("SSR share meta injection failed" in r.message for r in caplog.records)


class TestDbUriQuotePlus:
    """DB 密码含特殊字符时应 quote_plus。"""

    def test_password_with_at_sign_encoded(self, monkeypatch):
        monkeypatch.setenv("SECRET_KEY", "k")
        monkeypatch.setenv("DB_HOST", "127.0.0.1")
        monkeypatch.setenv("DB_USER", "u@ser")
        monkeypatch.setenv("DB_PASSWORD", "p@ss:word/x")
        monkeypatch.setenv("DB_NAME", "db")
        monkeypatch.setenv("CORS_ORIGINS", "http://localhost:8500")

        from backend.config.config import Config

        cfg = Config()
        assert "p%40ss%3Aword%2Fx" in cfg.SQLALCHEMY_DATABASE_URI
        assert "u%40ser" in cfg.SQLALCHEMY_DATABASE_URI
        # 原始未编码片段不应直接拼进 authority
        assert ":p@ss:word/x@" not in cfg.SQLALCHEMY_DATABASE_URI


class TestToggleLikeNoMemoryFallback:
    """点赞 DB 失败返回错误，不写内存。"""

    def test_controller_returns_error_on_db_raise(self):
        from backend.controllers.brand_controller import BrandController

        ctrl = BrandController()
        with patch(
            "backend.controllers.brand_controller.BrandLike.toggle_like",
            side_effect=OSError("mysql gone"),
        ):
            result = ctrl.toggle_like("品牌", "hash", "1.1.1.1", "ua")
        assert result["success"] is False
