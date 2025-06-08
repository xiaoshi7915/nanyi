#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
南意秋棠 - 主应用程序（重构版）
"""

import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from flask import Flask, render_template
from flask_cors import CORS
from backend.config.config import config_map
from backend.models import db
from backend.routes import api_bp
from backend.utils.db_utils import init_database, create_default_admin

def create_app(config_name='development'):
    """应用工厂函数"""
    app = Flask(__name__, 
                template_folder='../frontend',
                static_folder='../frontend/static')
    
    # 加载配置
    config_class = config_map.get(config_name, config_map['default'])
    app.config.from_object(config_class)
    
    # 初始化扩展
    db.init_app(app)
    CORS(app, origins=app.config['CORS_ORIGINS'])
    
    # 注册蓝图
    app.register_blueprint(api_bp)
    
    # 注册路由
    @app.route('/')
    def index():
        """主页重定向到前端"""
        from flask import redirect
        frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:8500')
        return redirect(frontend_url)
    
    @app.route('/health')
    def health():
        """健康检查"""
        backend_port = os.environ.get('BACKEND_PORT', '5001')
        return {'status': 'healthy', 'service': 'nanyi-backend', 'port': int(backend_port)}
    
    # 错误处理
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return {'error': 'Internal server error'}, 500
    
    # 初始化数据库（仅在开发环境）
    if config_name == 'development':
        with app.app_context():
            if init_database(app):
                create_default_admin()
    
    return app

def main():
    """主函数"""
    # 获取环境变量
    config_name = os.environ.get('FLASK_ENV', 'development')
    port = int(os.environ.get('BACKEND_PORT', 5001))
    host = os.environ.get('HOST', '0.0.0.0')
    domain = os.environ.get('DOMAIN', 'localhost')
    
    # 创建应用
    app = create_app(config_name)
    
    print(f"🚀 南意秋棠后端服务启动")
    print(f"📱 本地访问: http://localhost:{port}")
    print(f"🌐 生产地址: http://{domain}:{port}")
    print(f"🔧 环境: {config_name}")
    print(f"💾 数据库: {app.config['SQLALCHEMY_DATABASE_URI'].split('@')[1] if '@' in app.config['SQLALCHEMY_DATABASE_URI'] else 'N/A'}")
    
    # 启动应用
    app.run(
        host=host,
        port=port,
        debug=app.config['DEBUG'],
        threaded=True
    )

if __name__ == '__main__':
    main() 