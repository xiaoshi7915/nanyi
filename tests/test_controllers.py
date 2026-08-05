#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
控制器测试
测试各个控制器的业务逻辑
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from backend.controllers.image_controller import ImageController
from backend.controllers.brand_controller import BrandController
from backend.controllers.product_controller import ProductController


class TestImageController:
    """测试图片控制器"""
    
    @pytest.fixture
    def image_controller(self):
        """创建图片控制器实例"""
        return ImageController()
    
    @pytest.fixture
    def mock_image_service(self):
        """创建模拟图片服务"""
        mock_service = Mock()
        mock_service.get_all_images.return_value = [
            {
                'brand_name': '江南春(红色)',
                'filename': 'test1.jpg',
                'url': 'http://test.com/test1.jpg',
                'image_type': '概念图'
            },
            {
                'brand_name': '江南春(蓝色)',
                'filename': 'test2.jpg',
                'url': 'http://test.com/test2.jpg',
                'image_type': '设计图'
            }
        ]
        return mock_service
    
    def test_get_images_with_pagination_default(self, image_controller, mock_image_service):
        """测试默认分页获取图片"""
        image_controller.image_service = mock_image_service
        
        # Mock数据库查询
        with patch('backend.controllers.image_controller.Product') as mock_product:
            mock_product.query.all.return_value = []
            
            with patch('backend.controllers.image_controller.BrandLike') as mock_brand_like:
                mock_brand_like.get_all_like_counts.return_value = {}
                
                result = image_controller.get_images_with_pagination()
                
                assert result['success'] is True
                assert 'brands' in result
                assert 'pagination' in result
                assert result['pagination']['current_page'] == 1
                assert result['pagination']['per_page'] == 12
    
    def test_get_images_with_pagination_custom(self, image_controller, mock_image_service):
        """测试自定义分页获取图片"""
        image_controller.image_service = mock_image_service
        
        with patch('backend.controllers.image_controller.Product') as mock_product:
            mock_product.query.all.return_value = []
            
            with patch('backend.controllers.image_controller.BrandLike') as mock_brand_like:
                mock_brand_like.get_all_like_counts.return_value = {}
                
                result = image_controller.get_images_with_pagination(page=2, per_page=5)
                
                assert result['pagination']['current_page'] == 2
                assert result['pagination']['per_page'] == 5
    
    def test_get_images_with_pagination_load_all(self, image_controller, mock_image_service):
        """测试加载所有图片"""
        image_controller.image_service = mock_image_service
        
        with patch('backend.controllers.image_controller.Product') as mock_product:
            mock_product.query.all.return_value = []
            
            with patch('backend.controllers.image_controller.BrandLike') as mock_brand_like:
                mock_brand_like.get_all_like_counts.return_value = {}
                
                result = image_controller.get_images_with_pagination(load_all=True)
                
                assert result['pagination']['total_pages'] == 1
                assert result['pagination']['has_next'] is False
                assert result['pagination']['has_prev'] is False
    
    def test_pick_preview_images_per_category(self, image_controller):
        """列表 preview_images 每分类最多一张"""
        images = [
            {'filename': 'a-设计图-01.jpg', 'image_type': '设计图'},
            {'filename': 'a-设计图-02.jpg', 'image_type': '设计图'},
            {'filename': 'a-布料图-01.jpg', 'image_type': '布料图'},
        ]
        previews = image_controller._pick_preview_images(images)
        types = {p['image_type'] for p in previews}
        assert types == {'设计图', '布料图'}
        assert len(previews) == 2

    def test_compact_brand_includes_preview_images(self, image_controller):
        """紧凑列表含 preview_images 与单张封面"""
        brand_data = {
            'name': '测试品牌',
            'images': [
                {'filename': 'a-设计图-01.jpg', 'image_type': '设计图'},
                {'filename': 'a-布料图-01.jpg', 'image_type': '布料图'},
            ],
            'imageCount': 2,
            'year': 2024,
        }
        compact = image_controller._compact_brand_for_list(brand_data)
        assert len(compact['images']) == 1
        assert len(compact['preview_images']) == 2

    def test_get_images_with_pagination_brand_grouping(self, image_controller, mock_image_service):
        """测试品牌分组功能"""
        image_controller.image_service = mock_image_service
        
        # Mock产品数据
        mock_product = Mock()
        mock_product.brand_name = '江南春(红色)'
        mock_product.year = 2024
        mock_product.material = '棉麻'
        mock_product.theme_series = '经典系列'
        mock_product.print_size = '循环印花料'
        mock_product.inspiration_origin = '测试灵感'
        mock_product.publish_month = '2024-01'
        
        with patch('backend.controllers.image_controller.Product') as mock_product_class:
            mock_product_class.query.all.return_value = [mock_product]
            
            with patch('backend.controllers.image_controller.BrandLike') as mock_brand_like:
                mock_brand_like.get_all_like_counts.return_value = {}
                
                result = image_controller.get_images_with_pagination()
                
                # 应该将相同基础品牌的图片分组
                assert len(result['brands']) > 0
                # 检查品牌信息是否正确
                brand = result['brands'][0]
                assert 'name' in brand
                assert 'images' in brand
                assert 'year' in brand


