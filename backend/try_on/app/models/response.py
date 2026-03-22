"""
响应模型定义
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class TryOnResponse(BaseModel):
    """试衣生成响应模型"""
    
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态：processing 或 completed")
    result_image_url: Optional[str] = Field(None, description="生成图片OSS URL")
    local_path: Optional[str] = Field(None, description="本地存储路径")


class TaskStatusResponse(BaseModel):
    """任务状态查询响应模型"""
    
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态：processing, completed, failed")
    result_image_url: Optional[str] = Field(None, description="生成图片OSS URL")
    local_path: Optional[str] = Field(None, description="本地存储路径")
    error_message: Optional[str] = Field(None, description="错误信息")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class ErrorResponse(BaseModel):
    """错误响应模型"""
    
    error_code: str = Field(..., description="错误码")
    error_message: str = Field(..., description="错误信息")
    detail: Optional[dict] = Field(None, description="错误详情")

