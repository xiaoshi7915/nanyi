#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
南意秋棠 - 主应用程序（重构版）
"""

import os
import sys
from dotenv import load_dotenv

# 清理系统Python路径，避免版本冲突
sys.path = [p for p in sys.path if '/usr/local/lib/python3.8/site-packages' not in p]

# 加载环境变量
load_dotenv()

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from flask import Flask, render_template, request, session
from flask_cors import CORS
from flask_restx import Api, Resource, fields
from backend.config.config import config_map
from backend.models import db, init_models
from backend.utils.logger import setup_logging, logger
from backend.utils.cache_control import init_cache_control_helpers
from datetime import datetime
import secrets
import gzip
from functools import wraps

def create_app(config_name='development'):
    """应用工厂函数"""
    app = Flask(__name__, 
                template_folder='../frontend',
                static_folder='../frontend/static')
    
    # 加载配置
    config_class = config_map.get(config_name, config_map['default'])
    # 如果配置类是类，需要实例化，传递config_name以便CORS配置判断环境
    if isinstance(config_class, type):
        config_instance = config_class(config_name=config_name)
        app.config.from_object(config_instance)
    else:
        app.config.from_object(config_class)
    
    # 初始化扩展
    db.init_app(app)
    
    # CORS配置 - 从配置类读取，仅允许HTTPS域名（开发环境允许localhost）
    # 配置类已经验证了域名格式，这里直接使用
    cors_origins = app.config.get('CORS_ORIGINS', [])
    
    # 如果配置为空，使用默认值（仅用于开发环境）
    if not cors_origins and config_name == 'development':
        cors_origins = ['http://localhost:8500', 'http://127.0.0.1:8500']
    
    CORS(app, 
         origins=cors_origins,
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
         allow_headers=['Content-Type', 'Authorization', 'Access-Control-Allow-Credentials', 'X-Requested-With', 'X-CSRF-Token'],
         supports_credentials=True,
         expose_headers=['X-CSRF-Token'])
    
    # CSRF保护 - 使用Flask内置的CSRF保护机制
    # 为每个会话生成CSRF token
    @app.before_request
    def csrf_protect():
        """CSRF保护中间件"""
        # 跳过OPTIONS请求（CORS预检请求）
        if request.method == 'OPTIONS':
            return
        
        # 跳过健康检查、API路由和静态资源
        # API路由通常使用token认证，不需要CSRF保护
        skip_paths = ['/health', '/', '/api/csrf-token']
        if request.path.startswith('/api/'):
            # API路由跳过CSRF保护（使用token认证）
            return
        
        if request.path in skip_paths:
            return
        
        # 对于需要CSRF保护的请求（POST, PUT, DELETE）
        if request.method in ['POST', 'PUT', 'DELETE']:
            # 检查是否包含CSRF token
            csrf_token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
            
            # 如果会话中没有CSRF token，生成一个
            if 'csrf_token' not in session:
                session['csrf_token'] = secrets.token_hex(32)
            
            # 验证CSRF token
            if csrf_token != session.get('csrf_token'):
                from flask import jsonify
                return jsonify({'error': 'CSRF token验证失败'}), 403
    
    # 提供CSRF token获取接口
    @app.route('/api/csrf-token', methods=['GET'])
    def get_csrf_token():
        """获取CSRF token"""
        if 'csrf_token' not in session:
            session['csrf_token'] = secrets.token_hex(32)
        return {'csrf_token': session['csrf_token']}
    
    # 初始化日志
    setup_logging(app)
    
    # 初始化缓存控制
    init_cache_control_helpers(app)
    
    # 初始化API性能监控
    try:
        from backend.utils.api_monitor import init_api_monitoring
        init_api_monitoring(app)
    except Exception as e:
        logger.warning(f"API性能监控初始化失败: {e}")
    
    # 启用响应压缩（gzip）
    @app.after_request
    def compress_response(response):
        """压缩响应内容，减少传输大小"""
        # 只压缩JSON和文本响应
        if (response.content_length and response.content_length > 1024 and 
            response.mimetype in ('application/json', 'text/html', 'text/css', 
                                 'text/javascript', 'application/javascript')):
            # 检查客户端是否支持gzip
            accept_encoding = request.headers.get('Accept-Encoding', '')
            if 'gzip' in accept_encoding:
                compressed_data = gzip.compress(response.get_data(), compresslevel=6)
                response.set_data(compressed_data)
                response.headers['Content-Encoding'] = 'gzip'
                response.headers['Content-Length'] = len(compressed_data)
                logger.debug(f"响应已压缩: {response.content_length} -> {len(compressed_data)} bytes")
        return response
    
    # 在应用上下文中初始化模型
    with app.app_context():
        # 初始化模型
        Product, Admin, AccessLog = init_models()
        
        # 测试数据库连接
        try:
            # 尝试连接数据库
            db.engine.connect()
            logger.info("✅ 数据库连接成功")
            
            # 创建表
            db.create_all()
            
            # 创建点赞数据表
            from backend.models.brand_like import BrandLike
            BrandLike.create_table()

            # 创建评价数据表
            from backend.models.brand_review import BrandReview
            BrandReview.create_table()
            
            logger.info("✅ 数据表创建成功")
            
            # 创建默认管理员（如果不存在）
            if Admin:
                admin = Admin.query.filter_by(username='admin').first()
                if not admin:
                    import secrets
                    # 生成随机密码，避免使用弱密码
                    default_password = secrets.token_urlsafe(16)
                    admin = Admin(username='admin', email='admin@nanyi.com')
                    admin.set_password(default_password)
                    db.session.add(admin)
                    db.session.commit()
                    logger.info(f"✅ 默认管理员创建成功")
                    logger.warning(f"⚠️  默认密码: {default_password}")
                    logger.warning(f"⚠️  请立即登录并修改密码！")
                    
        except Exception as e:
            logger.error(f"❌ 数据库初始化失败: {e}")
            # 不中断服务，继续启动
    
    # 初始化Flask-RESTX API文档（可选，如果flask-restx可用）
    api = None
    try:
        from flask_restx import Api
        api = Api(
            app,
            version='1.0',
            title='南意秋棠API文档',
            description='南意秋棠产品展示系统API文档',
            doc='/api/docs',  # Swagger UI路径
            prefix='/api'
        )
        logger.info("✅ Flask-RESTX API文档已初始化: http://localhost:5432/api/docs")
    except ImportError:
        logger.warning("⚠️  Flask-RESTX未安装，API文档功能不可用")
    
    # 延迟导入路由，避免循环导入
    try:
        # 注册通用API路由
        from backend.routes.api import api_bp, api_bp_v1
        app.register_blueprint(api_bp)  # 向后兼容旧版API
        app.register_blueprint(api_bp_v1)  # 新版API v1
        
        # 注册拆分后的路由模块
        from backend.routes.images import images_bp
        from backend.routes.brands import brands_bp
        from backend.routes.products import products_bp
        from backend.routes.filters import filters_bp
        from backend.routes.share import share_bp
        from backend.routes.static_cards import static_cards_bp
        from backend.routes.try_on import try_on_bp
        from backend.routes.auth import auth_bp
        from backend.routes.reviews import reviews_bp
        from backend.routes.admin_reviews import admin_reviews_bp
        
        app.register_blueprint(images_bp)
        app.register_blueprint(brands_bp)
        app.register_blueprint(products_bp)
        app.register_blueprint(filters_bp)
        app.register_blueprint(share_bp)
        app.register_blueprint(static_cards_bp)
        app.register_blueprint(try_on_bp)
        app.register_blueprint(auth_bp)
        app.register_blueprint(reviews_bp)
        app.register_blueprint(admin_reviews_bp)
        
        logger.info("✅ API路由注册成功 (支持 /api 和 /api/v1)")
        logger.info("✅ 已注册路由模块: images, brands, products, filters, share, try_on, auth, reviews, admin_reviews")
    except ImportError as e:
        logger.warning(f"警告: 路由导入失败 - {e}")
        import traceback
        traceback.print_exc()
    
    # 注册基本路由
    @app.route('/')
    def index():
        """API根路径，返回服务状态"""
        return {
            'service': '南意秋棠后端API',
            'version': '1.0.0',
            'status': 'running',
            'frontend_url': 'http://121.36.205.70:8500',
            'api_docs': '/api',
            'endpoints': {
                'products': '/api/products',
                'brands': '/api/brand/<brand_name>',
                'health': '/health'
            }
        }
    
    @app.route('/health')
    def health():
        """健康检查 - 增强版，包含详细状态信息"""
        backend_port = os.environ.get('BACKEND_PORT', '5432')
        
        health_status = {
            'status': 'healthy',
            'service': 'nanyi-backend',
            'port': int(backend_port),
            'timestamp': datetime.utcnow().isoformat(),
            'checks': {}
        }
        
        # 检查数据库连接
        try:
            db.engine.connect()
            db_status = 'connected'
            # 测试简单查询
            db.session.execute('SELECT 1')
            health_status['checks']['database'] = {
                'status': 'ok',
                'connection': 'connected'
            }
        except Exception as e:
            db_status = 'disconnected'
            health_status['checks']['database'] = {
                'status': 'error',
                'connection': 'disconnected',
                'error': str(e)
            }
            health_status['status'] = 'degraded'
        
        # 检查缓存服务（如果使用）
        try:
            from backend.services.cache_service import cache_service
            cache_service.get('health_check')
            
            # 获取缓存统计信息
            cache_stats = cache_service.stats()
            health_status['checks']['cache'] = {
                'status': 'ok',
                'type': 'redis' if cache_service.redis_cache else 'memory',
                'hit_ratio': f"{cache_stats.get('hit_ratio', 0):.2f}%",
                'total_operations': cache_stats.get('total_operations', 0)
            }
        except Exception as e:
            health_status['checks']['cache'] = {
                'status': 'error',
                'error': str(e)
            }
            # 缓存错误不影响整体健康状态
        
        # 如果数据库不可用，标记为不健康
        if health_status['checks']['database']['status'] != 'ok':
            health_status['status'] = 'unhealthy'
            return health_status, 503
        
        return health_status
    
    # 初始化 TryOn 图片处理服务（集成模式）
    # 在应用上下文中初始化，确保数据库连接可用
    try_on_image_service = None
    try:
        from backend.services.try_on_image_service import TryOnImageService
        from backend.config.config import Config
        
        # 获取配置实例
        config_instance = Config(config_name=config_name)
        
        # 初始化 TryOnImageService（会自动启动后台工作器线程）
        # 传递 Flask 应用实例，以便在后台线程中使用应用上下文
        try_on_image_service = TryOnImageService(config_instance, app=app)
        
        # 将服务实例存储在 app 对象上，以便在应用关闭时能够调用 shutdown
        app.try_on_image_service = try_on_image_service
        
        logger.info("✅ TryOn图片处理服务已初始化（集成模式，后台工作器已启动）")
    except Exception as e:
        logger.warning(f"⚠️  TryOn图片处理服务初始化失败: {e}", exc_info=True)
        # 不中断服务启动，但记录警告
        app.try_on_image_service = None
    
    # 注册应用关闭时的清理函数
    @app.teardown_appcontext
    def close_try_on_service(error):
        """
        应用上下文关闭时的清理函数
        注意：这个函数在每个请求结束时调用，不是应用关闭时
        """
        # 这里不做任何操作，因为工作器需要在应用关闭时统一关闭
        pass
    
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
    import atexit
    import signal
    
    # 获取环境变量
    config_name = os.environ.get('FLASK_ENV', 'development')
    port = int(os.environ.get('BACKEND_PORT', 5432))
    host = os.environ.get('HOST', '0.0.0.0')
    
    # 创建应用
    app = create_app(config_name)
    
    logger.info(f"🚀 南意秋棠后端服务启动")
    logger.info(f"📱 本地访问: http://localhost:{port}")
    logger.info(f"🌐 IP访问: http://121.36.205.70:{port}")
    logger.info(f"🌐 域名访问: http://products.nanyiqiutang.cn (通过nginx代理)")
    logger.info(f"🔧 环境: {config_name}")
    logger.info(f"💾 数据库: {app.config['SQLALCHEMY_DATABASE_URI'].split('@')[1] if '@' in app.config['SQLALCHEMY_DATABASE_URI'] else 'N/A'}")
    
    # 定义优雅关闭函数
    def shutdown_try_on_service():
        """关闭 TryOn 图片处理服务"""
        if hasattr(app, 'try_on_image_service') and app.try_on_image_service:
            try:
                logger.info("正在关闭 TryOn 图片处理服务...")
                app.try_on_image_service.shutdown()
                logger.info("✅ TryOn 图片处理服务已关闭")
            except Exception as e:
                logger.error(f"关闭 TryOn 图片处理服务时出错: {e}", exc_info=True)
    
    # 注册信号处理器（用于优雅关闭）
    def signal_handler(signum, frame):
        """信号处理器"""
        logger.info(f"收到信号 {signum}，正在关闭服务...")
        shutdown_try_on_service()
        # 注意：这里不直接退出，让 Flask 的 run() 方法正常退出
    
    # 注册退出时的清理函数
    atexit.register(shutdown_try_on_service)
    
    # 注册信号处理器（SIGTERM 和 SIGINT）
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # 启动应用
        app.run(
            host=host,
            port=port,
            debug=app.config['DEBUG'],
            threaded=True
        )
    finally:
        # 确保在应用退出时关闭服务
        shutdown_try_on_service()

if __name__ == '__main__':
    main() 