class TestBrandController:
    """测试品牌控制器"""
    
    @pytest.fixture
    def brand_controller(self):
        """创建品牌控制器实例"""
        return BrandController()
    
    @pytest.fixture
    def mock_product_service(self):
        """创建模拟产品服务"""
        mock_service = Mock()
        mock_service.get_brand_detail.return_value = {
            'name': '江南春',
            'year': 2024,
            'material': '棉麻',
            'theme_series': '经典系列',
            'print_size': '循环印花料',
            'inspiration_origin': '测试灵感',
            'images': [
                {'filename': 'test1.jpg', 'image_type': '概念图'},
                {'filename': 'test2.jpg', 'image_type': '设计图'}
            ]
        }
        return mock_service
    
    def test_get_brand_detail_success(self, brand_controller, mock_product_service):
        """测试成功获取品牌详情"""
        brand_controller.product_service = mock_product_service
        
        with patch('backend.controllers.brand_controller.BrandLike') as mock_brand_like:
            mock_brand_like.get_like_count.return_value = 10
            
            result = brand_controller.get_brand_detail('江南春')
            
            assert result is not None
            assert result['success'] is True
            assert 'brand_info' in result
            assert 'images' in result
            assert result['brand_info']['name'] == '江南春'
            assert result['brand_info']['like_count'] == 10
    
    def test_get_brand_detail_not_found(self, brand_controller, mock_product_service):
        """测试品牌不存在"""
        mock_product_service.get_brand_detail.return_value = None
        brand_controller.product_service = mock_product_service
        
        result = brand_controller.get_brand_detail('不存在的品牌')
        
        assert result is None
    
    def test_get_brand_detail_url_encoded(self, brand_controller, mock_product_service):
        """测试URL编码的品牌名"""
        brand_controller.product_service = mock_product_service
        
        with patch('backend.controllers.brand_controller.BrandLike') as mock_brand_like:
            mock_brand_like.get_like_count.return_value = 5
            
            # URL编码的品牌名
            result = brand_controller.get_brand_detail('%E6%B1%9F%E5%8D%97%E6%98%A5')
            
            assert result is not None
            assert result['success'] is True

    def test_get_brand_images_only_success(self, brand_controller):
        """测试轻量品牌图片接口"""
        mock_images = [
            {'filename': 'a-设计图-01.jpg', 'image_type': '设计图'},
            {'filename': 'a-布料图-01.jpg', 'image_type': '布料图'},
        ]
        with patch('backend.services.image_service.ImageService') as mock_image_service:
            mock_image_service.return_value.get_brand_images.return_value = mock_images
            with patch('backend.services.cache_service.cache_service') as mock_cache:
                mock_cache.get.return_value = None
                result = brand_controller.get_brand_images_only('江南春')
                assert result is not None
                assert result['success'] is True
                assert len(result['images']) == 2
                mock_cache.set.assert_called_once()
    
    def test_toggle_like_success(self, brand_controller):
        """测试成功切换点赞状态"""
        with patch('backend.controllers.brand_controller.BrandLike') as mock_brand_like:
            mock_brand_like.toggle_like.return_value = (True, 11, True)
            
            result = brand_controller.toggle_like('江南春', 'unique_id_123', '127.0.0.1', 'test-agent')
            
            assert result['success'] is True
            assert result['liked'] is True
            assert result['like_count'] == 11
            assert '点赞成功' in result['message']
    
    def test_toggle_like_failure(self, brand_controller):
        """测试点赞失败"""
        with patch('backend.controllers.brand_controller.BrandLike') as mock_brand_like:
            mock_brand_like.toggle_like.return_value = (False, '操作失败', False)
            mock_brand_like.get_like_count.return_value = 10
            
            result = brand_controller.toggle_like('江南春', 'unique_id_123', '127.0.0.1', 'test-agent')
            
            assert result['success'] is False
            assert result['like_count'] == 10

    def test_toggle_like_db_exception_returns_error(self, brand_controller):
        """DB 异常时不得回退内存计数（避免与库分叉）"""
        with patch('backend.controllers.brand_controller.BrandLike') as mock_brand_like:
            mock_brand_like.toggle_like.side_effect = RuntimeError('db down')

            result = brand_controller.toggle_like(
                '江南春', 'unique_id_123', '127.0.0.1', 'test-agent'
            )

            assert result['success'] is False
            assert '不可用' in result['message'] or '失败' in result['message']
    
    def test_get_like_status_success(self, brand_controller):
        """测试成功获取点赞状态"""
        with patch('backend.controllers.brand_controller.BrandLike') as mock_brand_like:
            mock_brand_like.check_user_liked.return_value = True
            mock_brand_like.get_like_count.return_value = 15
            
            result = brand_controller.get_like_status('江南春', 'unique_id_123')
            
            assert result['success'] is True
            assert result['liked'] is True
            assert result['like_count'] == 15


