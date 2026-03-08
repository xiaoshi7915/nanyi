"""
异常处理中间件
统一处理应用异常，转换为HTTP响应
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.utils.logger import get_logger
from app.utils.exceptions import (
    BaseAppException,
    RateLimitError,
    ValidationError,
    TaskNotFoundError,
    StorageError,
    AIModelError,
    ImageProcessingError,
    TaskProcessingError,
    ConfigurationError
)

# 获取日志记录器
logger = get_logger(__name__)


async def app_exception_handler(request: Request, exc: BaseAppException) -> JSONResponse:
    """
    应用异常处理器（统一异常格式，包含上下文信息）
    
    Args:
        request: FastAPI请求对象
        exc: 应用异常
    
    Returns:
        JSON响应
    """
    # 根据异常类型确定HTTP状态码
    status_code_map = {
        ValidationError: status.HTTP_400_BAD_REQUEST,
        RateLimitError: status.HTTP_429_TOO_MANY_REQUESTS,
        TaskNotFoundError: status.HTTP_404_NOT_FOUND,
        StorageError: status.HTTP_503_SERVICE_UNAVAILABLE,  # 存储服务错误
        AIModelError: status.HTTP_503_SERVICE_UNAVAILABLE,  # AI模型服务错误
        ImageProcessingError: status.HTTP_422_UNPROCESSABLE_ENTITY,  # 图片处理错误
        TaskProcessingError: status.HTTP_500_INTERNAL_SERVER_ERROR,  # 任务处理错误
        ConfigurationError: status.HTTP_500_INTERNAL_SERVER_ERROR,  # 配置错误
    }
    
    status_code = status_code_map.get(type(exc), status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # 构建响应内容（统一格式）
    response_content = {
        "error_code": exc.error_code,
        "error_message": exc.message,
        "detail": exc.detail,
        "retryable": exc.retryable,
        "timestamp": exc.timestamp
    }
    
    # 在调试模式下，添加更多上下文信息
    from app.config import settings
    if settings.debug:
        response_content["context"] = exc.context
        response_content["traceback"] = exc.traceback
    
    # 记录异常日志（包含上下文信息）
    log_context = {
        "error_code": exc.error_code,
        "error_message": exc.message,
        "detail": exc.detail,
        "context": exc.context,
        "retryable": exc.retryable,
        "request_path": str(request.url.path),
        "request_method": request.method,
        "client_host": request.client.host if request.client else None
    }
    
    if status_code >= 500:
        # 服务器错误，记录为错误级别
        logger.error(f"应用异常: {exc.error_code} - {exc.message}", extra=log_context, exc_info=True)
    else:
        # 客户端错误，记录为警告级别
        logger.warning(f"应用异常: {exc.error_code} - {exc.message}", extra=log_context)
    
    return JSONResponse(
        status_code=status_code,
        content=response_content
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    请求验证异常处理器（统一异常格式）
    
    Args:
        request: FastAPI请求对象
        exc: 验证异常
    
    Returns:
        JSON响应
    """
    from datetime import datetime
    
    # 构建上下文信息
    context = {
        "request_path": str(request.url.path),
        "request_method": request.method,
        "client_host": request.client.host if request.client else None
    }
    
    # 记录验证失败日志
    logger.warning(
        f"请求验证失败: {exc.errors()}",
        extra={
            "error_code": "VALIDATION_ERROR",
            "context": context,
            "validation_errors": exc.errors()
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error_code": "VALIDATION_ERROR",
            "error_message": "请求参数验证失败",
            "detail": exc.errors(),
            "retryable": False,
            "timestamp": datetime.now().isoformat()
        }
    )

