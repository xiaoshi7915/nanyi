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
    # 获取前端目录的绝对路径
    frontend_dir = os.path.dirname(os.path.abspath(__file__))
    
    app = Flask(__name__, 
                static_folder=os.path.join(frontend_dir, 'static'),
                template_folder=frontend_dir)
    
    # CORS配置
    cors_origins = os.environ.get('CORS_ORIGINS', 'http://localhost:5432').split(',')
    CORS(app, origins=cors_origins)
    
    @app.route('/')
    def index():
        """主页"""
        return send_from_directory(frontend_dir, 'index.html')
    
    @app.route('/<path:filename>')
    def static_files(filename):
        """静态文件服务"""
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