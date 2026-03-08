"""
Mock AI模型实现
用于测试环境，避免调用真实的豆包API（节省免费额度）
"""
import io
import time
from typing import Dict, Any, Optional
from PIL import Image

from app.utils.logger import get_logger
from app.utils.exceptions import AIModelError, ValidationError
from app.services.ai_models.base import BaseAIModel, GenerateParams

# 获取日志记录器
logger = get_logger(__name__)


class MockAIModel(BaseAIModel):
    """
    Mock AI模型实现
    生成一个简单的测试图片，不调用真实API
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化Mock模型
        
        Args:
            config: 模型配置字典（可选）
        """
        if config is None:
            config = {
                "mock_delay": 2.0,  # 模拟API调用延迟（秒）
                "image_size": (512, 512),  # 生成的图片尺寸
            }
        super().__init__(config)
        self.mock_delay = self.config.get("mock_delay", 2.0)
        self.image_size = self.config.get("image_size", (512, 512))
        
        logger.info("Mock AI模型初始化完成（测试模式，不调用真实API）")
    
    def _validate_config(self) -> bool:
        """
        验证模型配置是否有效
        
        Returns:
            配置是否有效
        """
        logger.debug("Mock模型配置验证通过")
        return True
    
    async def validate_input(self, params: GenerateParams) -> bool:
        """
        验证输入参数
        
        Args:
            params: 生成参数
        
        Returns:
            参数是否有效
        
        Raises:
            ValidationError: 参数无效时抛出异常
        """
        # 验证布料图片
        if not params.fabric_images or len(params.fabric_images) == 0:
            raise ValidationError("至少需要提供一张布料/成衣图片")
        
        if len(params.fabric_images) > 5:
            raise ValidationError("最多支持5张布料/成衣图片")
        
        # 验证模特类型
        if params.model_type == "real":
            if not params.real_person_image:
                raise ValidationError("model_type为'real'时，必须提供real_person_image")
        
        logger.debug("Mock模型输入参数验证通过")
        return True
    
    async def generate(self, params: GenerateParams) -> bytes:
        """
        生成图片（Mock实现）
        生成一个简单的测试图片
        
        Args:
            params: 生成参数
        
        Returns:
            生成的图片二进制数据（PNG格式）
        
        Raises:
            AIModelError: 生成失败时抛出异常
        """
        try:
            logger.info(
                f"Mock模型开始生成图片: model_type={params.model_type}, "
                f"shot_type={params.shot_type}, aspect_ratio={params.aspect_ratio}"
            )
            
            # 验证输入
            await self.validate_input(params)
            
            # 模拟API调用延迟
            await self._simulate_api_delay()
            
            # 根据aspect_ratio计算图片尺寸
            width, height = self._parse_aspect_ratio(params.aspect_ratio)
            if params.resolution:
                width, height = self._parse_resolution(params.resolution)
            
            # 生成一个简单的测试图片
            image = self._generate_test_image(width, height, params)
            
            # 转换为字节数据
            img_bytes = io.BytesIO()
            image.save(img_bytes, format="PNG")
            img_bytes.seek(0)
            image_data = img_bytes.read()
            
            logger.info(
                f"Mock模型图片生成成功: size={len(image_data)} bytes, "
                f"dimensions={width}x{height}"
            )
            return image_data
            
        except (ValidationError, AIModelError):
            # 重新抛出业务异常
            raise
        except Exception as e:
            logger.error(f"Mock模型图片生成失败: {str(e)}", exc_info=True)
            raise AIModelError(f"图片生成失败: {str(e)}")
    
    async def _simulate_api_delay(self):
        """
        模拟API调用延迟
        """
        import asyncio
        await asyncio.sleep(self.mock_delay)
    
    def _generate_test_image(
        self,
        width: int,
        height: int,
        params: GenerateParams
    ) -> Image.Image:
        """
        生成测试图片
        
        Args:
            width: 图片宽度
            height: 图片高度
            params: 生成参数
        
        Returns:
            PIL Image对象
        """
        # 创建一个简单的测试图片
        # 根据参数生成不同颜色的图片
        if params.model_type == "ai":
            # AI模特：蓝色背景
            color = (100, 150, 255)
        else:
            # 真人模特：绿色背景
            color = (100, 255, 150)
        
        # 创建图片
        image = Image.new("RGB", (width, height), color=color)
        
        # 添加一些文字标识（可选）
        try:
            from PIL import ImageDraw, ImageFont
            draw = ImageDraw.Draw(image)
            
            # 添加文本标识
            text = f"Mock Image\n{params.shot_type}\n{params.aspect_ratio}"
            try:
                # 尝试使用默认字体
                font = ImageFont.load_default()
            except:
                font = None
            
            # 计算文本位置（居中）
            bbox = draw.textbbox((0, 0), text, font=font) if font else (0, 0, 100, 20)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            position = ((width - text_width) // 2, (height - text_height) // 2)
            
            # 绘制文本
            draw.text(position, text, fill=(255, 255, 255), font=font)
        except Exception as e:
            logger.warning(f"添加文本标识失败: {str(e)}")
        
        return image
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        Returns:
            模型信息字典
        """
        return {
            "name": "Mock AI Model",
            "version": "1.0.0",
            "provider": "mock",
            "model_name": "mock_model",
            "base_url": "mock://localhost",
            "supported_model_types": ["ai", "real"],
            "supported_shot_types": ["full_body", "half_body"],
            "supported_aspect_ratios": ["9:16", "16:9", "1:1"],
            "max_fabric_images": 5,
            "features": [
                "Mock模式（测试用）",
                "不调用真实API",
                "快速生成测试图片"
            ],
            "is_mock": True
        }

