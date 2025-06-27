#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
缓存控制工具
用于管理静态资源的缓存策略，实现高性能和内容更新的平衡
"""

import os
import time
import hashlib
from datetime import datetime, timedelta
from flask import request, make_response, current_app
from functools import wraps

class CacheControlManager:
    """缓存控制管理器"""
    
    def __init__(self):
        # 不同资源类型的缓存策略（秒）
        self.cache_strategies = {
            # 图片资源 - 长期缓存，稳定资源
            'images': {
                'max_age': 86400 * 30,  # 30天缓存，图片基本不会更新
                'must_revalidate': False,
                'etag': True
            },
            # CSS/JS文件 - 长期缓存
            'static': {
                'max_age': 86400,  # 24小时
                'must_revalidate': False,
                'etag': True
            },
            # API响应 - 中期缓存，提升性能
            'api': {
                'max_age': 600,  # 10分钟，提升性能
                'must_revalidate': False,
                'etag': True
            },
            # 字体文件 - 长期缓存
            'fonts': {
                'max_age': 86400 * 30,  # 30天
                'must_revalidate': False,
                'etag': False
            }
        }
    
    def get_file_etag(self, file_path):
        """生成文件的ETag"""
        try:
            if os.path.exists(file_path):
                # 使用文件修改时间和大小生成ETag
                stat = os.stat(file_path)
                etag_data = f"{stat.st_mtime}-{stat.st_size}"
                return hashlib.md5(etag_data.encode()).hexdigest()
        except:
            pass
        return None
    
    def get_resource_type(self, path):
        """根据路径判断资源类型"""
        if '/static/images/' in path or path.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg')):
            return 'images'
        elif '/static/' in path and path.endswith(('.css', '.js')):
            return 'static'
        elif path.startswith('/api/'):
            return 'api'
        elif path.endswith(('.woff', '.woff2', '.ttf', '.eot')):
            return 'fonts'
        else:
            return 'static'  # 默认策略
    
    def apply_cache_headers(self, response, resource_type=None, file_path=None):
        """为响应添加缓存头"""
        if resource_type is None:
            resource_type = self.get_resource_type(request.path)
        
        strategy = self.cache_strategies.get(resource_type, self.cache_strategies['static'])
        
        # 设置Cache-Control
        cache_control_parts = [f"max-age={strategy['max_age']}"]
        
        if strategy['must_revalidate']:
            cache_control_parts.append('must-revalidate')
        
        # 添加public缓存指令，允许CDN和代理缓存
        cache_control_parts.append('public')
        
        response.headers['Cache-Control'] = ', '.join(cache_control_parts)
        
        # 设置ETag（如果启用）
        if strategy['etag'] and file_path:
            etag = self.get_file_etag(file_path)
            if etag:
                response.headers['ETag'] = f'"{etag}"'
                
                # 检查If-None-Match头
                if request.headers.get('If-None-Match') == f'"{etag}"':
                    response.status_code = 304
                    return response
        
        # 设置Last-Modified
        if file_path and os.path.exists(file_path):
            try:
                mtime = os.path.getmtime(file_path)
                last_modified = datetime.fromtimestamp(mtime)
                response.headers['Last-Modified'] = last_modified.strftime('%a, %d %b %Y %H:%M:%S GMT')
                
                # 检查If-Modified-Since头
                if_modified_since = request.headers.get('If-Modified-Since')
                if if_modified_since:
                    try:
                        client_time = datetime.strptime(if_modified_since, '%a, %d %b %Y %H:%M:%S GMT')
                        if last_modified <= client_time:
                            response.status_code = 304
                            return response
                    except:
                        pass
            except:
                pass
        
        return response

# 全局缓存控制管理器实例
cache_manager = CacheControlManager()

def cache_control(resource_type=None, max_age=None):
    """缓存控制装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            response = make_response(f(*args, **kwargs))
            
            # 如果指定了max_age，使用自定义缓存时间
            if max_age is not None:
                response.headers['Cache-Control'] = f'public, max-age={max_age}, must-revalidate'
            else:
                # 使用默认策略
                cache_manager.apply_cache_headers(response, resource_type)
            
            return response
        return decorated_function
    return decorator

