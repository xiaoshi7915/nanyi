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
            # 验证图片数量限制（布料图2张，其他各1张）
            assert len(result['card_data']['images']) <= 4
    
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
