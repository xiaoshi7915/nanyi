"""
Seedream 4.5模型服务实现
基于火山引擎方舟官方SDK
"""
import base64
import io
from typing import Dict, Any, Optional
import httpx
from PIL import Image
from volcenginesdkarkruntime import Ark

from app.config import settings
from app.utils.logger import get_logger
from app.utils.exceptions import AIModelError, ValidationError
from app.services.ai_models.base import BaseAIModel, GenerateParams
from app.services.prompt_service import prompt_service

# 获取日志记录器
logger = get_logger(__name__)


class SeedreamModel(BaseAIModel):
    """
    Seedream 4.5模型实现
    使用火山引擎方舟官方SDK
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化Seedream模型
        
        Args:
            config: 模型配置字典（可选，默认使用settings中的配置）
        """
        if config is None:
            config = {
                "api_key": settings.ark_api_key,
                "base_url": settings.ark_base_url,
                "model_name": settings.ark_model_name,
                "timeout": 300,  # 5分钟超时
                "max_retries": 3,  # 最大重试次数
            }
        super().__init__(config)
        self.api_key = self.config["api_key"]
        self.base_url = self.config["base_url"]
        self.model_name = self.config["model_name"]
        self.timeout = self.config.get("timeout", 300)
        self.max_retries = self.config.get("max_retries", 3)
        
        # 初始化火山引擎客户端
        self._init_client()
    
    def _init_client(self) -> None:
        """初始化火山引擎客户端"""
        try:
            self.client = Ark(
                base_url=self.base_url,
                api_key=self.api_key
            )
            logger.info("火山引擎客户端初始化成功")
        except Exception as e:
            logger.error(f"火山引擎客户端初始化失败: {str(e)}", exc_info=True)
            raise AIModelError(f"初始化AI模型客户端失败: {str(e)}")
    
    def _validate_config(self) -> bool:
        """
        验证模型配置是否有效
        
        Returns:
            配置是否有效
        
        Raises:
            ValidationError: 配置无效时抛出异常
        """
        if not self.config.get("api_key"):
            raise ValidationError("火山引擎API密钥未配置")
        if not self.config.get("base_url"):
            raise ValidationError("火山引擎API地址未配置")
        if not self.config.get("model_name"):
            raise ValidationError("模型名称未配置")
        logger.info("Seedream模型配置验证通过")
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
        
        # 验证图片格式
        for img_data in params.fabric_images:
            try:
                Image.open(io.BytesIO(img_data))
            except Exception as e:
                raise ValidationError(f"无效的图片数据: {str(e)}")
        
        if params.real_person_image:
            try:
                Image.open(io.BytesIO(params.real_person_image))
            except Exception as e:
                raise ValidationError(f"无效的真人照片数据: {str(e)}")
        
        logger.debug("输入参数验证通过")
        return True
    
    def _encode_image(self, image_data: bytes) -> str:
        """
        将图片编码为base64字符串
        
        Args:
            image_data: 图片二进制数据
        
        Returns:
            base64编码的字符串（带data URI前缀）
        """
        # 检测图片格式
        try:
            img = Image.open(io.BytesIO(image_data))
            format_map = {
                "JPEG": "image/jpeg",
                "PNG": "image/png",
                "WEBP": "image/webp"
            }
            mime_type = format_map.get(img.format, "image/jpeg")
        except:
            mime_type = "image/jpeg"
        
        base64_str = base64.b64encode(image_data).decode("utf-8")
        return f"data:{mime_type};base64,{base64_str}"
    
    def _build_prompt(self, params: GenerateParams) -> str:
        """
        构建提示词（使用提示词服务）
        
        Args:
            params: 生成参数
        
        Returns:
            构建的提示词
        """
        return prompt_service.build_prompt(params)
    
    def _parse_size(self, aspect_ratio: str, resolution: Optional[str] = None) -> str:
        """
        解析图像尺寸参数
        
        Args:
            aspect_ratio: 图像比例
            resolution: 分辨率（可选）
        
        Returns:
            尺寸字符串（如 "2K", "1024x1792"）
        """
        # 如果提供了分辨率，直接使用
        if resolution:
            return resolution
        
        # 根据比例返回默认尺寸
        # 火山引擎支持 "1K", "2K" 等预设尺寸
        size_map = {
            "9:16": "2K",  # 竖屏，适合手机
            "16:9": "2K",  # 横屏
            "1:1": "1K",   # 正方形
        }
        
        return size_map.get(aspect_ratio, "2K")
    
    async def _download_image_with_retry(
        self,
        image_url: str,
        api_retry_count: int = 0,
        download_retry_count: int = 0
    ) -> bytes:
        """
        下载图片（带重试机制）
        
        Args:
            image_url: 图片URL
            api_retry_count: API调用重试次数（用于日志上下文）
            download_retry_count: 下载重试次数
        
        Returns:
            图片二进制数据
        
        Raises:
            AIModelError: 下载失败时抛出异常
        """
        max_download_retries = self.max_retries  # 使用相同的最大重试次数
        
        try:
            # 下载图片
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                download_response = await client.get(image_url)
                
                if download_response.status_code != 200:
                    raise AIModelError(f"下载图片失败，状态码: {download_response.status_code}")
                
                image_data = download_response.content
                
                # 验证下载的数据不为空
                if not image_data or len(image_data) == 0:
                    raise AIModelError("下载的图片数据为空")
                
                return image_data
        
        except (httpx.TimeoutException, httpx.RequestError, httpx.HTTPStatusError) as e:
            # 网络错误或HTTP错误，可以重试
            if download_retry_count < max_download_retries:
                wait_time = min(2 ** download_retry_count, 60)  # 指数退避，最多60秒
                logger.warning(
                    f"图片下载失败，将重试: url={image_url}, "
                    f"error={str(e)}, download_retry={download_retry_count + 1}/{max_download_retries}, "
                    f"wait_time={wait_time}s"
                )
                import asyncio
                await asyncio.sleep(wait_time)
                return await self._download_image_with_retry(
                    image_url, 
                    api_retry_count, 
                    download_retry_count + 1
                )
            else:
                logger.error(
                    f"图片下载失败，已达到最大重试次数: url={image_url}, "
                    f"error={str(e)}, max_retries={max_download_retries}"
                )
                raise AIModelError(f"下载图片失败（已重试{max_download_retries}次）: {str(e)}")
        
        except Exception as e:
            # 其他错误，直接抛出
            logger.error(f"图片下载异常: url={image_url}, error={str(e)}", exc_info=True)
            raise AIModelError(f"下载图片失败: {str(e)}")
    
    async def _call_api(
        self,
        prompt: str,
        size: str = "2K",
        image: Optional[str | list[str]] = None,
        retry_count: int = 0
    ) -> bytes:
        """
        调用火山引擎API生成图片（支持图生图和多图输入）
        
        Args:
            prompt: 提示词
            size: 图片尺寸
            image: 输入的参考图片（base64编码的data URI格式，可以是单个字符串或字符串列表，可选）
            retry_count: 当前重试次数
        
        Returns:
            生成的图片二进制数据
        
        Raises:
            AIModelError: API调用失败时抛出异常
        """
        try:
            logger.info(f"调用火山引擎API生成图片 (重试次数: {retry_count})")
            has_images = image is not None
            image_count = len(image) if isinstance(image, list) else (1 if image else 0)
            logger.debug(f"提示词: {prompt}, 尺寸: {size}, 输入图片数量: {image_count}")
            
            # 构建请求参数
            request_params = {
                "model": self.model_name,
                "prompt": prompt,
                "size": size,
                "response_format": "url",  # 返回URL，然后下载
                "watermark": False
            }
            
            # 如果有输入图片，添加到请求参数中（图生图模式，支持多图）
            if image:
                request_params["image"] = image
                if isinstance(image, list):
                    logger.info(f"✓ 使用多图输入模式，已添加 {len(image)} 张输入图片到API请求")
                else:
                    logger.info(f"✓ 使用单图输入模式，已添加输入图片到API请求，图片base64长度: {len(image)} 字符")
            else:
                logger.warning("⚠️ 警告：没有输入图片，将使用文生图模式")
            
            # 调用API
            resp = self.client.images.generate(**request_params)
            
            # 检查响应
            if not resp or not resp.data or len(resp.data) == 0:
                raise AIModelError("API返回空响应")
            
            # 获取图片URL
            image_url = resp.data[0].url
            if not image_url:
                raise AIModelError("API响应中未找到图片URL")
            
            logger.info(f"获取到图片URL: {image_url}")
            
            # 下载图片（带重试机制）
            image_data = await self._download_image_with_retry(image_url, retry_count)
            logger.info("图片下载成功")
            return image_data
        
        except httpx.TimeoutException:
            if retry_count < self.max_retries:
                logger.warning(f"API调用超时，重试 (重试 {retry_count + 1}/{self.max_retries})")
                import asyncio
                await asyncio.sleep(2 ** retry_count)  # 指数退避
                return await self._call_api(prompt, size, image, retry_count + 1)
            else:
                raise AIModelError("API调用超时，已达到最大重试次数")
        
        except Exception as e:
            # 如果是可重试的错误，进行重试
            if retry_count < self.max_retries and isinstance(e, (httpx.HTTPStatusError, httpx.RequestError)):
                logger.warning(f"API调用错误，重试 (重试 {retry_count + 1}/{self.max_retries}): {str(e)}")
                import asyncio
                await asyncio.sleep(2 ** retry_count)
                return await self._call_api(prompt, size, image, retry_count + 1)
            else:
                logger.error(f"火山引擎API调用异常: {str(e)}", exc_info=True)
                raise AIModelError(f"AI模型调用失败: {str(e)}")
    
    async def generate(self, params: GenerateParams) -> bytes:
        """
        生成图片
        
        Args:
            params: 生成参数
        
        Returns:
            生成的图片二进制数据
        
        Raises:
            AIModelError: 生成失败时抛出异常
        """
        try:
            # 验证输入
            await self.validate_input(params)
            
            # 构建提示词
            prompt = self._build_prompt(params)
            
            # 解析尺寸
            size = self._parse_size(params.aspect_ratio, params.resolution)
            
            # 准备输入图片
            # 简化逻辑：
            # 1. AI模式：只使用第一张成衣图，单图输入，生成全身AI女模特穿成衣图
            # 2. 真人模式：使用真人图+第一张成衣图，2图输入，生成全身真人穿成衣图
            input_image = None
            if params.model_type == "real" and params.real_person_image:
                # 真人图模式：使用真人图+第一张成衣图作为2图输入
                # 第一张：真人图（作为主体）
                # 第二张：成衣图（作为参考）
                if not params.fabric_images or len(params.fabric_images) == 0:
                    raise ValidationError("真人图模式需要至少一张成衣图")
                
                image_list = []
                # 第一张：真人图
                real_person_encoded = self._encode_image(params.real_person_image)
                image_list.append(real_person_encoded)
                logger.info(f"真人图模式：添加真人图，图片大小: {len(params.real_person_image)} bytes")
                
                # 第二张：第一张成衣图
                fabric_image_data = params.fabric_images[0]
                fabric_encoded = self._encode_image(fabric_image_data)
                image_list.append(fabric_encoded)
                logger.info(f"真人图模式：添加成衣图，图片大小: {len(fabric_image_data)} bytes")
                
                input_image = image_list
                logger.info(f"真人图模式：使用2图输入（真人图+成衣图）")
                
            elif params.fabric_images and len(params.fabric_images) > 0:
                # AI模式：只使用第一张成衣图，单图输入
                fabric_image_data = params.fabric_images[0]
                input_image = self._encode_image(fabric_image_data)
                logger.info(f"AI模式：使用单张成衣图进行图生图，图片大小: {len(fabric_image_data)} bytes")
                logger.info(f"AI模式：成衣图已编码为base64，长度: {len(input_image)} 字符")
                # 验证图片数据不为空
                if not fabric_image_data or len(fabric_image_data) == 0:
                    raise ValidationError("成衣图数据为空")
                if not input_image or len(input_image) == 0:
                    raise ValidationError("成衣图编码失败")
            
            # 调用API生成图片（图生图模式，支持多图输入）
            # 提示词中已包含成衣描述，AI会根据提示词和多图输入理解要穿哪件衣服
            image_data = await self._call_api(
                prompt=prompt,
                size=size,
                image=input_image
            )
            
            logger.info("图片生成成功")
            return image_data
        
        except (ValidationError, AIModelError):
            # 重新抛出业务异常
            raise
        except Exception as e:
            logger.error(f"图片生成失败: {str(e)}", exc_info=True)
            raise AIModelError(f"图片生成失败: {str(e)}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        Returns:
            模型信息字典
        """
        return {
            "name": "Seedream",
            "version": "4.5",
            "provider": "volcengine_ark",
            "model_name": self.model_name,
            "base_url": self.base_url,
            "supported_model_types": ["ai", "real"],
            "supported_shot_types": ["full_body", "half_body"],
            "supported_aspect_ratios": ["9:16", "16:9", "1:1"],
            "max_fabric_images": 5,
            "features": [
                "图生图",
                "AI模特",
                "真人模特",
                "全身/半身照",
                "自定义比例",
                "自定义分辨率"
            ]
        }
