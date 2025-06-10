import logging
import json
import requests
from datetime import datetime
from functools import wraps
from flask import request, g
import os

class LoggerConfig:
    """日志配置类"""
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化日志配置"""
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # 访问日志配置
        access_handler = logging.FileHandler(os.path.join(log_dir, 'access.log'))
        access_handler.setLevel(logging.INFO)
        access_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        access_handler.setFormatter(access_formatter)
        
        # 错误日志配置
        error_handler = logging.FileHandler(os.path.join(log_dir, 'error.log'))
        error_handler.setLevel(logging.ERROR)
        error_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s'
        )
        error_handler.setFormatter(error_formatter)
        
        # 创建日志记录器
        self.access_logger = logging.getLogger('access')
        self.access_logger.setLevel(logging.INFO)
        self.access_logger.addHandler(access_handler)
        
        self.error_logger = logging.getLogger('error')
        self.error_logger.setLevel(logging.ERROR)
        self.error_logger.addHandler(error_handler)
        
        app.logger.addHandler(access_handler)
        app.logger.addHandler(error_handler)

class IPService:
    """IP归属地查询服务"""
    
    @staticmethod
    def get_ip_info(ip):
        """获取IP归属地信息"""
        try:
            # 使用免费的IP查询API
            url = f"http://ip-api.com/json/{ip}?lang=zh-CN"
            response = requests.get(url, timeout=3)
            if response.status_code == 200:
                data = response.json()
                return {
                    'country': data.get('country', '未知'),
                    'region': data.get('regionName', '未知'),
                    'city': data.get('city', '未知'),
                    'isp': data.get('isp', '未知'),
                    'timezone': data.get('timezone', '未知')
                }
        except Exception as e:
            print(f"获取IP信息失败: {e}")
        
        return {
            'country': '未知',
            'region': '未知', 
            'city': '未知',
            'isp': '未知',
            'timezone': '未知'
        }

def log_access(f):
    """访问日志装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 获取客户端IP
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if client_ip:
            client_ip = client_ip.split(',')[0].strip()
        
        # 获取请求信息
        user_agent = request.headers.get('User-Agent', '')
        referer = request.headers.get('Referer', '')
        method = request.method
        path = request.path
        query_string = request.query_string.decode('utf-8')
        
        # 获取IP归属地信息
        ip_info = IPService.get_ip_info(client_ip)
        
        # 记录请求开始时间
        start_time = datetime.now()
        
        try:
            # 执行请求
            response = f(*args, **kwargs)
            status_code = 200
            
            # 计算响应时间
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # 记录访问日志
            log_data = {
                'timestamp': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'client_ip': client_ip,
                'method': method,
                'path': path,
                'query_string': query_string,
                'status_code': status_code,
                'response_time_ms': round(response_time, 2),
                'user_agent': user_agent,
                'referer': referer,
                'ip_info': ip_info
            }
            
            # 写入访问日志
            access_logger = logging.getLogger('access')
            access_logger.info(json.dumps(log_data, ensure_ascii=False))
            
            return response
            
        except Exception as e:
            # 计算响应时间
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # 记录错误日志
            log_data = {
                'timestamp': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'client_ip': client_ip,
                'method': method,
                'path': path,
                'query_string': query_string,
                'status_code': 500,
                'response_time_ms': round(response_time, 2),
                'user_agent': user_agent,
                'referer': referer,
                'ip_info': ip_info,
                'error': str(e)
            }
            
            # 写入错误日志
            error_logger = logging.getLogger('error')
            error_logger.error(json.dumps(log_data, ensure_ascii=False))
            
            raise e
    
    return decorated_function

def setup_logging(app):
    """设置应用日志"""
    logger_config = LoggerConfig(app)
    return logger_config 