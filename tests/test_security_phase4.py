#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 4 安全相关验收用例：试衣 access_token、缓存 pattern、Markdown 输出子集、SSE 并发烟雾测试。
"""

from __future__ import annotations

import json
import re
from unittest.mock import patch

import pytest

from backend.exceptions import PermissionError as TryOnPermissionError
from backend.utils.validators import validate_cache_clear_pattern


# --- 与 frontend/index.html 中 escapeHtml + formatMarkdown 逻辑保持一致（变更前端时请同步） ---

def _escape_html(s):
    if s is None:
        return ""
    t = str(s).replace("\r\n", "\n").replace("\r", "\n")
    return (
        t.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def format_markdown_like_frontend(text):
    if not text:
        return ""
    s = _escape_html(str(text).replace("\r\n", "\n").replace("\r", "\n"))
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s, flags=re.DOTALL)
    s = re.sub(r"__(.+?)__", r"<strong>\1</strong>", s, flags=re.DOTALL)
    s = re.sub(r"\*([^*\n]+)\*", r"<em>\1</em>", s)
    s = re.sub(r"_([^_\n]+)_", r"<em>\1</em>", s)
    parts = re.split(r"\n\n+", s)
    return "".join("<p>" + p.replace("\n", "<br>") + "</p>" for p in parts)


class TestTryOnAccessToken:
    """GET /api/try-on/status 与 /stream 在 token 无效时应 403。"""

    def test_status_forbidden_without_token(self, client):
        with patch("backend.routes.try_on.try_on_controller.get_task_status") as m:
            m.side_effect = TryOnPermissionError("缺少试衣任务访问凭证（access_token）")
            r = client.get("/api/try-on/status/fake-task-id")
            assert r.status_code == 403
            body = json.loads(r.data)
            assert body.get("success") is False

    def test_status_forbidden_wrong_token(self, client):
        with patch("backend.routes.try_on.try_on_controller.get_task_status") as m:
            m.side_effect = TryOnPermissionError("试衣任务访问凭证无效")
            r = client.get(
                "/api/try-on/status/fake-task-id?access_token=wrong"
            )
            assert r.status_code == 403

    def test_stream_forbidden_wrong_token(self, client):
        with patch("backend.routes.try_on.try_on_controller.get_task_status") as m:
            m.side_effect = TryOnPermissionError("试衣任务访问凭证无效")
            r = client.get(
                "/api/try-on/stream/fake-task-id?access_token=bad"
            )
            assert r.status_code == 403


class TestCacheClearPattern:
    """POST /api/cache/clear 的 pattern 校验。"""

    def test_clear_rejects_oversized_pattern(self, client):
        r = client.post(
            "/api/cache/clear",
            data=json.dumps({"pattern": "a" * 201}),
            content_type="application/json",
        )
        assert r.status_code == 400

    def test_clear_rejects_unsafe_characters(self, client):
        r = client.post(
            "/api/cache/clear",
            data=json.dumps({"pattern": ".*(a+)+$"}),
            content_type="application/json",
        )
        assert r.status_code == 400

    def test_clear_accepts_safe_literal(self, client):
        with patch("backend.routes.api.cache_service.clear_pattern") as clear:
            r = client.post(
                "/api/cache/clear",
                data=json.dumps({"pattern": "images/brands_"}),
                content_type="application/json",
            )
            assert r.status_code == 200
            clear.assert_called_once_with("images/brands_")

    def test_validate_default_pattern(self):
        assert validate_cache_clear_pattern(None) == ".*"
        assert validate_cache_clear_pattern(".*") == ".*"


class TestFormatMarkdownXSSSubset:
    """formatMarkdown 仅允许转义后的文本 + 有限 strong/em/p/br。"""

    @pytest.mark.parametrize(
        "malicious",
        [
            '<script>alert(1)</script>',
            '<img src=x onerror=alert(1)>',
            '"><svg onload=alert(1)>',
        ],
    )
    def test_no_unescaped_active_markup(self, malicious):
        out = format_markdown_like_frontend(malicious)
        ol = out.lower()
        # 允许文本中出现 onerror= 等子串（已整体转义为纯文本）；禁止未转义的活跃标签
        assert "<script" not in ol
        assert "<img" not in ol
        assert "<svg" not in ol
        assert "javascript:" not in ol

    def test_bold_and_paragraph_allowed(self):
        out = format_markdown_like_frontend("Hello **world**\n\nSecond line.")
        assert "<strong>world</strong>" in out
        assert out.startswith("<p>")
        assert "<br>" in out or "</p><p>" in out


class TestIndexHtmlMarkdownUsesEscape:
    """静态断言：详情页 v-html 使用的 formatMarkdown 仍先经过 escapeHtml。"""

    def test_index_html_escape_before_markdown(self):
        from pathlib import Path

        root = Path(__file__).resolve().parents[1]
        html = (root / "frontend" / "index.html").read_text(encoding="utf-8", errors="replace")
        assert "escapeHtml" in html and "formatMarkdown" in html
        # formatMarkdown 内应调用 escapeHtml（防止绕过）
        m = re.search(
            r"formatMarkdown\s*\([^)]*\)\s*\{[^}]{0,800}",
            html,
            re.DOTALL,
        )
        assert m, "formatMarkdown 块未找到"
        block = m.group(0)
        assert "escapeHtml" in block, "formatMarkdown 应内含 escapeHtml 调用"


class TestSSEConcurrencySmoke:
    """连续多次请求 SSE（任务立即完成），验证流式响应可正常结束（gthread 场景烟雾测试）。"""

    def test_multiple_streams_complete_sequentially(self, client):
        payload = {
            "success": True,
            "status": "completed",
            "result_image_url": None,
            "progress": 100,
            "error": None,
        }

        with patch(
            "backend.routes.try_on.try_on_controller.get_task_status",
            return_value=payload,
        ):
            for i in range(8):
                r = client.get(
                    f"/api/try-on/stream/t-{i}?access_token=ok",
                    buffered=False,
                )
                assert r.status_code == 200, (i, r.status_code)
                # 消费生成器，避免测试客户端悬挂
                _ = r.get_data()
