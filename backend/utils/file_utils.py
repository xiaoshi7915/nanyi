#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件处理工具函数
"""

import os
import re
from werkzeug.utils import secure_filename
from backend.config.config import Config

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def parse_filename(filename):
    """
    解析文件名获取品牌信息
    支持两种格式:
    1. 品牌名-图片类型-编号.扩展名 (例如: 春风裁-布料图-01.jpg)
    2. 品牌名(颜色)-图片类型-编号.扩展名 (例如: 次第春(绿)-设计图-01.jpg)
    """
    # 移除文件扩展名
    name_without_ext = os.path.splitext(filename)[0]
    
    # 匹配格式1: 品牌名-图片类型-编号
    pattern1 = r'^([^-]+)-([^-]+)-(\d+)$'
    match1 = re.match(pattern1, name_without_ext)
    
    if match1:
        return {
            'brand_name': match1.group(1).strip(),
            'image_type': match1.group(2).strip(),
            'number': match1.group(3).strip(),
            'color': None,
            'has_color': False
        }
    
    # 匹配格式2: 品牌名(颜色)-图片类型-编号
    pattern2 = r'^([^(]+)\(([^)]+)\)-([^-]+)-(\d+)$'
    match2 = re.match(pattern2, name_without_ext)
    
    if match2:
        return {
            'brand_name': match2.group(1).strip(),
            'color': match2.group(2).strip(),
            'image_type': match2.group(3).strip(),
            'number': match2.group(4).strip(),
            'has_color': True
        }
    
    # 如果都不匹配，返回默认值
    return {
        'brand_name': name_without_ext,
        'image_type': '其他',
        'number': '01',
        'color': None,
        'has_color': False
    }

def secure_filename_custom(filename):
    """自定义安全文件名处理"""
    # 先使用werkzeug的secure_filename
    secured = secure_filename(filename)
    
    # 如果文件名被过度处理（比如中文字符被移除），保留原文件名的结构
    if not secured or len(secured) < 3:
        # 只移除危险字符，保留中文
        safe_chars = re.sub(r'[<>:"/\\|?*]', '_', filename)
        return safe_chars
    
    return secured

def get_file_size_readable(size_bytes):
    """将文件大小转换为可读格式"""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"

def create_directory_if_not_exists(path):
    """如果目录不存在则创建"""
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
        return True
    return False 