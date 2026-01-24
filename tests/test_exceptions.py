#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
异常处理测试
测试统一异常处理体系的功能
"""

import pytest
from backend.exceptions import (
    BaseAPIException,
    ValidationError,
    NotFoundError,
    PermissionError,
    DatabaseError,
    ServiceError,
    AuthenticationError,
    RateLimitError
)


class TestBaseAPIException:
    """测试基础异常类"""
    
    def test_base_exception_initialization(self):
        """测试基础异常初始化"""
        exception = BaseAPIException(
            message='测试错误',
            status_code=400,
            error_code='TEST_ERROR',
            details={'field': 'test_field'}
        )
        
        assert exception.message == '测试错误'
        assert exception.status_code == 400
        assert exception.error_code == 'TEST_ERROR'
        assert exception.details == {'field': 'test_field'}
    
    def test_base_exception_to_dict(self):
        """测试异常转换为字典"""
        exception = BaseAPIException(
            message='测试错误',
            status_code=400,
            error_code='TEST_ERROR',
            details={'field': 'test_field'}
        )
        
        result = exception.to_dict()
        
        assert result['success'] is False
        assert result['error'] == '测试错误'
        assert result['error_code'] == 'TEST_ERROR'
        assert result['status_code'] == 400
        assert result['field'] == 'test_field'
    
    def test_base_exception_default_error_code(self):
        """测试默认错误代码"""
        exception = BaseAPIException(message='测试错误')
        
        assert exception.error_code == 'BaseAPIException'
        assert exception.status_code == 500


class TestValidationError:
    """测试参数验证错误"""
    
    def test_validation_error_default(self):
        """测试默认验证错误"""
        error = ValidationError()
        
        assert error.message == '参数验证失败'
        assert error.status_code == 400
        assert error.error_code == 'VALIDATION_ERROR'
    
    def test_validation_error_with_field(self):
        """测试带字段信息的验证错误"""
        error = ValidationError(
            message='字段验证失败',
            field='username',
            value='test'
        )
        
        assert error.message == '字段验证失败'
        assert error.details['field'] == 'username'
        assert error.details['value'] == 'test'
    
    def test_validation_error_custom_details(self):
        """测试自定义详情的验证错误"""
        error = ValidationError(
            message='验证失败',
            details={'custom': 'value'}
        )
        
        assert error.details['custom'] == 'value'


class TestNotFoundError:
    """测试资源不存在错误"""
    
    def test_not_found_error_default(self):
        """测试默认资源不存在错误"""
        error = NotFoundError()
        
        assert error.message == '资源不存在'
        assert error.status_code == 404
        assert error.error_code == 'NOT_FOUND'
    
    def test_not_found_error_with_resource_info(self):
        """测试带资源信息的错误"""
        error = NotFoundError(
            message='产品不存在',
            resource_type='product',
            resource_id=123
        )
        
        assert error.details['resource_type'] == 'product'
        assert error.details['resource_id'] == 123


class TestPermissionError:
    """测试权限错误"""
    
    def test_permission_error_default(self):
        """测试默认权限错误"""
        error = PermissionError()
        
        assert error.message == '权限不足'
        assert error.status_code == 403
        assert error.error_code == 'PERMISSION_DENIED'
    
    def test_permission_error_with_required_permission(self):
        """测试带所需权限的错误"""
        error = PermissionError(
            message='需要管理员权限',
            required_permission='admin'
        )
        
        assert error.details['required_permission'] == 'admin'


class TestDatabaseError:
    """测试数据库错误"""
    
    def test_database_error_default(self):
        """测试默认数据库错误"""
        error = DatabaseError()
        
        assert error.message == '数据库操作失败'
        assert error.status_code == 500
        assert error.error_code == 'DATABASE_ERROR'
    
    def test_database_error_with_operation(self):
        """测试带操作类型的错误"""
        error = DatabaseError(
            message='查询失败',
            operation='query'
        )
        
        assert error.details['operation'] == 'query'


class TestServiceError:
    """测试服务层错误"""
    
    def test_service_error_default(self):
        """测试默认服务错误"""
        error = ServiceError()
        
        assert error.message == '服务处理失败'
        assert error.status_code == 500
        assert error.error_code == 'SERVICE_ERROR'
    
    def test_service_error_with_service_name(self):
        """测试带服务名称的错误"""
        error = ServiceError(
            message='产品服务错误',
            service_name='ProductService'
        )
        
        assert error.details['service_name'] == 'ProductService'


class TestAuthenticationError:
    """测试认证错误"""
    
    def test_authentication_error_default(self):
        """测试默认认证错误"""
        error = AuthenticationError()
        
        assert error.message == '认证失败'
        assert error.status_code == 401
        assert error.error_code == 'AUTHENTICATION_ERROR'
    
    def test_authentication_error_with_reason(self):
        """测试带失败原因的错误"""
        error = AuthenticationError(
            message='登录失败',
            reason='密码错误'
        )
        
        assert error.details['reason'] == '密码错误'


class TestRateLimitError:
    """测试限流错误"""
    
    def test_rate_limit_error_default(self):
        """测试默认限流错误"""
        error = RateLimitError()
        
        assert error.message == '请求过于频繁，请稍后再试'
        assert error.status_code == 429
        assert error.error_code == 'RATE_LIMIT_EXCEEDED'
    
    def test_rate_limit_error_with_retry_after(self):
        """测试带重试时间的错误"""
        error = RateLimitError(
            message='请求过于频繁',
            retry_after=60
        )
        
        assert error.details['retry_after'] == 60


class TestExceptionInheritance:
    """测试异常继承关系"""
    
    def test_all_exceptions_inherit_from_base(self):
        """测试所有异常都继承自BaseAPIException"""
        exceptions = [
            ValidationError(),
            NotFoundError(),
            PermissionError(),
            DatabaseError(),
            ServiceError(),
            AuthenticationError(),
            RateLimitError()
        ]
        
        for exc in exceptions:
            assert isinstance(exc, BaseAPIException)
            assert isinstance(exc, Exception)
    
    def test_exception_to_dict_consistency(self):
        """测试异常字典格式的一致性"""
        exceptions = [
            ValidationError('测试'),
            NotFoundError('测试'),
            PermissionError('测试'),
            DatabaseError('测试'),
            ServiceError('测试'),
            AuthenticationError('测试'),
            RateLimitError('测试')
        ]
        
        for exc in exceptions:
            result = exc.to_dict()
            # 所有异常字典都应该包含success和error字段
            assert 'success' in result
            assert 'error' in result
            assert 'error_code' in result
            assert 'status_code' in result
            assert result['success'] is False
