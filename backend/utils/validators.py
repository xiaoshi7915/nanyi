#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
参数验证模块
提取公共验证逻辑，统一参数验证规则
"""

from functools import wraps
from flask import request, jsonify
from typing import Dict, Any, Optional, Tuple, List
import logging
import re

from backend.exceptions import ValidationError

logger = logging.getLogger(__name__)

# 缓存清理 pattern：仅允许线性安全的字面量子集（避免复杂正则 ReDoS）
_CACHE_CLEAR_PATTERN_SAFE = re.compile(r'^[a-zA-Z0-9_.\-\/]{1,200}$')


def validate_cache_clear_pattern(pattern) -> str:
    """
    校验 /api/cache/clear 的 pattern。
    缺省或显式 ``.*`` 时由服务端使用全量匹配；自定义 pattern 仅允许安全字符集且长度 <= 200。
    """
    if pattern is None:
        return '.*'
    if not isinstance(pattern, str):
        raise ValidationError(
            message='pattern 必须为字符串',
            field='pattern',
            value=pattern,
        )
    p = pattern.strip()
    if not p or p == '.*':
        return '.*'
    if len(p) > 200:
        raise ValidationError(
            message='pattern 长度不能超过 200',
            field='pattern',
            value=pattern,
        )
    if not _CACHE_CLEAR_PATTERN_SAFE.match(p):
        raise ValidationError(
            message='pattern 仅允许字母、数字、下划线、点、横线、斜杠',
            field='pattern',
            value=pattern,
        )
    return p


def validate_pagination(page: int = None, per_page: int = None, max_per_page: int = 100) -> Tuple[int, int]:
    """
    验证和规范化分页参数
    
    Args:
        page: 页码（从请求参数获取，如果为None则从request.args获取）
        per_page: 每页数量（从请求参数获取，如果为None则从request.args获取）
        max_per_page: 每页最大数量限制
    
    Returns:
        tuple: (page, per_page) 规范化后的分页参数
    
    Raises:
        ValidationError: 当参数无效时抛出
    
    Example:
        >>> page, per_page = validate_pagination()
        >>> page, per_page = validate_pagination(page=1, per_page=20, max_per_page=50)
    """
    # 从请求参数获取分页参数（如果未提供）
    if page is None:
        try:
            page = request.args.get('page', 1, type=int)
        except (ValueError, TypeError):
            page = 1
    
    if per_page is None:
        try:
            per_page = request.args.get('per_page', 12, type=int)
        except (ValueError, TypeError):
            per_page = 12
    
    # 验证页码
    if page < 1:
        raise ValidationError(
            message=f'页码必须大于0，当前值: {page}',
            field='page',
            value=page
        )
    
    # 验证每页数量
    if per_page < 1:
        raise ValidationError(
            message=f'每页数量必须大于0，当前值: {per_page}',
            field='per_page',
            value=per_page
        )
    
    # 限制每页最大数量
    if per_page > max_per_page:
        logger.warning(f'每页数量超过限制 {max_per_page}，已自动调整为 {max_per_page}')
        per_page = max_per_page
    
    return page, per_page


def validate_search(search: str = None, min_length: int = 1, max_length: int = 100) -> Optional[str]:
    """
    验证搜索关键词
    
    Args:
        search: 搜索关键词（从请求参数获取，如果为None则从request.args获取）
        min_length: 最小长度
        max_length: 最大长度
    
    Returns:
        str: 规范化后的搜索关键词，如果为空则返回None
    
    Raises:
        ValidationError: 当搜索关键词长度不符合要求时抛出
    
    Example:
        >>> search = validate_search()
        >>> search = validate_search(search='test', min_length=2, max_length=50)
    """
    # 从请求参数获取搜索关键词（如果未提供）
    if search is None:
        search = request.args.get('search', '').strip()
    else:
        search = str(search).strip()
    
    # 如果搜索关键词为空，返回None
    if not search:
        return None
    
    # 验证长度
    if len(search) < min_length:
        raise ValidationError(
            message=f'搜索关键词长度至少为 {min_length} 个字符',
            field='search',
            value=search
        )
    
    if len(search) > max_length:
        raise ValidationError(
            message=f'搜索关键词长度不能超过 {max_length} 个字符',
            field='search',
            value=search
        )
    
    return search


def validate_brand_name(brand_name: str, allow_empty: bool = False) -> str:
    """
    验证品牌名称
    
    Args:
        brand_name: 品牌名称
        allow_empty: 是否允许为空
    
    Returns:
        str: 规范化后的品牌名称
    
    Raises:
        ValidationError: 当品牌名称无效时抛出
    
    Example:
        >>> brand_name = validate_brand_name('江南春')
        >>> brand_name = validate_brand_name('', allow_empty=True)
    """
    if not brand_name:
        if allow_empty:
            return ''
        raise ValidationError(
            message='品牌名称不能为空',
            field='brand_name',
            value=brand_name
        )
    
    brand_name = str(brand_name).strip()
    
    if not brand_name and not allow_empty:
        raise ValidationError(
            message='品牌名称不能为空',
            field='brand_name',
            value=brand_name
        )
    
    # 验证长度（品牌名称通常不超过100个字符）
    if len(brand_name) > 100:
        raise ValidationError(
            message='品牌名称长度不能超过100个字符',
            field='brand_name',
            value=brand_name
        )
    
    return brand_name


def validate_integer(value: Any, field_name: str, min_value: int = None, max_value: int = None, allow_none: bool = False) -> Optional[int]:
    """
    验证整数参数
    
    Args:
        value: 要验证的值
        field_name: 字段名称（用于错误消息）
        min_value: 最小值
        max_value: 最大值
        allow_none: 是否允许为None
    
    Returns:
        int: 验证后的整数值，如果允许None且值为None则返回None
    
    Raises:
        ValidationError: 当值无效时抛出
    
    Example:
        >>> year = validate_integer(2024, 'year', min_value=2000, max_value=2100)
        >>> page = validate_integer(None, 'page', allow_none=True)
    """
    if value is None:
        if allow_none:
            return None
        raise ValidationError(
            message=f'{field_name}不能为空',
            field=field_name,
            value=value
        )
    
    try:
        int_value = int(value)
    except (ValueError, TypeError):
        raise ValidationError(
            message=f'{field_name}必须是整数',
            field=field_name,
            value=value
        )
    
    if min_value is not None and int_value < min_value:
        raise ValidationError(
            message=f'{field_name}不能小于 {min_value}',
            field=field_name,
            value=int_value
        )
    
    if max_value is not None and int_value > max_value:
        raise ValidationError(
            message=f'{field_name}不能大于 {max_value}',
            field=field_name,
            value=int_value
        )
    
    return int_value


def validate_string(value: Any, field_name: str, min_length: int = None, max_length: int = None, allow_empty: bool = False, allow_none: bool = False) -> Optional[str]:
    """
    验证字符串参数
    
    Args:
        value: 要验证的值
        field_name: 字段名称（用于错误消息）
        min_length: 最小长度
        max_length: 最大长度
        allow_empty: 是否允许为空字符串
        allow_none: 是否允许为None
    
    Returns:
        str: 验证后的字符串，如果允许None且值为None则返回None
    
    Raises:
        ValidationError: 当值无效时抛出
    
    Example:
        >>> title = validate_string('测试标题', 'title', min_length=1, max_length=200)
        >>> description = validate_string(None, 'description', allow_none=True)
    """
    if value is None:
        if allow_none:
            return None
        raise ValidationError(
            message=f'{field_name}不能为空',
            field=field_name,
            value=value
        )
    
    str_value = str(value).strip()
    
    if not str_value and not allow_empty:
        raise ValidationError(
            message=f'{field_name}不能为空',
            field=field_name,
            value=str_value
        )
    
    if min_length is not None and len(str_value) < min_length:
        raise ValidationError(
            message=f'{field_name}长度至少为 {min_length} 个字符',
            field=field_name,
            value=str_value
        )
    
    if max_length is not None and len(str_value) > max_length:
        raise ValidationError(
            message=f'{field_name}长度不能超过 {max_length} 个字符',
            field=field_name,
            value=str_value
        )
    
    return str_value


def validate_request(required_params: List[str] = None, optional_params: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    验证请求参数（通用验证器）
    
    Args:
        required_params: 必需参数列表
        optional_params: 可选参数字典，格式为 {param_name: default_value}
    
    Returns:
        dict: 验证后的参数字典
    
    Raises:
        ValidationError: 当必需参数缺失时抛出
    
    Example:
        >>> params = validate_request(
        ...     required_params=['brand_name', 'year'],
        ...     optional_params={'page': 1, 'per_page': 20}
        ... )
    """
    # 获取请求数据（支持GET和POST）
    if request.method in ['POST', 'PUT', 'PATCH']:
        data = request.get_json() or {}
        # 同时检查form数据（用于文件上传等场景）
        if not data and request.form:
            data = dict(request.form)
    else:
        data = dict(request.args)
    
    validated_params = {}
    
    # 验证必需参数
    if required_params:
        missing_params = []
        for param in required_params:
            if param not in data or data[param] is None or data[param] == '':
                missing_params.append(param)
        
        if missing_params:
            raise ValidationError(
                message=f'缺少必需参数: {", ".join(missing_params)}',
                details={'missing_params': missing_params}
            )
        
        # 提取必需参数
        for param in required_params:
            validated_params[param] = data.get(param)
    
    # 处理可选参数
    if optional_params:
        for param, default_value in optional_params.items():
            validated_params[param] = data.get(param, default_value)
    
    return validated_params


