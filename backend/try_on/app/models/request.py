"""
请求模型定义
"""
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, ConfigDict


class TryOnRequest(BaseModel):
    """试衣生成请求模型"""
    
    # 解决 Pydantic 受保护命名空间冲突警告
    model_config = ConfigDict(protected_namespaces=())
    
    model_type: str = Field(..., description="模特类型：ai 或 real")
    shot_type: str = Field(..., description="拍摄类型：full_body 或 half_body")
    aspect_ratio: str = Field(..., description="图像比例：9:16, 16:9, 1:1")
    style: str = Field(default="portrait_photography", description="风格")
    resolution: Optional[str] = Field(None, description="分辨率，如 1024x1792")
    ai_model_id: Optional[str] = Field(None, description="AI模特ID（model_type=ai时可选）")
    model_provider: str = Field(default="seedream", description="模型提供商")
    prompt: Optional[str] = Field(None, description="自定义提示词（可选）")
    
    @field_validator("model_type")
    @classmethod
    def validate_model_type(cls, v: str) -> str:
        """验证模特类型"""
        if v not in ["ai", "real"]:
            raise ValueError("model_type必须是 'ai' 或 'real'")
        return v
    
    @field_validator("shot_type")
    @classmethod
    def validate_shot_type(cls, v: str) -> str:
        """验证拍摄类型"""
        if v not in ["full_body", "half_body"]:
            raise ValueError("shot_type必须是 'full_body' 或 'half_body'")
        return v
    
    @field_validator("aspect_ratio")
    @classmethod
    def validate_aspect_ratio(cls, v: str) -> str:
        """验证图像比例"""
        valid_ratios = ["9:16", "16:9", "1:1"]
        if v not in valid_ratios:
            raise ValueError(f"aspect_ratio必须是 {valid_ratios} 之一")
        return v
    
    @field_validator("resolution")
    @classmethod
    def validate_resolution(cls, v: Optional[str]) -> Optional[str]:
        """验证分辨率格式"""
        if v is None:
            return v
        import re
        if not re.match(r'^\d+x\d+$', v):
            raise ValueError("resolution格式错误，应为 '宽x高'，如 '1024x1792'")
        return v

