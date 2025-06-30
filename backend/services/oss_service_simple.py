#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版OSS存储服务 - 避开依赖冲突
"""

import os
import logging
import requests
import hashlib
import hmac
import base64
from datetime import datetime, timezone
from typing import Dict, List, Optional
from urllib.parse import quote

from ..config.oss_config import OSSConfig

# 配置日志
logger = logging.getLogger(__name__)

class SimpleOSSService:
    """简化版OSS存储服务"""
    
    def __init__(self):
        """初始化OSS服务"""
        try:
            # 验证配置
            OSSConfig.validate_config()
            self.access_key_id = OSSConfig.ACCESS_KEY_ID
            self.access_key_secret = OSSConfig.ACCESS_KEY_SECRET
            self.endpoint = OSSConfig.ENDPOINT
            self.bucket_name = OSSConfig.BUCKET_NAME
            
            # 构建bucket URL
            self.bucket_url = f"https://{self.bucket_name}.{self.endpoint.replace('https://', '')}"
            
            logger.info("✅ 简化版OSS服务初始化成功")
            
        except Exception as e:
            logger.error(f"❌ OSS服务初始化失败: {e}")
            raise
    
    def _get_gmt_time(self):
        """获取GMT时间字符串"""
        return datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')
    
    def _sign_request(self, method, content_type, date, oss_headers, resource):
        """生成OSS签名"""
        # 构建签名字符串
        string_to_sign = f"{method}\n\n{content_type}\n{date}\n{resource}"
        
        # 计算签名
        signature = base64.b64encode(
            hmac.new(
                self.access_key_secret.encode('utf-8'),
                string_to_sign.encode('utf-8'),
                hashlib.sha1
            ).digest()
        ).decode('utf-8')
        
        return f"OSS {self.access_key_id}:{signature}"
    
    def upload_image(self, local_path: str, image_type: str, brand_name: str, 
                    filename: str = None) -> Dict:
        """
        上传图片到OSS
        """
        try:
            # 检查本地文件
            if not os.path.exists(local_path):
                raise FileNotFoundError(f"本地文件不存在: {local_path}")
            
            # 获取文件名
            if not filename:
                filename = os.path.basename(local_path)
            
            # 生成OSS存储路径
            oss_path = OSSConfig.get_image_path(image_type, brand_name, filename)
            
            # 读取文件内容
            with open(local_path, 'rb') as f:
                file_content = f.read()
            
            # 准备请求
            url = f"{self.bucket_url}/{oss_path}"
            date = self._get_gmt_time()
            content_type = self._get_content_type(filename)
            resource = f"/{self.bucket_name}/{oss_path}"
            
            # 生成签名
            authorization = self._sign_request('PUT', content_type, date, {}, resource)
            
            # 设置请求头
            headers = {
                'Authorization': authorization,
                'Date': date,
                'Content-Type': content_type,
                'Content-Length': str(len(file_content))
            }
            
            # 发送请求
            response = requests.put(url, data=file_content, headers=headers)
            
            if response.status_code == 200:
                # 上传成功
                result = {
                    'success': True,
                    'oss_path': oss_path,
                    'original_url': OSSConfig.get_image_url(oss_path, 'original'),
                    'thumbnail_url': OSSConfig.get_image_url(oss_path, 'thumbnail'),
                    'preview_url': OSSConfig.get_image_url(oss_path, 'preview'),
                    'file_size': len(file_content),
                    'etag': response.headers.get('ETag', '').strip('"')
                }
                
                logger.info(f"✅ 图片上传成功: {oss_path}")
                return result
            else:
                error_msg = f"上传失败: HTTP {response.status_code} - {response.text}"
                logger.error(f"❌ {error_msg}")
                return {
                    'success': False,
                    'error': error_msg,
                    'oss_path': None
                }
                
        except Exception as e:
            logger.error(f"❌ 图片上传失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'oss_path': None
            }
    
    def _get_content_type(self, filename):
        """根据文件扩展名获取Content-Type"""
        ext = filename.lower().split('.')[-1]
        content_types = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'webp': 'image/webp',
            'bmp': 'image/bmp'
        }
        return content_types.get(ext, 'application/octet-stream')
    
    def check_connection(self) -> bool:
        """检查OSS连接是否正常"""
        try:
            # 尝试列出bucket（HEAD请求）
            date = self._get_gmt_time()
            resource = f"/{self.bucket_name}/"
            authorization = self._sign_request('HEAD', '', date, {}, resource)
            
            headers = {
                'Authorization': authorization,
                'Date': date
            }
            
            response = requests.head(self.bucket_url, headers=headers)
            
            if response.status_code == 200:
                logger.info(f"✅ OSS连接正常 - Bucket: {self.bucket_name}")
                return True
            else:
                logger.error(f"❌ OSS连接失败: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ OSS连接失败: {e}")
            return False

# 创建全局OSS服务实例
try:
    simple_oss_service = SimpleOSSService()
except Exception as e:
    logger.error(f"❌ 无法创建简化版OSS服务实例: {e}")
    simple_oss_service = None 