def validate_request_decorator(required_params: List[str] = None, optional_params: Dict[str, Any] = None):
    """
    请求参数验证装饰器
    
    Args:
        required_params: 必需参数列表
        optional_params: 可选参数字典
    
    Returns:
        装饰器函数
    
    Example:
        >>> @validate_request_decorator(required_params=['brand_name'])
        >>> def get_brand(brand_name):
        ...     pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # 验证请求参数
                validated_params = validate_request(required_params, optional_params)
                # 将验证后的参数添加到kwargs中
                kwargs.update(validated_params)
                return f(*args, **kwargs)
            except ValidationError as e:
                # 返回验证错误响应
                return jsonify(e.to_dict()), e.status_code
        
        return decorated_function
    return decorator


def validate_filters(filters: Dict[str, Any] = None, allowed_filters: List[str] = None) -> Dict[str, Any]:
    """
    验证筛选参数
    
    Args:
        filters: 筛选参数字典（从请求参数获取，如果为None则从request.args获取）
        allowed_filters: 允许的筛选字段列表
    
    Returns:
        dict: 验证后的筛选参数字典
    
    Example:
        >>> filters = validate_filters(allowed_filters=['year', 'material', 'theme_series'])
    """
    if filters is None:
        filters = {}
        # 从请求参数获取筛选参数
        for key in ['year', 'material', 'theme', 'theme_series', 'print_size', 'state']:
            value = request.args.get(key)
            if value:
                filters[key] = value
    
    # 如果指定了允许的筛选字段，只保留允许的字段
    if allowed_filters:
        validated_filters = {}
        for key in allowed_filters:
            if key in filters:
                validated_filters[key] = filters[key]
        return validated_filters
    
    return filters


def validate_boolean(value: Any, field_name: str, default: bool = False) -> bool:
    """
    验证布尔值参数
    
    Args:
        value: 要验证的值
        field_name: 字段名称（用于错误消息）
        default: 默认值（当值为None或无效时使用）
    
    Returns:
        bool: 验证后的布尔值
    
    Example:
        >>> load_all = validate_boolean(request.args.get('load_all'), 'load_all', default=False)
    """
    if value is None:
        return default
    
    # 处理字符串形式的布尔值
    if isinstance(value, str):
        value_lower = value.lower().strip()
        if value_lower in ['true', '1', 'yes', 'on']:
            return True
        elif value_lower in ['false', '0', 'no', 'off', '']:
            return False
        else:
            logger.warning(f'无效的布尔值 {value} for {field_name}，使用默认值 {default}')
            return default
    
    # 处理数字形式的布尔值
    if isinstance(value, (int, float)):
        return bool(value)
    
    # 处理布尔值
    if isinstance(value, bool):
        return value
    
    # 其他情况使用默认值
    logger.warning(f'无法解析布尔值 {value} for {field_name}，使用默认值 {default}')
    return default


# 导出所有验证函数
__all__ = [
    'validate_pagination',
    'validate_search',
    'validate_brand_name',
    'validate_integer',
    'validate_string',
    'validate_request',
    'validate_request_decorator',
    'validate_filters',
    'validate_boolean'
]