class TestProductController:
    """测试产品控制器"""
    
    @pytest.fixture
    def product_controller(self):
        """创建产品控制器实例"""
        return ProductController()
    
    @pytest.fixture
    def mock_product_service(self):
        """创建模拟产品服务"""
        mock_service = Mock()
        
        # Mock分页结果
        mock_pagination = Mock()
        mock_pagination.items = []
        mock_pagination.page = 1
        mock_pagination.pages = 1
        mock_pagination.per_page = 20
        mock_pagination.total = 0
        mock_pagination.has_next = False
        mock_pagination.has_prev = False
        
        mock_service.get_all_products.return_value = mock_pagination
        mock_service.get_statistics.return_value = {
            'total_products': 100,
            'total_brands': 50,
            'total_images': 200
        }
        
        return mock_service
    
    def test_get_products_success(self, product_controller, mock_product_service):
        """测试成功获取产品列表"""
        product_controller.product_service = mock_product_service
        
        result = product_controller.get_products(page=1, per_page=20)
        
        assert result['success'] is True
        assert 'products' in result
        assert 'pagination' in result
        assert result['pagination']['page'] == 1
    
    def test_get_products_with_search(self, product_controller, mock_product_service):
        """测试带搜索条件获取产品列表"""
        product_controller.product_service = mock_product_service
        
        result = product_controller.get_products(page=1, per_page=20, search='测试')
        
        # 验证调用了带搜索条件的服务方法
        mock_product_service.get_all_products.assert_called_once()
        call_args = mock_product_service.get_all_products.call_args
        assert call_args[1]['search'] == '测试'
    
    def test_get_products_with_filters(self, product_controller, mock_product_service):
        """测试带筛选条件获取产品列表"""
        product_controller.product_service = mock_product_service
        
        filters = {'year': '2024', 'material': '棉麻'}
        result = product_controller.get_products(page=1, per_page=20, filters=filters)
        
        # 验证调用了带筛选条件的服务方法
        call_args = mock_product_service.get_all_products.call_args
        assert call_args[1]['filters'] == filters
    
    def test_get_products_service_failure(self, product_controller, mock_product_service):
        """测试服务返回None的情况"""
        mock_product_service.get_all_products.return_value = None
        product_controller.product_service = mock_product_service
        
        result = product_controller.get_products()
        
        assert result['success'] is False
        assert 'error' in result
    
    def test_get_statistics_success(self, product_controller, mock_product_service):
        """测试成功获取统计信息"""
        product_controller.product_service = mock_product_service
        
        result = product_controller.get_statistics()
        
        assert result['success'] is True
        assert 'statistics' in result
        assert result['statistics']['total_products'] == 100
    
    def test_get_filter_options_success(self, product_controller):
        """测试成功获取筛选选项"""
        # Mock产品数据
        mock_products = []
        for i in range(3):
            mock_product = Mock()
            mock_product.year = 2024
            mock_product.material = '棉麻'
            mock_product.theme_series = '经典系列'
            mock_product.print_size = '循环印花料'
            mock_products.append(mock_product)
        
        with patch('backend.controllers.product_controller.Product') as mock_product_class:
            mock_product_class.query.all.return_value = mock_products
            
            result = product_controller.get_filter_options()
            
            assert result['success'] is True
            assert 'filters' in result
            assert 'years' in result['filters']
            assert 'materials' in result['filters']
            assert 'theme_series' in result['filters']
            assert 'print_sizes' in result['filters']
    
    def test_get_filter_options_database_error(self, product_controller):
        """测试数据库查询失败的情况"""
        with patch('backend.controllers.product_controller.Product') as mock_product_class:
            mock_product_class.query.all.side_effect = Exception('数据库错误')
            
            result = product_controller.get_filter_options()
            
            # 应该返回默认选项
            assert result['success'] is True
            assert 'filters' in result
            assert 'years' in result['filters']
    
    def test_generate_share_card_success(self, product_controller, mock_product_service):
        """测试成功生成分享卡片"""
        mock_product_service.get_brand_detail.return_value = {
            'name': '江南春',
            'year': 2024,
            'material': '棉麻',
            'theme_series': '经典系列',
            'print_size': '循环印花料',
            'inspiration_origin': '测试灵感',
            'images': [
                {'image_type': '概念图', 'url': 'http://test.com/img1.jpg'},
                {'image_type': '设计图', 'url': 'http://test.com/img2.jpg'},
                {'image_type': '布料图', 'url': 'http://test.com/img3.jpg'},
                {'image_type': '布料图', 'url': 'http://test.com/img4.jpg'}
            ]
        }
        product_controller.product_service = mock_product_service
        
        # BrandLike是在函数内部导入的，需要patch导入路径
        with patch('backend.models.brand_like.BrandLike') as mock_brand_like:
            mock_brand_like.get_like_count.return_value = 20
            
            result = product_controller.generate_share_card('江南春', 'localhost:8500')
            
            assert result['success'] is True
            assert 'card_data' in result
            assert 'card_url' in result
            assert result['card_data']['brand_name'] == '江南春'
            assert result['card_data']['like_count'] == 20
            imgs = result['card_data']['images']
            assert len(imgs) == 4
            assert [i['image_type'] for i in imgs] == ['概念图', '设计图', '布料图', '布料图']

    def test_generate_share_card_image_selection_rules(self, product_controller, mock_product_service):
        """分享卡片选图：概念/设计全取；布料/模特按花色各最多2张；成衣/买家秀各最多2张"""
        mock_product_service.get_brand_detail.return_value = {
            'name': '测试款',
            'year': 2024,
            'material': '棉麻',
            'theme_series': '系列',
            'print_size': '印花',
            'inspiration_origin': '灵感',
            'images': [
                {'image_type': '概念图', 'url': 'http://test.com/c1.jpg', 'filename': 'a-概念图-1.jpg'},
                {'image_type': '概念图', 'url': 'http://test.com/c2.jpg', 'filename': 'a-概念图-2.jpg'},
                {'image_type': '设计图', 'url': 'http://test.com/d1.jpg', 'filename': 'a-设计图-1.jpg'},
                {'image_type': '布料图', 'url': 'http://test.com/f1.jpg', 'filename': 'a(红)-布料图-1.jpg'},
                {'image_type': '布料图', 'url': 'http://test.com/f2.jpg', 'filename': 'a(红)-布料图-2.jpg'},
                {'image_type': '布料图', 'url': 'http://test.com/f3.jpg', 'filename': 'a(红)-布料图-3.jpg'},
                {'image_type': '布料图', 'url': 'http://test.com/f4.jpg', 'filename': 'a(蓝)-布料图-1.jpg'},
                {'image_type': '布料图', 'url': 'http://test.com/f5.jpg', 'filename': 'a(蓝)-布料图-2.jpg'},
                {'image_type': '布料图', 'url': 'http://test.com/f6.jpg', 'filename': 'a(蓝)-布料图-3.jpg'},
                {'image_type': '成衣图', 'url': 'http://test.com/g1.jpg', 'filename': 'a-成衣图-1.jpg'},
                {'image_type': '成衣图', 'url': 'http://test.com/g2.jpg', 'filename': 'a-成衣图-2.jpg'},
                {'image_type': '成衣图', 'url': 'http://test.com/g3.jpg', 'filename': 'a-成衣图-3.jpg'},
                {'image_type': '买家秀图', 'url': 'http://test.com/b1.jpg', 'filename': 'a-买家秀图-1.jpg'},
                {'image_type': '模特图', 'url': 'http://test.com/m1.jpg', 'filename': 'a(红)-模特图-1.jpg'},
                {'image_type': '模特图', 'url': 'http://test.com/m2.jpg', 'filename': 'a(红)-模特图-2.jpg'},
                {'image_type': '模特图', 'url': 'http://test.com/m3.jpg', 'filename': 'a(红)-模特图-3.jpg'},
                {'image_type': '模特图', 'url': 'http://test.com/m4.jpg', 'filename': 'a(蓝)-模特图-1.jpg'},
                {'image_type': '模特图', 'url': 'http://test.com/m5.jpg', 'filename': 'a(蓝)-模特图-2.jpg'},
            ]
        }
        product_controller.product_service = mock_product_service
        with patch('backend.models.brand_like.BrandLike') as mock_brand_like:
            mock_brand_like.get_like_count.return_value = 0
            result = product_controller.generate_share_card('测试款', 'localhost:8500')
        assert result['success'] is True
        types = [i['image_type'] for i in result['card_data']['images']]
        assert types.count('概念图') == 2
        assert types.count('设计图') == 1
        assert types.count('布料图') == 4
        assert types.count('成衣图') == 2
        assert types.count('买家秀图') == 1
        assert types.count('模特图') == 4
        assert types == [
            '概念图', '概念图', '设计图',
            '布料图', '布料图', '布料图', '布料图',
            '成衣图', '成衣图',
            '买家秀图',
            '模特图', '模特图', '模特图', '模特图',
        ]
    
    def test_generate_share_card_brand_not_found(self, product_controller, mock_product_service):
        """测试品牌不存在的情况"""
        mock_product_service.get_brand_detail.return_value = None
        product_controller.product_service = mock_product_service
        
        result = product_controller.generate_share_card('不存在的品牌', 'localhost:8500')
        
        assert result['success'] is False
        assert 'error' in result
    
    def test_generate_share_card_url_encoded(self, product_controller, mock_product_service):
        """测试URL编码的品牌名"""
        mock_product_service.get_brand_detail.return_value = {
            'name': '江南春',
            'year': 2024,
            'material': '棉麻',
            'theme_series': '经典系列',
            'print_size': '循环印花料',
            'inspiration_origin': '测试灵感',
            'images': []
        }
        product_controller.product_service = mock_product_service
        
        # BrandLike是在函数内部导入的，需要patch导入路径
        with patch('backend.models.brand_like.BrandLike') as mock_brand_like:
            mock_brand_like.get_like_count.return_value = 0
            
            # URL编码的品牌名
            result = product_controller.generate_share_card('%E6%B1%9F%E5%8D%97%E6%98%A5', 'localhost:8500')
            
            assert result['success'] is True
