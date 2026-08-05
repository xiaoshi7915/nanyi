#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""分享卡片页 SSR meta 注入，供微信爬虫读取链接卡片预览。"""

import html
import os
import re
import urllib.parse
from typing import Dict

import requests


def _strip_html(text: str) -> str:
    return re.sub(r'<[^>]+>', '', text or '').strip()


def _get_backend_api_base() -> str:
    """SSR 注入优先走本机 loopback，避免公网 BACKEND_URL 超时导致 meta 未注入。"""
    configured = os.environ.get('BACKEND_URL', '').rstrip('/')
    candidates = [
        'http://127.0.0.1:5432',
        'http://localhost:5432',
        configured,
    ]
    seen = set()
    for candidate in candidates:
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        try:
            response = requests.get(f"{candidate}/health", timeout=2)
            if response.ok:
                return candidate
        except Exception:
            continue
    return 'http://127.0.0.1:5432'


def _absolute_image_url(img: Dict, protocol: str, host: str) -> str:
    host = host.split(':')[0]
    base = f"{protocol}://{host}"
    default = f"{base}/static/images/牡丹亭/牡丹亭-概念图-01.jpg"

    if not img:
        return default

    medium = img.get('medium_url') or ''
    if isinstance(medium, str) and medium.startswith('http'):
        return medium

    url = img.get('url') or ''
    if isinstance(url, str) and url.startswith('http'):
        return url

    relative_path = img.get('relative_path')
    if relative_path:
        encoded = '/'.join(urllib.parse.quote(part) for part in str(relative_path).split('/'))
        return f"{base}/static/images/{encoded}"

    filename = img.get('filename')
    if filename:
        return f"{base}/static/images/{urllib.parse.quote(str(filename))}"

    return default


def _normalize_share_text(text: str, max_len: int = 80) -> str:
    """分享摘要：去 HTML、压成单行，避免 meta 标签被换行截断。"""
    cleaned = re.sub(r'\s+', ' ', _strip_html(text or '')).strip()
    if len(cleaned) > max_len:
        cleaned = cleaned[:max_len] + '...'
    return cleaned


def build_share_meta(card_data: Dict, page_url: str, protocol: str, host: str) -> Dict[str, str]:
    brand_name = card_data.get('brand_name') or '南意秋棠布料'
    raw = card_data.get('inspiration_origin') or card_data.get('inspiration') or '古典美学设计，望君着美于裳'
    body = _normalize_share_text(str(raw), 80)
    if not body:
        body = '古典美学设计，望君着美于裳'
    slogan = '传承经典 美美与共'
    if slogan not in body:
        body = f"{slogan} · {body}"

    images = card_data.get('images') or []
    share_image = _absolute_image_url(images[0] if images else None, protocol, host)
    title = f"{brand_name} - 南意秋棠"

    return {
        'title': title,
        'desc': body,
        'timeline_title': f"{title} · {slogan}",
        'image': share_image,
        'url': page_url,
    }


def _escape_meta_value(value: str) -> str:
    """meta content 必须是单行，否则微信爬虫无法解析链接卡片。"""
    single_line = re.sub(r'[\r\n\t]+', ' ', str(value or '')).strip()
    return html.escape(single_line, quote=True)


def _set_meta_content(content: str, key: str, value: str, attr: str = 'property') -> str:
    escaped = _escape_meta_value(value)
    # 先移除可能含换行的旧标签，再写入单行合法 meta
    remove_pattern = rf'<meta\s+{attr}="{re.escape(key)}"[\s\S]*?/>'
    content = re.sub(remove_pattern, '', content, count=1, flags=re.IGNORECASE)
    insert = f'    <meta {attr}="{key}" content="{escaped}" />\n'
    return content.replace('</head>', insert + '</head>', 1)


def inject_share_meta(html_content: str, meta: Dict[str, str]) -> str:
    content = html_content
    content = re.sub(
        r'<title[^>]*>[^<]*</title>',
        f"<title>{html.escape(meta['title'])}</title>",
        content,
        count=1,
    )

    content = _set_meta_content(content, 'og:title', meta['title'])
    content = _set_meta_content(content, 'og:description', meta['desc'])
    content = _set_meta_content(content, 'og:url', meta['url'])
    content = _set_meta_content(content, 'og:image', meta['image'])
    content = _set_meta_content(content, 'og:type', 'website')

    content = _set_meta_content(content, 'twitter:title', meta['title'], 'name')
    content = _set_meta_content(content, 'twitter:description', meta['desc'], 'name')
    content = _set_meta_content(content, 'twitter:image', meta['image'], 'name')

    content = _set_meta_content(content, 'name', meta['title'], 'itemprop')
    content = _set_meta_content(content, 'description', meta['desc'], 'itemprop')
    content = _set_meta_content(content, 'image', meta['image'], 'itemprop')

    for key in ('wechat:title', 'wechat:desc', 'wechat:imgUrl', 'wechat:link'):
        value = meta['title'] if key == 'wechat:title' else (
            meta['desc'] if key == 'wechat:desc' else (
                meta['image'] if key == 'wechat:imgUrl' else meta['url']
            )
        )
        content = _set_meta_content(content, key, value, 'name')

    for key, value in (
        ('weixin:appmsg_title', meta['title']),
        ('weixin:appmsg_desc', meta['desc']),
        ('weixin:timeline_title', meta['timeline_title']),
        ('weixin:timeline_desc', meta['desc']),
        ('weixin:img_url', meta['image']),
    ):
        content = _set_meta_content(content, key, value, 'name')

    summary = html.escape(meta['desc'])
    if 'id="wx-share-summary"' in content:
        content = re.sub(
            r'(<div[^>]*id="wx-share-summary"[^>]*>)(.*?)(</div>)',
            rf'\1{summary}\3',
            content,
            count=1,
            flags=re.DOTALL,
        )
    else:
        snippet = (
            f'    <div id="wx-share-summary" aria-hidden="true" '
            f'style="position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0);">'
            f'{summary}</div>\n'
        )
        content = content.replace('<body>', '<body>\n' + snippet, 1)

    return content


def load_card_html_with_share_meta(
    card_html_path: str,
    brand_name: str,
    page_url: str,
    protocol: str,
    host: str,
) -> str:
    with open(card_html_path, 'r', encoding='utf-8') as file:
        html_content = file.read()

    if not brand_name:
        return html_content

    try:
        backend_url = _get_backend_api_base()
        encoded_brand = urllib.parse.quote(brand_name, safe='')
        response = requests.get(
            f"{backend_url}/api/share/card/{encoded_brand}",
            timeout=8,
        )
        if response.ok:
            payload = response.json()
            card_data = payload.get('data') or payload.get('card_data')
            if payload.get('success') and card_data:
                meta = build_share_meta(card_data, page_url, protocol, host)
                return inject_share_meta(html_content, meta)
    except Exception:
        pass

    return html_content
