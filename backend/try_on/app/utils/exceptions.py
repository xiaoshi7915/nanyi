"""
统一异常处理模块
定义自定义异常类，提供统一的错误处理机制
"""
from typing import Optional, Dict, Any
import traceback
from datetime import datetime


class BaseAppException(Exception):
    """应用基础异常类"""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        detail: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
        retryable: bool = False
    ):
        """
        初始化异常
        
        Args:
            message: 错误消息
            error_code: 错误码（可选）
            detail: 错误详情（可选）
            context: 错误上下文信息（可选），用于记录错误发生时的上下文
            retryable: 是否可重试（可选）
        """
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.detail = detail or {}
        self.context = context or {}
        self.retryable = retryable
        self.timestamp = datetime.now().isoformat()
        self.traceback = traceback.format_exc()
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将异常转换为字典格式（用于日志和响应）
        
        Returns:
            异常字典
        """
        return {
            "error_code": self.error_code,
            "error_message": self.message,
            "detail": self.detail,
            "context": self.context,
            "retryable": self.retryable,
            "timestamp": self.timestamp
        }


class ValidationError(BaseAppException):
    """参数验证错误"""
    def __init__(self, message: str, detail: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, "VALIDATION_ERROR", detail, context, retryable=False)


class RateLimitError(BaseAppException):
    """限流错误"""
    def __init__(self, message: str, detail: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, "RATE_LIMIT_ERROR", detail, context, retryable=True)


class StorageError(BaseAppException):
    """存储服务错误"""
    def __init__(self, message: str, detail: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None, retryable: bool = True):
        super().__init__(message, "STORAGE_ERROR", detail, context, retryable=retryable)


class AIModelError(BaseAppException):
    """AI模型服务错误"""
    def __init__(self, message: str, detail: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None, retryable: bool = True):
        super().__init__(message, "AI_MODEL_ERROR", detail, context, retryable=retryable)


class ImageProcessingError(BaseAppException):
    """图片处理错误"""
    def __init__(self, message: str, detail: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None, retryable: bool = False):
        super().__init__(message, "IMAGE_PROCESSING_ERROR", detail, context, retryable=retryable)


class TaskNotFoundError(BaseAppException):
    """任务不存在错误"""
    def __init__(self, message: str, detail: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, "TASK_NOT_FOUND_ERROR", detail, context, retryable=False)


class TaskProcessingError(BaseAppException):
    """任务处理错误"""
    def __init__(self, message: str, detail: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None, retryable: bool = True):
        super().__init__(message, "TASK_PROCESSING_ERROR", detail, context, retryable=retryable)


class ConfigurationError(BaseAppException):
    """配置错误"""
    def __init__(self, message: str, detail: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, "CONFIGURATION_ERROR", detail, context, retryable=False)

