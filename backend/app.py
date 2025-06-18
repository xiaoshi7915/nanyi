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
from backend.models import db, init_models
from backend.utils.logger import setup_logging
from backend.utils.cache_control import init_cache_control_helpers

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
    
    # 正式CORS配置，支持所有必要的域名
    cors_origins = [
        'http://localhost:8500',
        'http://127.0.0.1:8500', 
        'http://121.36.205.70:8500',
        'http://chenxiaoshivivid.com.cn:8500',
        'http://www.chenxiaoshivivid.com.cn:8500'
    ]
    
    CORS(app, 
         origins=cors_origins,
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
         allow_headers=['Content-Type', 'Authorization', 'Access-Control-Allow-Credentials'],
         supports_credentials=True)
    
    # 初始化日志
    setup_logging(app)
    
    # 初始化缓存控制
    init_cache_control_helpers(app)
    
    # 在应用上下文中初始化模型
    with app.app_context():
        # 初始化模型
        Product, Admin, AccessLog = init_models()
        
        # 测试数据库连接
        try:
            # 尝试连接数据库
            db.engine.connect()
            print("✅ 数据库连接成功")
            
            # 创建表
            db.create_all()
            print("✅ 数据表创建成功")
            
            # 创建默认管理员（如果不存在）
            if Admin:
                admin = Admin.query.filter_by(username='admin').first()
                if not admin:
                    admin = Admin(username='admin', email='admin@nanyi.com')
                    admin.set_password('admin123')
                    db.session.add(admin)
                    db.session.commit()
                    print("✅ 默认管理员创建成功")
                    
        except Exception as e:
            print(f"❌ 数据库初始化失败: {e}")
            # 不中断服务，继续启动
    
    # 延迟导入路由，避免循环导入
    try:
        from backend.routes import api_bp
        app.register_blueprint(api_bp)
        print("✅ API路由注册成功")
    except ImportError as e:
        print(f"警告: 路由导入失败 - {e}")
    
    # 注册基本路由
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
        try:
            # 测试数据库连接
            db.engine.connect()
            db_status = 'connected'
        except:
            db_status = 'disconnected'
            
        return {
            'status': 'healthy', 
            'service': 'nanyi-backend', 
            'port': int(backend_port),
            'database': db_status
        }
    
    # 错误处理
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return {'error': 'Internal server error'}, 500
    
    return app

def main():
    """主函数"""
    # 获取环境变量
    config_name = os.environ.get('FLASK_ENV', 'development')
    port = int(os.environ.get('BACKEND_PORT', 5001))
    host = os.environ.get('HOST', '0.0.0.0')
    domain = os.environ.get('DOMAIN', 'chenxiaoshivivid.com.cn')
    
    # 创建应用
    app = create_app(config_name)
    
    print(f"🚀 南意秋棠后端服务启动")
    print(f"📱 本地访问: http://localhost:{port}")
    print(f"🌐 域名访问: http://{domain}:{port}")
    print(f"🌐 IP访问: http://121.36.205.70:{port}")
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