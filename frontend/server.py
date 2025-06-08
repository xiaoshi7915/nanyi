#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
南意秋棠 - 前端静态文件服务器
"""

import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from flask import Flask, send_from_directory, render_template_string
from flask_cors import CORS

def create_frontend_app():
    """创建前端应用"""
    app = Flask(__name__, 
                static_folder='static',
                template_folder='.')
    
    # CORS配置
    cors_origins = os.environ.get('CORS_ORIGINS', 'http://localhost:5001').split(',')
    CORS(app, origins=cors_origins)
    
    @app.route('/')
    def index():
        """主页"""
        return send_from_directory('.', 'index.html')
    
    @app.route('/<path:filename>')
    def static_files(filename):
        """静态文件服务"""
        return send_from_directory('.', filename)
    
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
    domain = os.environ.get('DOMAIN', 'localhost')
    backend_url = os.environ.get('BACKEND_URL', 'http://localhost:5001')
    
    # 创建应用
    app = create_frontend_app()
    
    print(f"🎨 南意秋棠前端服务启动")
    print(f"📱 本地访问: http://localhost:{port}")
    print(f"🌐 生产地址: http://{domain}:{port}")
    print(f"🔗 后端API: {backend_url}")
    
    # 启动应用
    app.run(
        host=host,
        port=port,
        debug=True,
        threaded=True
    )

if __name__ == '__main__':
    main() 