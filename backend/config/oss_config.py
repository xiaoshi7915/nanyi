#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阿里云OSS配置文件
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class OSSConfig:
    """阿里云OSS配置"""
    
    # OSS访问凭证 - 仅从环境变量获取，不提供默认值
    ACCESS_KEY_ID = os.environ.get('OSS_ACCESS_KEY_ID')
    ACCESS_KEY_SECRET = os.environ.get('OSS_ACCESS_KEY_SECRET')
    
    # OSS服务配置
    ENDPOINT = os.environ.get('OSS_ENDPOINT', 'https://oss-cn-hangzhou.aliyuncs.com')
    BUCKET_NAME = os.environ.get('OSS_BUCKET_NAME', 'nanyiqiutang')
    
    # CDN配置（可选）
    CDN_DOMAIN = os.environ.get('OSS_CDN_DOMAIN', '')  # 如：img.chenxiaoshivivid.com.cn
    
    # 图片存储路径配置
    IMAGE_PATHS = {
        '概念图': 'gainiangtu',      # 概念图
        '设计图': 'shejitu',          # 设计图  
        '成衣图': 'chengyitu',        # 成衣图
        '布料图': 'buliaotu',         # 布料图
        '模特图': 'motetu',           # 模特图
        '买家秀图': 'maijiaxiutu',    # 买家秀图
        '其他': 'qita'                # 其他
    }
    
    # 图片处理配置
    IMAGE_QUALITY = {
        'thumbnail': 80,    # 缩略图质量
        'preview': 85,      # 预览图质量
        'original': 95      # 原图质量
    }
    
    # 图片尺寸配置
    IMAGE_SIZES = {
        'thumbnail': (300, 300),    # 缩略图尺寸
        'preview': (800, 800),      # 预览图尺寸
        'medium': (1200, 1200)      # 中等尺寸
    }
    
    # 支持的图片格式
    SUPPORTED_FORMATS = ['jpg', 'jpeg', 'png', 'webp', 'bmp']
    
    # 输出格式配置
    OUTPUT_FORMATS = {
        'thumbnail': 'webp',    # 缩略图使用WebP格式
        'preview': 'webp',      # 预览图使用WebP格式
        'original': 'jpg'       # 原图保持原格式或转为JPG
    }
    
    @classmethod
    def get_image_path(cls, image_type, brand_name, filename):
        """
        生成图片在OSS中的存储路径
        
        格式: images/{image_type}/{brand_name}/{filename}
        例如: images/xuanchuantu/tianzhongjiahua/design_001.jpg
        """
        # 获取图片类型对应的路径
        type_path = cls.IMAGE_PATHS.get(image_type, cls.IMAGE_PATHS['其他'])
        
        # 清理品牌名称（移除特殊字符）
        clean_brand_name = cls._clean_filename(brand_name)
        
        # 构建完整路径
        return f"images/{type_path}/{clean_brand_name}/{filename}"
    
    @classmethod
    def get_image_url(cls, oss_path, size='original'):
        """
        生成图片访问URL
        
        Args:
            oss_path: OSS中的文件路径
            size: 图片尺寸类型 (thumbnail, preview, original)
        """
        if cls.CDN_DOMAIN:
            base_url = f"https://{cls.CDN_DOMAIN}"
        else:
            base_url = f"https://{cls.BUCKET_NAME}.{cls.ENDPOINT.replace('https://', '')}"
        
        if size != 'original':
            # 添加OSS图片处理参数
            width, height = cls.IMAGE_SIZES[size]
            quality = cls.IMAGE_QUALITY[size]
            format_type = cls.OUTPUT_FORMATS[size]
            
            process_params = f"?x-oss-process=image/resize,w_{width},h_{height},m_lfit/quality,q_{quality}/format,{format_type}"
            return f"{base_url}/{oss_path}{process_params}"
        
        return f"{base_url}/{oss_path}"
    
    @staticmethod
    def _clean_filename(filename):
        """清理文件名，移除特殊字符"""
        import re
        # 移除或替换特殊字符
        clean_name = re.sub(r'[^\w\u4e00-\u9fff\-_.]', '_', filename)
        return clean_name.strip('_')
    
    @classmethod
    def validate_config(cls):
        """验证OSS配置是否完整"""
        required_fields = ['ACCESS_KEY_ID', 'ACCESS_KEY_SECRET', 'ENDPOINT', 'BUCKET_NAME']
        missing_fields = []
        
        for field in required_fields:
            if not getattr(cls, field):
                missing_fields.append(field)
        
        if missing_fields:
            raise ValueError(f"OSS配置缺失: {', '.join(missing_fields)}")
        
        return True

# 验证配置
try:
    OSSConfig.validate_config()
    print("✅ OSS配置验证成功")
except ValueError as e:
    print(f"❌ OSS配置错误: {e}")
