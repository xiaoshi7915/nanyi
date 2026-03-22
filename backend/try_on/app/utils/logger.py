"""
日志工具模块
"""
import logging
import sys
from typing import Optional
from pythonjsonlogger import jsonlogger


# 全局日志配置
_logger: Optional[logging.Logger] = None


def setup_logger(
    name: str = "try_on",
    level: str = "INFO",
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    设置结构化日志记录器（增强版，包含性能指标）
    
    Args:
        name: 日志记录器名称
        level: 日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
        format_string: 自定义格式字符串（可选）
    
    Returns:
        配置好的日志记录器
    """
    global _logger
    
    # 如果已经设置过，直接返回
    if _logger is not None:
        return _logger
    
    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # 避免重复添加处理器
    if logger.handlers:
        return logger
    
    # 创建控制台处理器
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, level.upper()))
    
    # 设置JSON格式（增强版，包含更多上下文信息）
    if format_string is None:
        format_string = (
            "%(asctime)s %(name)s %(levelname)s %(message)s "
            "%(pathname)s %(lineno)d %(funcName)s"
        )
    
    formatter = jsonlogger.JsonFormatter(
        format_string,
        json_ensure_ascii=False  # 支持中文
    )
    handler.setFormatter(formatter)
    
    # 添加处理器到记录器
    logger.addHandler(handler)
    
    # 保存全局引用
    _logger = logger
    
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    获取日志记录器
    
    Args:
        name: 日志记录器名称（可选，默认使用全局记录器）
    
    Returns:
        日志记录器实例
    """
    if name:
        return logging.getLogger(name)
    
    # 如果全局记录器未设置，先设置它
    if _logger is None:
        return setup_logger()
    
    return _logger

