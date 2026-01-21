#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
参数验证器测试
测试统一参数验证模块的功能
"""

import pytest
from flask import Flask, request
from backend.exceptions import ValidationError
from backend.utils.validators import (
    validate_pagination,
    validate_search,
    validate_brand_name,
    validate_integer,
    validate_string,
    validate_request,
    validate_request_decorator,
    validate_filters,
    validate_boolean
)


@pytest.fixture
def app():
    """创建Flask应用用于测试"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    return app


class TestValidatePagination:
    """测试分页参数验证"""
    
    def test_validate_pagination_default(self, app):
        """测试默认分页参数"""
        with app.test_request_context('/?page=1&per_page=12'):
            page, per_page = validate_pagination()
            assert page == 1
            assert per_page == 12
    
    def test_validate_pagination_custom(self, app):
        """测试自定义分页参数"""
        with app.test_request_context('/?page=2&per_page=20'):
            page, per_page = validate_pagination()
            assert page == 2
            assert per_page == 20
    
    def test_validate_pagination_explicit_params(self):
        """测试显式传入参数"""
        page, per_page = validate_pagination(page=3, per_page=30)
        assert page == 3
        assert per_page == 30
    
    def test_validate_pagination_invalid_page(self, app):
        """测试无效页码"""
        with app.test_request_context('/'):
            with pytest.raises(ValidationError) as exc_info:
                validate_pagination(page=0)
            
            assert exc_info.value.details.get('field') == 'page'
            assert exc_info.value.status_code == 400
    
    def test_validate_pagination_invalid_per_page(self, app):
        """测试无效每页数量"""
        with app.test_request_context('/'):
            with pytest.raises(ValidationError) as exc_info:
                validate_pagination(per_page=0)
            
            assert exc_info.value.details.get('field') == 'per_page'
            assert exc_info.value.status_code == 400
    
    def test_validate_pagination_max_limit(self, app):
        """测试最大每页数量限制"""
        with app.test_request_context('/'):
            page, per_page = validate_pagination(per_page=200, max_per_page=100)
            assert per_page == 100  # 应该被限制为100


class TestValidateSearch:
    """测试搜索关键词验证"""
    
    def test_validate_search_default(self, app):
        """测试默认搜索关键词"""
        with app.test_request_context('/?search=test'):
            search = validate_search()
            assert search == 'test'
    
    def test_validate_search_empty(self, app):
        """测试空搜索关键词"""
        with app.test_request_context('/'):
            search = validate_search()
            assert search is None
    
    def test_validate_search_explicit(self):
        """测试显式传入搜索关键词"""
        search = validate_search(search='测试')
        assert search == '测试'
    
    def test_validate_search_too_short(self, app):
        """测试搜索关键词太短"""
        with app.test_request_context('/?search=a'):
            # 空字符串会返回None，不会抛出异常
            # 这里测试一个字符的情况（min_length=2）
            with pytest.raises(ValidationError) as exc_info:
                validate_search(search='a', min_length=2)
            
            assert exc_info.value.details.get('field') == 'search'
    
    def test_validate_search_too_long(self, app):
        """测试搜索关键词太长"""
        with app.test_request_context('/'):
            long_search = 'a' * 101
            with pytest.raises(ValidationError) as exc_info:
                validate_search(search=long_search, max_length=100)
            
            assert exc_info.value.details.get('field') == 'search'
    
    def test_validate_search_strip_whitespace(self):
        """测试去除空白字符"""
        search = validate_search(search='  test  ')
        assert search == 'test'


class TestValidateBrandName:
    """测试品牌名称验证"""
    
    def test_validate_brand_name_valid(self):
        """测试有效品牌名称"""
        brand_name = validate_brand_name('江南春')
        assert brand_name == '江南春'
    
    def test_validate_brand_name_empty(self):
        """测试空品牌名称"""
        with pytest.raises(ValidationError) as exc_info:
            validate_brand_name('')
        
        assert exc_info.value.details.get('field') == 'brand_name'
        assert exc_info.value.status_code == 400
    
    def test_validate_brand_name_allow_empty(self):
        """测试允许空品牌名称"""
        brand_name = validate_brand_name('', allow_empty=True)
        assert brand_name == ''
    
    def test_validate_brand_name_too_long(self):
        """测试品牌名称太长"""
        long_name = 'a' * 101
        with pytest.raises(ValidationError) as exc_info:
            validate_brand_name(long_name)
        
        assert exc_info.value.details.get('field') == 'brand_name'
    
    def test_validate_brand_name_strip_whitespace(self):
        """测试去除空白字符"""
        brand_name = validate_brand_name('  江南春  ')
        assert brand_name == '江南春'


