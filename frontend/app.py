#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
南意秋棠 - 前端服务器
"""

import os
import sys
from flask import Flask, render_template, send_from_directory

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def create_app():
    """创建前端Flask应用"""
    app = Flask(__name__, 
                template_folder='.',
                static_folder='static')
    
    # 基本配置
    app.config['SECRET_KEY'] = 'nanyi_frontend_key_2024'
    app.config['DEBUG'] = True
    
    @app.route('/')
    def index():
        """主页"""
        return send_from_directory('.', 'index.html')
    
    @app.route('/health')
    def health():
        """健康检查"""
        return {
            'status': 'healthy',
            'service': 'nanyi-frontend',
            'port': 8500,
            'backend_api': 'http://121.36.205.70:5001/api'
        }
    
    @app.route('/js/<path:filename>')
    def serve_js(filename):
        """提供JavaScript文件"""
        return send_from_directory('js', filename)
    
    @app.route('/css/<path:filename>')
    def serve_css(filename):
        """提供CSS文件"""
        return send_from_directory('css', filename)
    
    # 静态文件路由 - 移除自定义路由，使用Flask默认处理
    
    # 错误处理
    @app.errorhandler(404)
    def not_found(error):
        # 如果是静态文件请求，返回404而不是index.html
        if error.description and '/static/' in str(error.description):
            return {'error': 'File not found'}, 404
        return send_from_directory('.', 'index.html')  # SPA路由处理
    
    return app

def main():
    """主函数"""
    app = create_app()
    
    port = 8500
    host = '0.0.0.0'
    
    print(f"🎨 南意秋棠前端服务启动")
    print(f"📱 本地访问: http://localhost:{port}")
    print(f"🌐 生产访问: http://121.36.205.70:{port}")
    print(f"🔗 后端API: http://121.36.205.70:5001/api")
    print(f"💡 健康检查: http://121.36.205.70:{port}/health")
    
    # 启动应用
    app.run(
        host=host,
        port=port,
        debug=True,
        threaded=True
    )

if __name__ == '__main__':
    main() 