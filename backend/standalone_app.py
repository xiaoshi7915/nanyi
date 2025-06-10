#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
南意秋棠 - 独立应用程序
当数据库连接失败时的备用方案
"""

import os
import sys
import json
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 模拟数据库数据
MOCK_PRODUCTS = [
    {
        'id': 1,
        'brand_name': '汉尚华莲',
        'title': '明制立领长衫',
        'year': 2024,
        'publish_month': '2024-01',
        'material': '真丝',
        'theme_series': '明制汉服',
        'print_size': '循环印花料',
        'inspiration_origin': '明代传统服饰文化',
        'created_at': '2024-01-01T00:00:00',
        'updated_at': '2024-01-01T00:00:00'
    },
    {
        'id': 2,
        'brand_name': '重回汉唐',
        'title': '唐制齐胸襦裙',
        'year': 2024,
        'publish_month': '2024-02',
        'material': '雪纺',
        'theme_series': '唐制汉服',
        'print_size': '循环印花料',
        'inspiration_origin': '唐代宫廷服饰',
        'created_at': '2024-02-01T00:00:00',
        'updated_at': '2024-02-01T00:00:00'
    },
    {
        'id': 3,
        'brand_name': '花朝记',
        'title': '宋制褙子套装',
        'year': 2024,
        'publish_month': '2024-03',
        'material': '棉麻',
        'theme_series': '宋制汉服',
        'print_size': '循环印花料',
        'inspiration_origin': '宋代文人雅士服饰',
        'created_at': '2024-03-01T00:00:00',
        'updated_at': '2024-03-01T00:00:00'
    }
]

def create_app():
    """创建Flask应用"""
    app = Flask(__name__)
    
    # 基本配置
    app.config['SECRET_KEY'] = 'nanyi_standalone_key'
    app.config['JSON_AS_ASCII'] = False
    
    # 启用CORS
    CORS(app, origins=['http://localhost:8500', 'http://121.36.205.70:8500'])
    
    # 健康检查
    @app.route('/health')
    def health():
        return {
            'status': 'healthy',
            'service': 'nanyi-standalone',
            'mode': 'standalone',
            'database': 'mock_data'
        }
    
    # API路由
    @app.route('/api/products', methods=['GET'])
    def get_products():
        """获取产品列表"""
        return jsonify({
            'success': True,
            'data': MOCK_PRODUCTS,
            'total': len(MOCK_PRODUCTS),
            'message': '获取产品列表成功（模拟数据）'
        })
    
    @app.route('/api/products/<int:product_id>', methods=['GET'])
    def get_product(product_id):
        """获取单个产品"""
        product = next((p for p in MOCK_PRODUCTS if p['id'] == product_id), None)
        if product:
            return jsonify({
                'success': True,
                'data': product,
                'message': '获取产品详情成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '产品不存在'
            }), 404
    
    @app.route('/api/products', methods=['POST'])
    def add_product():
        """添加产品"""
        data = request.get_json()
        if not data or not data.get('brand_name'):
            return jsonify({
                'success': False,
                'message': '品牌名称不能为空'
            }), 400
        
        # 创建新产品
        new_id = max([p['id'] for p in MOCK_PRODUCTS]) + 1 if MOCK_PRODUCTS else 1
        new_product = {
            'id': new_id,
            'brand_name': data.get('brand_name'),
            'title': data.get('title', ''),
            'year': data.get('year'),
            'publish_month': data.get('publish_month'),
            'material': data.get('material', ''),
            'theme_series': data.get('theme_series', '其他'),
            'print_size': data.get('print_size', '循环印花料'),
            'inspiration_origin': data.get('inspiration_origin', ''),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        MOCK_PRODUCTS.append(new_product)
        
        return jsonify({
            'success': True,
            'data': new_product,
            'message': '产品添加成功（模拟数据）'
        })
    
    @app.route('/api/products/<int:product_id>', methods=['PUT'])
    def update_product(product_id):
        """更新产品"""
        product = next((p for p in MOCK_PRODUCTS if p['id'] == product_id), None)
        if not product:
            return jsonify({
                'success': False,
                'message': '产品不存在'
            }), 404
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400
        
        # 更新产品信息
        for key, value in data.items():
            if key in product and key != 'id':
                product[key] = value
        
        product['updated_at'] = datetime.now().isoformat()
        
        return jsonify({
            'success': True,
            'data': product,
            'message': '产品更新成功（模拟数据）'
        })
    
    @app.route('/api/products/<int:product_id>', methods=['DELETE'])
    def delete_product(product_id):
        """删除产品"""
        global MOCK_PRODUCTS
        product = next((p for p in MOCK_PRODUCTS if p['id'] == product_id), None)
        if not product:
            return jsonify({
                'success': False,
                'message': '产品不存在'
            }), 404
        
        MOCK_PRODUCTS = [p for p in MOCK_PRODUCTS if p['id'] != product_id]
        
        return jsonify({
            'success': True,
            'message': '产品删除成功（模拟数据）'
        })
    
    @app.route('/api/statistics', methods=['GET'])
    def get_statistics():
        """获取统计信息"""
        years = list(set([p['year'] for p in MOCK_PRODUCTS if p.get('year')]))
        themes = list(set([p['theme_series'] for p in MOCK_PRODUCTS if p.get('theme_series')]))
        materials = list(set([p['material'] for p in MOCK_PRODUCTS if p.get('material')]))
        
        return jsonify({
            'success': True,
            'data': {
                'total_brands': len(MOCK_PRODUCTS),
                'years': sorted(years, reverse=True),
                'theme_series': sorted(themes),
                'materials': sorted(materials)
            },
            'message': '获取统计信息成功（模拟数据）'
        })
    
    @app.route('/api/search', methods=['GET'])
    def search_products():
        """搜索产品"""
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({
                'success': True,
                'data': MOCK_PRODUCTS,
                'total': len(MOCK_PRODUCTS),
                'message': '获取全部产品'
            })
        
        # 简单的搜索逻辑
        results = [
            p for p in MOCK_PRODUCTS
            if query.lower() in p['brand_name'].lower() or 
               (p.get('title') and query.lower() in p['title'].lower()) or
               (p.get('theme_series') and query.lower() in p['theme_series'].lower())
        ]
        
        return jsonify({
            'success': True,
            'data': results,
            'total': len(results),
            'message': f'搜索到 {len(results)} 个结果（模拟数据）'
        })
    
    # 管理员相关API
    @app.route('/api/admin/login', methods=['POST'])
    def admin_login():
        """管理员登录"""
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400
        
        username = data.get('username')
        password = data.get('password')
        
        # 简单的验证逻辑
        if username == 'admin' and password == 'admin123':
            return jsonify({
                'success': True,
                'data': {
                    'token': 'mock_token_123456',
                    'username': 'admin',
                    'email': 'admin@nanyi.com'
                },
                'message': '登录成功（模拟数据）'
            })
        else:
            return jsonify({
                'success': False,
                'message': '用户名或密码错误'
            }), 401
    
    # 主页
    @app.route('/')
    def index():
        """主页"""
        return jsonify({
            'service': '南意秋棠 - 独立模式',
            'version': '1.0.0',
            'mode': 'standalone',
            'status': 'running',
            'api_endpoints': [
                '/api/products',
                '/api/statistics',
                '/api/search',
                '/api/admin/login',
                '/health'
            ],
            'message': '服务正在运行中（独立模式，使用模拟数据）'
        })
    
    # 错误处理
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    return app

def main():
    """主函数"""
    app = create_app()
    
    # 获取环境变量
    port = int(os.environ.get('BACKEND_PORT', 5001))
    host = os.environ.get('HOST', '0.0.0.0')
    
    print(f"🚀 南意秋棠独立服务启动")
    print(f"📱 访问地址: http://localhost:{port}")
    print(f"🔧 模式: 独立模式（模拟数据）")
    print(f"💾 数据库: 模拟数据")
    print(f"📋 API文档: http://localhost:{port}/")
    
    # 启动应用
    app.run(
        host=host,
        port=port,
        debug=True,
        threaded=True
    )

if __name__ == '__main__':
    main() 