class TestValidateInteger:
    """测试整数验证"""
    
    def test_validate_integer_valid(self):
        """测试有效整数"""
        value = validate_integer(123, 'test_field')
        assert value == 123
    
    def test_validate_integer_string(self):
        """测试字符串形式的整数"""
        value = validate_integer('123', 'test_field')
        assert value == 123
    
    def test_validate_integer_none_not_allowed(self):
        """测试不允许None值"""
        with pytest.raises(ValidationError) as exc_info:
            validate_integer(None, 'test_field')
        
        assert exc_info.value.details.get('field') == 'test_field'
    
    def test_validate_integer_none_allowed(self):
        """测试允许None值"""
        value = validate_integer(None, 'test_field', allow_none=True)
        assert value is None
    
    def test_validate_integer_invalid_type(self):
        """测试无效类型"""
        with pytest.raises(ValidationError) as exc_info:
            validate_integer('abc', 'test_field')
        
        assert exc_info.value.details.get('field') == 'test_field'
    
    def test_validate_integer_min_value(self):
        """测试最小值限制"""
        with pytest.raises(ValidationError) as exc_info:
            validate_integer(5, 'test_field', min_value=10)
        
        assert exc_info.value.details.get('field') == 'test_field'
    
    def test_validate_integer_max_value(self):
        """测试最大值限制"""
        with pytest.raises(ValidationError) as exc_info:
            validate_integer(150, 'test_field', max_value=100)
        
        assert exc_info.value.details.get('field') == 'test_field'


class TestValidateString:
    """测试字符串验证"""
    
    def test_validate_string_valid(self):
        """测试有效字符串"""
        value = validate_string('test', 'test_field')
        assert value == 'test'
    
    def test_validate_string_empty_not_allowed(self):
        """测试不允许空字符串"""
        with pytest.raises(ValidationError) as exc_info:
            validate_string('', 'test_field')
        
        assert exc_info.value.details.get('field') == 'test_field'
    
    def test_validate_string_empty_allowed(self):
        """测试允许空字符串"""
        value = validate_string('', 'test_field', allow_empty=True)
        assert value == ''
    
    def test_validate_string_none_not_allowed(self):
        """测试不允许None值"""
        with pytest.raises(ValidationError) as exc_info:
            validate_string(None, 'test_field')
        
        assert exc_info.value.details.get('field') == 'test_field'
    
    def test_validate_string_none_allowed(self):
        """测试允许None值"""
        value = validate_string(None, 'test_field', allow_none=True)
        assert value is None
    
    def test_validate_string_min_length(self):
        """测试最小长度限制"""
        with pytest.raises(ValidationError) as exc_info:
            validate_string('ab', 'test_field', min_length=5)
        
        assert exc_info.value.details.get('field') == 'test_field'
    
    def test_validate_string_max_length(self):
        """测试最大长度限制"""
        long_string = 'a' * 101
        with pytest.raises(ValidationError) as exc_info:
            validate_string(long_string, 'test_field', max_length=100)
        
        assert exc_info.value.details.get('field') == 'test_field'
    
    def test_validate_string_strip_whitespace(self):
        """测试去除空白字符"""
        value = validate_string('  test  ', 'test_field')
        assert value == 'test'