def no_cache(f):
    """禁用缓存装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        response = make_response(f(*args, **kwargs))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    return decorated_function

def smart_cache(f):
    """智能缓存装饰器 - 根据内容变化自动调整缓存"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        response = make_response(f(*args, **kwargs))
        
        # 为API响应生成内容哈希作为ETag
        if hasattr(response, 'data'):
            content_hash = hashlib.md5(response.data).hexdigest()
            response.headers['ETag'] = f'"{content_hash}"'
            
            # 检查客户端缓存
            if request.headers.get('If-None-Match') == f'"{content_hash}"':
                response.status_code = 304
                response.data = b''
                return response
        
        # 设置短期缓存
        response.headers['Cache-Control'] = 'public, max-age=60, must-revalidate'
        
        return response
    return decorated_function

class VersionManager:
    """版本管理器 - 为静态资源添加版本号"""
    
    def __init__(self):
        self.version_cache = {}
        self.app_start_time = int(time.time())
    
    def get_file_version(self, file_path):
        """获取文件版本号"""
        if file_path in self.version_cache:
            return self.version_cache[file_path]
        
        try:
            if os.path.exists(file_path):
                # 使用文件修改时间作为版本号
                mtime = int(os.path.getmtime(file_path))
                version = mtime
            else:
                # 文件不存在时使用应用启动时间
                version = self.app_start_time
            
            self.version_cache[file_path] = version
            return version
        except:
            return self.app_start_time
    
    def add_version_to_url(self, url, base_path=''):
        """为URL添加版本参数"""
        if '?' in url:
            return url  # 已经有参数，不添加版本号
        
        # 构建完整文件路径
        if base_path:
            file_path = os.path.join(base_path, url.lstrip('/'))
        else:
            # 尝试从Flask应用获取静态文件路径
            try:
                static_folder = current_app.static_folder
                if static_folder:
                    file_path = os.path.join(static_folder, url.lstrip('/static/'))
                else:
                    file_path = url
            except:
                file_path = url
        
        version = self.get_file_version(file_path)
        return f"{url}?v={version}"
    
    def clear_cache(self):
        """清空版本缓存"""
        self.version_cache.clear()

# 全局版本管理器实例
version_manager = VersionManager()

def versioned_url(url, base_path=''):
    """生成带版本号的URL"""
    return version_manager.add_version_to_url(url, base_path)

# Flask模板函数
def init_cache_control_helpers(app):
    """初始化缓存控制辅助函数"""
    
    @app.template_global()
    def versioned_static(filename):
        """模板中使用的版本化静态文件URL"""
        static_url = f"/static/{filename}"
        return version_manager.add_version_to_url(static_url, app.static_folder)
    
    @app.template_global()
    def cache_bust():
        """获取缓存破坏参数"""
        return int(time.time())
    
    # 为静态文件请求添加缓存头
    @app.after_request
    def add_cache_headers(response):
        """为所有响应添加适当的缓存头"""
        # 跳过已经设置了缓存头的响应
        if 'Cache-Control' in response.headers:
            return response
        
        # 根据请求路径设置缓存策略
        path = request.path
        
        if path.startswith('/static/'):
            # 静态文件缓存
            if any(path.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']):
                # 图片文件 - 7天缓存，稳定资源
                response.headers['Cache-Control'] = 'public, max-age=604800, immutable'
                # 添加ETag支持
                cache_manager.apply_cache_headers(response, 'images')
            elif any(path.endswith(ext) for ext in ['.css', '.js']):
                # CSS/JS文件 - 24小时缓存
                response.headers['Cache-Control'] = 'public, max-age=86400'
            elif any(path.endswith(ext) for ext in ['.woff', '.woff2', '.ttf', '.eot']):
                # 字体文件 - 30天缓存
                response.headers['Cache-Control'] = 'public, max-age=2592000, immutable'
            else:
                # 其他静态文件 - 24小时缓存
                response.headers['Cache-Control'] = 'public, max-age=86400'
        elif path.startswith('/api/'):
            # API响应 - 5分钟缓存，提升性能
            response.headers['Cache-Control'] = 'public, max-age=300'
        
        return response
    
    return app 