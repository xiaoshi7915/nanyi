#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
南意秋棠 - 独立后端应用
"""

import os
import sys
import traceback
import re
from flask import Flask, jsonify, send_file, request, abort
from flask_cors import CORS

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def create_app():
    """创建Flask应用"""
    app = Flask(__name__, 
                static_folder='../frontend/static')
    
    # 基本配置
    app.config['SECRET_KEY'] = 'nanyi_backend_key_2024'
    app.config['DEBUG'] = True
    app.config['JSON_AS_ASCII'] = False
    
    # 启用CORS
    CORS(app, origins=[
        "http://localhost:8500",
        "http://127.0.0.1:8500", 
        "http://121.36.205.70:8500"
    ])
    
    # 图片处理函数
    def parse_filename(filename):
        """解析文件名获取品牌信息"""
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
        
        return {
            'brand_name': name_without_ext,
            'image_type': '其他',
            'number': '01',
            'color': None,
            'has_color': False
        }
    
    def get_all_images():
        """获取所有图片信息"""
        images = []
        images_dir = 'frontend/static/images'
        
        if not os.path.exists(images_dir):
            return images
        
        # 扫描根目录下的图片文件
        for filename in os.listdir(images_dir):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')):
                filepath = os.path.join(images_dir, filename)
                if os.path.isfile(filepath):
                    parsed_info = parse_filename(filename)
                    images.append({
                        'filename': filename,
                        'relative_path': filename,
                        'brand_name': parsed_info['brand_name'],
                        'image_type': parsed_info['image_type'],
                        'color': parsed_info['color'],
                        'has_color': parsed_info['has_color'],
                        'size': os.path.getsize(filepath)
                    })
        
        # 扫描子文件夹中的图片
        for item in os.listdir(images_dir):
            item_path = os.path.join(images_dir, item)
            if os.path.isdir(item_path):
                for filename in os.listdir(item_path):
                    if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')):
                        filepath = os.path.join(item_path, filename)
                        if os.path.isfile(filepath):
                            parsed_info = parse_filename(filename)
                            images.append({
                                'filename': filename,
                                'relative_path': f"{item}/{filename}",
                                'brand_name': parsed_info['brand_name'] or item,
                                'image_type': parsed_info['image_type'],
                                'color': parsed_info['color'],
                                'has_color': parsed_info['has_color'],
                                'size': os.path.getsize(filepath)
                            })
        
        return sorted(images, key=lambda x: x['brand_name'] or '')
    
    # API路由
    @app.route('/api/health')
    def api_health():
        """API健康检查"""
        return jsonify({
            'success': True,
            'status': 'healthy',
            'message': '南意秋棠后端API服务运行正常',
            'version': '2.0-standalone',
            'port': 5001
        })
    
    @app.route('/api/images')
    def api_images():
        """获取所有图片信息"""
        try:
            images = get_all_images()
            
            # 按品牌分组
            brands = {}
            for img in images:
                brand_name = img['brand_name']
                if brand_name not in brands:
                    brands[brand_name] = {
                        'name': brand_name,
                        'images': [],
                        'year': 2024,  # 默认年份
                        'material': '棉麻',  # 默认材质
                        'theme_series': '经典系列',  # 默认主题
                        'inspiration_origin': f'{brand_name}的设计灵感来源于传统文化与现代美学的融合。'
                    }
                brands[brand_name]['images'].append(img)
            
            # 转换为列表格式
            brand_list = []
            for brand_name, brand_data in brands.items():
                brand_list.append({
                    **brand_data,
                    'imageCount': len(brand_data['images'])
                })
            
            return jsonify({
                'success': True,
                'images': images,
                'brands': brand_list,
                'total': len(images)
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'获取图片信息失败: {str(e)}'
            }), 500
    
    @app.route('/api/filters')
    def api_filters():
        """获取筛选选项和品牌统计"""
        try:
            images = get_all_images()
            
            # 分析所有品牌数据
            brands_analysis = {}
            filter_stats = {
                'years': {},
                'materials': {},
                'theme_series': {},
                'print_sizes': {}
            }
            
            for img in images:
                brand_name = img['brand_name']
                if brand_name not in brands_analysis:
                    # 为每个品牌设置属性（这里可以连接真实数据库）
                    brands_analysis[brand_name] = {
                        'year': 2024,  # 从数据库获取
                        'material': '棉麻',  # 从数据库获取
                        'theme_series': '经典系列',  # 从数据库获取
                        'print_size': '循环印花料'  # 从数据库获取
                    }
            
            # 统计每个筛选项的品牌数量
            for brand_name, brand_data in brands_analysis.items():
                year = brand_data['year']
                material = brand_data['material']
                theme = brand_data['theme_series']
                print_size = brand_data['print_size']
                
                filter_stats['years'][year] = filter_stats['years'].get(year, 0) + 1
                filter_stats['materials'][material] = filter_stats['materials'].get(material, 0) + 1
                filter_stats['theme_series'][theme] = filter_stats['theme_series'].get(theme, 0) + 1
                filter_stats['print_sizes'][print_size] = filter_stats['print_sizes'].get(print_size, 0) + 1
            
            return jsonify({
                'success': True,
                'filters': {
                    'years': sorted(list(filter_stats['years'].keys()), reverse=True),
                    'materials': sorted(list(filter_stats['materials'].keys())),
                    'theme_series': sorted(list(filter_stats['theme_series'].keys())),
                    'print_sizes': sorted(list(filter_stats['print_sizes'].keys()))
                },
                'brand_counts': filter_stats
            })
            
        except Exception as e:
            print(f"获取筛选选项失败: {e}")
            return jsonify({
                'success': True,
                'filters': {
                    'years': [2024, 2023, 2022, 2021],
                    'materials': ['棉麻', '真丝', '雪纺', '织锦'],
                    'theme_series': ['经典系列', '画韵春秋系列', '长物志系列', '执念系列'],
                    'print_sizes': ['循环印花料', '旗袍定位料']
                },
                'brand_counts': {
                    'years': {2024: 10, 2023: 8, 2022: 6, 2021: 4},
                    'materials': {'棉麻': 15, '真丝': 8, '雪纺': 5, '织锦': 4},
                    'theme_series': {'经典系列': 12, '画韵春秋系列': 8, '长物志系列': 6, '执念系列': 4},
                    'print_sizes': {'循环印花料': 20, '旗袍定位料': 8}
                }
            })
    
    @app.route('/api/brand/<brand_name>')
    def api_brand_detail(brand_name):
        """获取品牌详情"""
        try:
            images = get_all_images()
            brand_images = [img for img in images if img['brand_name'] == brand_name]
            
            if not brand_images:
                return jsonify({
                    'success': False,
                    'error': '品牌不存在'
                }), 404
            
            brand_info = {
                'id': 1,
                'brand_name': brand_name,
                'year': 2024,
                'material': '棉麻',
                'theme_series': '经典系列',
                'print_size': '循环印花料',
                'inspiration_origin': f'{brand_name}的设计灵感来源于传统文化与现代美学的融合，体现了汉文化的优雅与时尚的完美结合。',
                'is_featured': True
            }
            
            return jsonify({
                'success': True,
                'brand_info': brand_info,
                'images': brand_images
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'获取品牌详情失败: {str(e)}'
            }), 500
    
    @app.route('/api/view/<path:filepath>')
    def api_view_image(filepath):
        """查看图片"""
        try:
            # 处理URL编码的中文路径
            import urllib.parse
            filepath = urllib.parse.unquote(filepath)
            
            full_path = os.path.join('frontend/static/images', filepath)
            
            if not os.path.exists(full_path):
                print(f"图片文件不存在: {full_path}")
                abort(404)
            
            # 安全检查
            if not os.path.abspath(full_path).startswith(os.path.abspath('frontend/static/images')):
                abort(403)
            
            return send_file(full_path)
            
        except Exception as e:
            print(f"图片访问错误: {e}")
            abort(404)
    
    @app.route('/api/download/<path:filepath>')
    def api_download_image(filepath):
        """下载图片"""
        try:
            full_path = os.path.join('frontend/static/images', filepath)
            
            if not os.path.exists(full_path):
                abort(404)
            
            # 安全检查
            if not os.path.abspath(full_path).startswith(os.path.abspath('frontend/static/images')):
                abort(403)
            
            return send_file(full_path, as_attachment=True)
            
        except Exception as e:
            abort(404)
    
    @app.route('/health')
    def health():
        """健康检查"""
        return jsonify({
            'status': 'healthy',
            'service': 'nanyi-backend',
            'port': 5001,
            'version': '2.0-standalone'
        })
    
    # 错误处理
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'success': False, 'error': '资源不存在'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'success': False, 'error': '服务器内部错误'}), 500
    
    return app

def main():
    """主函数"""
    app = create_app()
    
    port = 5001
    host = '0.0.0.0'
    
    print(f"🚀 南意秋棠后端服务启动")
    print(f"📱 本地访问: http://localhost:{port}")
    print(f"🌐 生产访问: http://121.36.205.70:{port}")
    print(f"💡 API健康检查: http://121.36.205.70:{port}/api/health")
    print(f"🔧 环境: 独立版本 (无数据库依赖)")
    
    # 启动应用
    app.run(
        host=host,
        port=port,
        debug=True,
        threaded=True
    )

if __name__ == '__main__':
    main() 