class TestValidateRequest:
    """测试请求参数验证"""
    
    def test_validate_request_get(self, app):
        """测试GET请求参数验证"""
        with app.test_request_context('/?param1=value1&param2=value2'):
            params = validate_request(
                required_params=['param1'],
                optional_params={'param2': 'default2'}
            )
            
            assert params['param1'] == 'value1'
            assert params['param2'] == 'value2'
    
    def test_validate_request_post(self, app):
        """测试POST请求参数验证"""
        with app.test_request_context(
            '/',
            method='POST',
            json={'param1': 'value1', 'param2': 'value2'}
        ):
            params = validate_request(
                required_params=['param1'],
                optional_params={'param2': 'default2'}
            )
            
            assert params['param1'] == 'value1'
            assert params['param2'] == 'value2'
    
    def test_validate_request_missing_required(self, app):
        """测试缺少必需参数"""
        with app.test_request_context('/?param2=value2'):
            with pytest.raises(ValidationError) as exc_info:
                validate_request(required_params=['param1'])
            
            assert 'param1' in exc_info.value.message
    
    def test_validate_request_optional_default(self, app):
        """测试可选参数默认值"""
        with app.test_request_context('/?param1=value1'):
            params = validate_request(
                required_params=['param1'],
                optional_params={'param2': 'default2'}
            )
            
            assert params['param2'] == 'default2'


class TestValidateFilters:
    """测试筛选参数验证"""
    
    def test_validate_filters_default(self, app):
        """测试默认筛选参数"""
        with app.test_request_context('/?year=2024&material=棉麻'):
            filters = validate_filters()
            
            assert 'year' in filters
            assert 'material' in filters
            assert filters['year'] == '2024'
            assert filters['material'] == '棉麻'
    
    def test_validate_filters_allowed_list(self, app):
        """测试允许的筛选字段列表"""
        with app.test_request_context('/?year=2024&material=棉麻&invalid=value'):
            filters = validate_filters(allowed_filters=['year', 'material'])
            
            assert 'year' in filters
            assert 'material' in filters
            assert 'invalid' not in filters
    
    def test_validate_filters_explicit(self):
        """测试显式传入筛选参数"""
        filters = validate_filters(
            filters={'year': '2024', 'material': '棉麻'},
            allowed_filters=['year']
        )
        
        assert 'year' in filters
        assert 'material' not in filters


class TestValidateBoolean:
    """测试布尔值验证"""
    
    def test_validate_boolean_true_strings(self):
        """测试字符串形式的True值"""
        assert validate_boolean('true', 'test_field') is True
        assert validate_boolean('1', 'test_field') is True
        assert validate_boolean('yes', 'test_field') is True
        assert validate_boolean('on', 'test_field') is True
    
    def test_validate_boolean_false_strings(self):
        """测试字符串形式的False值"""
        assert validate_boolean('false', 'test_field') is False
        assert validate_boolean('0', 'test_field') is False
        assert validate_boolean('no', 'test_field') is False
        assert validate_boolean('off', 'test_field') is False
        assert validate_boolean('', 'test_field') is False
    
    def test_validate_boolean_integer(self):
        """测试整数形式的布尔值"""
        assert validate_boolean(1, 'test_field') is True
        assert validate_boolean(0, 'test_field') is False
    
    def test_validate_boolean_bool(self):
        """测试布尔值"""
        assert validate_boolean(True, 'test_field') is True
        assert validate_boolean(False, 'test_field') is False
    
    def test_validate_boolean_none_default(self):
        """测试None值使用默认值"""
        assert validate_boolean(None, 'test_field', default=True) is True
        assert validate_boolean(None, 'test_field', default=False) is False
    
    def test_validate_boolean_invalid_default(self):
        """测试无效值使用默认值"""
        assert validate_boolean('invalid', 'test_field', default=True) is True
        assert validate_boolean('invalid', 'test_field', default=False) is False


class TestValidateRequestDecorator:
    """测试请求参数验证装饰器"""
    
    def test_validate_request_decorator_success(self, app):
        """测试装饰器成功验证"""
        @validate_request_decorator(required_params=['param1'])
        def test_function(param1):
            from flask import jsonify
            return jsonify({'success': True, 'param1': param1})
        
        with app.test_request_context('/?param1=value1'):
            result = test_function()
            assert result.status_code == 200
    
    def test_validate_request_decorator_missing_param(self, app):
        """测试装饰器缺少参数"""
        @validate_request_decorator(required_params=['param1'])
        def test_function():
            from flask import jsonify
            return jsonify({'success': True})
        
        with app.test_request_context('/'):
            result = test_function()
            # 装饰器返回的是tuple (response, status_code)
            if isinstance(result, tuple):
                assert result[1] == 400  # status_code在第二个位置
            else:
                assert result.status_code == 400
