"""
试衣服务API端点
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Request
from typing import List, Optional

from app.models.request import TryOnRequest
from app.models.response import TryOnResponse, TaskStatusResponse, ErrorResponse
from app.utils.logger import get_logger
from app.utils.validators import validate_all_images
from app.utils.exceptions import (
    BaseAppException,
    ValidationError,
    RateLimitError,
    TaskNotFoundError,
    ImageProcessingError
)
from app.config import settings
from app.services.rate_limit_service import rate_limit_service
from app.services.image_service import image_service

# 创建路由
router = APIRouter()

# 获取日志记录器
logger = get_logger(__name__)


def get_client_ip(request: Request) -> str:
    """
    获取客户端IP地址
    
    Args:
        request: FastAPI请求对象
    
    Returns:
        客户端IP地址
    """
    # 优先从X-Forwarded-For获取（代理服务器场景）
    if "x-forwarded-for" in request.headers:
        ip = request.headers["x-forwarded-for"].split(",")[0].strip()
        return ip
    # 从X-Real-IP获取
    if "x-real-ip" in request.headers:
        return request.headers["x-real-ip"]
    # 从客户端获取
    if request.client:
        return request.client.host
    return "unknown"


@router.post(
    "/try-on/generate",
    response_model=TryOnResponse,
    summary="生成试衣效果图",
    description="上传布料/成衣图片，生成AI模特或真人试衣效果"
)
async def generate_try_on(
    request: Request,
    fabric_images: List[UploadFile] = File(..., description="布料/成衣图片（1-5张）"),
    model_type: str = Form(..., description="模特类型：ai 或 real"),
    shot_type: str = Form(..., description="拍摄类型：full_body 或 half_body"),
    aspect_ratio: str = Form(..., description="图像比例：9:16, 16:9, 1:1"),
    style: str = Form(default="portrait_photography", description="风格"),
    resolution: Optional[str] = Form(None, description="分辨率，如 1024x1792"),
    ai_model_id: Optional[str] = Form(None, description="AI模特ID"),
    real_person_image: Optional[UploadFile] = File(None, description="真人照片"),
    model_provider: str = Form(default="seedream", description="模型提供商"),
    prompt: Optional[str] = Form(None, description="自定义提示词（可选）")
):
    """
    生成试衣效果图
    
    - **fabric_images**: 布料/成衣图片（1-5张）
    - **model_type**: 模特类型（ai 或 real）
    - **shot_type**: 拍摄类型（full_body 或 half_body）
    - **aspect_ratio**: 图像比例（9:16, 16:9, 1:1）
    - **style**: 风格（默认：portrait_photography）
    - **resolution**: 分辨率（可选，如 1024x1792）
    - **ai_model_id**: AI模特ID（可选）
    - **real_person_image**: 真人照片（model_type=real时必填）
    - **model_provider**: 模型提供商（默认：seedream）
    - **prompt**: 自定义提示词（可选，会添加到系统提示词中）
    """
    try:
        # 获取客户端IP并检查限流
        client_ip = get_client_ip(request)
        allowed, error_msg = await rate_limit_service.check_rate_limit(client_ip=client_ip)
        if not allowed:
            logger.warning(f"限流拒绝请求: IP={client_ip}")
            raise RateLimitError(error_msg or "请求过于频繁，请稍后再试")
        
        # 验证请求参数
        try:
            request_data = TryOnRequest(
                model_type=model_type,
                shot_type=shot_type,
                aspect_ratio=aspect_ratio,
                style=style,
                resolution=resolution,
                ai_model_id=ai_model_id,
                model_provider=model_provider,
                prompt=prompt
            )
        except Exception as e:
            # Pydantic 验证错误转换为 ValidationError
            from pydantic import ValidationError as PydanticValidationError
            if isinstance(e, PydanticValidationError):
                error_messages = []
                for error in e.errors():
                    field = ".".join(str(loc) for loc in error.get("loc", []))
                    msg = error.get("msg", "验证失败")
                    error_messages.append(f"{field}: {msg}")
                raise ValidationError(f"请求参数验证失败: {', '.join(error_messages)}")
            # 其他异常继续抛出
            raise
        
        # 验证图片数量
        if len(fabric_images) < 1:
            raise ValidationError("至少需要上传1张布料/成衣图片")
        
        if len(fabric_images) > settings.max_images_per_request:
            raise ValidationError(f"最多只能上传{settings.max_images_per_request}张图片")
        
        # 验证真人照片（如果model_type为real）
        if model_type == "real" and real_person_image is None:
            raise ValidationError("model_type为'real'时，必须上传real_person_image")
        
        # 验证所有图片
        await validate_all_images(fabric_images, max_size_mb=settings.max_image_size_mb)
        if real_person_image:
            await validate_all_images([real_person_image], max_size_mb=settings.max_image_size_mb)
        
        # 调用图片处理服务创建任务
        task_id = await image_service.create_task(
            fabric_images=fabric_images,
            model_type=model_type,
            shot_type=shot_type,
            aspect_ratio=aspect_ratio,
            style=style,
            resolution=resolution,
            ai_model_id=ai_model_id,
            real_person_image=real_person_image,
            model_provider=model_provider,
            prompt=prompt
        )
        
        logger.info(f"创建试衣生成任务成功: task_id={task_id}, model_type={model_type}, shot_type={shot_type}, IP={client_ip}")
        
        # 返回任务信息
        return TryOnResponse(
            task_id=task_id,
            status="processing"
        )
        
    except (RateLimitError, ValidationError, ImageProcessingError):
        # 业务异常，直接抛出，由异常处理器处理
        raise
    except Exception as e:
        logger.error(f"生成试衣效果图失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器内部错误"
        )


@router.get(
    "/try-on/status/{task_id}",
    response_model=TaskStatusResponse,
    summary="查询任务状态",
    description="通过任务ID查询试衣生成任务的状态和结果"
)
async def get_task_status(request: Request, task_id: str):
    """
    查询任务状态
    
    - **task_id**: 任务ID
    """
    try:
        # 获取客户端IP并检查限流（查询接口也需要限流）
        client_ip = get_client_ip(request)
        allowed, error_msg = await rate_limit_service.check_rate_limit(client_ip=client_ip)
        if not allowed:
            logger.warning(f"限流拒绝查询请求: IP={client_ip}, task_id={task_id}")
            raise RateLimitError(error_msg or "请求过于频繁，请稍后再试")
        
        logger.info(f"查询任务状态: task_id={task_id}, IP={client_ip}")
        
        # 从图片处理服务获取任务状态
        task_status = image_service.get_task_status(task_id)
        
        # 返回任务状态
        return TaskStatusResponse(**task_status)
        
    except (RateLimitError, TaskNotFoundError, ValidationError):
        # 业务异常，转换为HTTP异常
        raise
    except Exception as e:
        logger.error(f"查询任务状态失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器内部错误"
        )

