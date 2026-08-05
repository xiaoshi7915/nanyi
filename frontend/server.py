#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
南意秋棠 - 前端静态文件服务器
"""

import os
import sys
import urllib.parse
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from flask import Flask, send_from_directory, request, Response
from flask_cors import CORS
from frontend.share_meta import load_card_html_with_share_meta

def create_frontend_app():
    """创建前端应用"""
    # 获取前端目录的绝对路径
    frontend_dir = os.path.dirname(os.path.abspath(__file__))
    
    app = Flask(__name__, 
                static_folder=None,  # 禁用默认静态文件夹，使用自定义路由
                template_folder=frontend_dir)
    
    # CORS配置
    cors_origins = os.environ.get('CORS_ORIGINS', 'http://localhost:5432').split(',')
    CORS(app, origins=cors_origins)
    
    # 静态图片路由 - 必须在通用路由之前，使用更具体的路径匹配
    @app.route('/static/images/<path:filename>')
    def static_images(filename):
        """静态图片文件服务（支持括号/中文路径）"""
        static_images_dir = os.path.join(frontend_dir, 'static', 'images')
        decoded = urllib.parse.unquote(filename)

        candidates = [decoded, filename]
        if decoded != filename:
            candidates.append(filename.replace('%28', '(').replace('%29', ')'))

        for candidate in candidates:
            file_path = os.path.join(static_images_dir, candidate)
            if os.path.exists(file_path) and os.path.isfile(file_path):
                return send_from_directory(static_images_dir, candidate)

        from flask import abort
        abort(404)
    
    @app.route('/')
    def index():
        """主页"""
        return send_from_directory(frontend_dir, 'index.html')

    @app.route('/card.html')
    def card_page():
        """分享卡片页：注入品牌级 OG/微信 meta，供链接卡片预览"""
        card_html_path = os.path.join(frontend_dir, 'card.html')
        brand_name = (request.args.get('brand') or '').strip()
        protocol = 'https' if (
            request.is_secure
            or request.headers.get('X-Forwarded-Proto') == 'https'
            or request.headers.get('X-Forwarded-Ssl') == 'on'
            or os.environ.get('FRONTEND_URL', '').startswith('https://')
        ) else 'http'
        host = request.host.split(':')[0]
        if brand_name:
            encoded_brand = urllib.parse.quote(brand_name, safe='')
            page_url = f"{protocol}://{host}/card.html?brand={encoded_brand}"
        else:
            page_url = request.url.replace('http://', f'{protocol}://', 1) if protocol == 'https' else request.url
        html_content = load_card_html_with_share_meta(
            card_html_path,
            brand_name,
            page_url,
            protocol,
            host,
        )
        return Response(html_content, mimetype='text/html; charset=utf-8')
    
    # 通用静态文件路由 - 放在最后
    @app.route('/<path:filename>')
    def static_files(filename):
        """静态文件服务"""
        if filename == 'card.html':
            return card_page()
        return send_from_directory(frontend_dir, filename)
    
    @app.route('/health')
    def health():
        """健康检查"""
        frontend_port = os.environ.get('FRONTEND_PORT', '8500')
        return {'status': 'healthy', 'service': 'nanyi-frontend', 'port': int(frontend_port)}
    
    return app

def main():
    """主函数"""
    # 获取环境变量
    port = int(os.environ.get('FRONTEND_PORT', 8500))
    host = os.environ.get('HOST', '0.0.0.0')
    backend_url = os.environ.get('BACKEND_URL', 'http://121.36.205.70:5432')
    
    # 创建应用
    app = create_frontend_app()
    
    print(f"🎨 南意秋棠前端服务启动")
    print(f"📱 本地访问: http://localhost:{port}")
    print(f"🌐 IP访问: http://121.36.205.70:{port}")
    print(f"🌐 域名访问: http://products.nanyiqiutang.cn (通过nginx代理)")
    print(f"🔗 后端API: {backend_url}")
    
    # 启动应用
    # 注意：在生产环境中禁用 debug 模式，避免自动重启导致服务退出
    app.run(
        host=host,
        port=port,
        debug=False,  # 改为 False，避免后台运行时自动重启导致进程退出
        threaded=True,
        use_reloader=False  # 禁用自动重载
    )

if __name__ == '__main__':
    main() 