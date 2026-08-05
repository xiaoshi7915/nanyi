#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Seedream 4.5模型服务实现（适配版）
基于火山引擎方舟官方SDK，使用主项目的配置
"""
import base64
import os
import io
from typing import Dict, Any, Optional
import httpx
from PIL import Image
from volcenginesdkarkruntime import Ark

from backend.config.config import Config
from backend.utils.logger import logger

# 导入异常类
try:
    from backend.exceptions import ValidationError, ServiceError as AIModelError
except ImportError:
    # 如果主项目没有这些异常，创建简单的异常类
    class ValidationError(Exception):
        """参数验证错误"""
        pass
    
    class AIModelError(Exception):
        """AI模型服务错误"""
        pass

# 导入 GenerateParams（从 try_on 服务复制或创建）
# 为了简化，我们直接在这里定义 GenerateParams
from pydantic import BaseModel, ConfigDict
from typing import List


class GenerateParams(BaseModel):
    """
    生成参数模型
    统一不同模型的参数格式
    """
    # 解决 Pydantic 受保护命名空间冲突警告
    model_config = ConfigDict(protected_namespaces=())
    
    # 基础参数
    fabric_images: List[bytes]  # 布料/成衣图片数据
    model_type: str  # 模特类型：ai 或 real
    shot_type: str  # 拍摄类型：full_body 或 half_body
    aspect_ratio: str  # 图像比例：9:16, 16:9, 1:1
    style: str = "portrait_photography"  # 风格
    
    # 可选参数
    real_person_image: Optional[bytes] = None  # 真人照片（model_type=real时必填）
    ai_model_id: Optional[str] = None  # AI模特ID（model_type=ai时可选）
    resolution: Optional[str] = None  # 分辨率，如 1024x1792
    prompt: Optional[str] = None  # 自定义提示词
    seed: Optional[int] = None  # 随机种子
    steps: Optional[int] = None  # 生成步数
    guidance_scale: Optional[float] = None  # 引导强度
    
    # 扩展参数（用于模型特定的配置）
    extra_params: Dict[str, Any] = {}


class TryOnPromptService:
    """
    提示词管理服务类（内联版本）
    负责根据参数构建合适的提示词
    """
    
    # 风格模板字典
    STYLE_TEMPLATES = {
        "portrait_photography": "专业人像摄影，高质量，影棚灯光",
        "fashion": "时尚摄影，编辑风格，高级时装",
        "casual": "休闲生活摄影，自然光线",
        "studio": "影棚摄影，专业灯光设置",
        "outdoor": "户外摄影，自然日光",
        "street": "街头风格摄影，城市背景",
    }
    
    # 拍摄类型描述
    SHOT_TYPE_DESCRIPTIONS = {
        "full_body": "全身照，完整身材可见",
        "half_body": "半身照，上半身可见",
    }
    
    # 模特类型描述
    MODEL_TYPE_DESCRIPTIONS = {
        "ai": "AI生成模特",
        "real": "真人模特",
    }
    
    @staticmethod
    def build_prompt(
        params: GenerateParams,
        custom_style: Optional[str] = None
    ) -> str:
        """
        构建提示词
        
        Args:
            params: 生成参数
            custom_style: 自定义风格（可选，会覆盖params.style）
        
        Returns:
            构建的提示词字符串
        """
        prompt_parts = []

        # 如果调用方已提供“整段固定中文提示词”，则直接使用该 prompt 作为最终输出，
        # 避免与当前模板拼接导致提示词不一致。
        if params.prompt and params.prompt.strip():
            logger.debug("检测到自定义固定prompt：直接返回该prompt（跳过模板拼接）")
            return params.prompt.strip()
        
        # AI模式：优先添加图片和服装相关的描述（放在最前面，最重要）
        if params.model_type == "ai" and params.fabric_images:
            # 最优先：强调关键要素（女模特、旗袍、全身、9:16、样式匹配）
            prompt_parts.append("关键：生成9:16比例的全身照，女模特穿着旗袍")
            prompt_parts.append("旗袍的图案、颜色和设计必须与输入的成衣图完全匹配")
            prompt_parts.append("全身照，完整旗袍，从头到脚完整身体，9:16竖屏人像")
            
            # 强调使用输入图片中的成衣样式
            prompt_parts.append("重要：使用输入图片中的旗袍，女模特必须穿着参考图片中展示的完全相同旗袍")
            prompt_parts.append("输入图片包含旗袍，将这件旗袍的图案、颜色和设计应用到女模特身上")
            prompt_parts.append("完全复制输入图片中旗袍的图案、颜色、设计和风格")
            prompt_parts.append("旗袍风格必须与输入成衣图完美匹配")
            
            # 关键：只生成模特效果图，不要展示输入图片
            prompt_parts.append("只生成女模特穿着旗袍的最终效果图，不要包含参考布料图在输出中")
            prompt_parts.append("不要显示输入布料图，不要将图片分割成布料和模特两部分")
            prompt_parts.append("生成单一完整的女模特穿着旗袍图片，无布料参考，无前后对比")
            
            # 强调真实女模特，排除机器人
            prompt_parts.append("真实人类女模特，照片级真实女性，真人，女性身材")
            prompt_parts.append("不是机器人，不是AI机器人，不是机械，不是人工，不是合成，不是男性")
            
            # 服装完整性：完整旗袍
            prompt_parts.append("完整旗袍，全长旗袍，一件式服装，中国传统旗袍")
            prompt_parts.append("不是分离的上衣和裤子，不是两件套，不是现代连衣裙")
            prompt_parts.append("全身覆盖，全长连衣裙，完整旗袍")
            
            logger.debug("AI模式：已优先添加关键要素（女模特、旗袍、全身、9:16、样式匹配）")
        
        # 添加风格
        style = custom_style or params.style or "portrait_photography"
        if style in TryOnPromptService.STYLE_TEMPLATES:
            prompt_parts.append(TryOnPromptService.STYLE_TEMPLATES[style])
        else:
            # 如果风格不在模板中，直接使用
            prompt_parts.append(style)
        
        # 添加拍摄类型
        # 如果model_type为real，强制使用full_body生成全身照效果
        effective_shot_type = params.shot_type
        if params.model_type == "real":
            effective_shot_type = "full_body"
            logger.debug(f"真人图模式：强制使用full_body生成全身照效果（用户传入shot_type={params.shot_type}）")
            # 为真人图模式添加更明确的全身照描述
            prompt_parts.append("全身照，完整身材可见，从头到脚完整身体")
        else:
            # AI模式：强制使用full_body生成全身照，并强调9:16比例
            if params.model_type == "ai":
                prompt_parts.append("全身照，完整身材可见，从头到脚完整身体")
                prompt_parts.append("9:16比例，竖屏人像，全长旗袍")
                logger.debug("AI模式：强制使用full_body和9:16比例")
            elif effective_shot_type in TryOnPromptService.SHOT_TYPE_DESCRIPTIONS:
                prompt_parts.append(TryOnPromptService.SHOT_TYPE_DESCRIPTIONS[effective_shot_type])
        
        # 添加模特类型描述（如果AI模式还没有添加）
        if params.model_type == "ai" and not params.fabric_images:
            # AI模式但没有成衣图的情况（理论上不应该发生）
            prompt_parts.append("真实女模特，照片级真实女性，人类")
            prompt_parts.append("不是机器人，不是AI机器人，不是机械")
            logger.debug("AI模式：已添加真实女模特描述（避免生成机器人）")
        elif params.model_type == "real":
            prompt_parts.append(TryOnPromptService.MODEL_TYPE_DESCRIPTIONS[params.model_type])
        
        # 添加成衣相关的描述（真人模式或AI模式的补充）
        if params.fabric_images:
            if params.model_type == "real":
                # 真人图模式：使用更明确和强调性的描述，确保AI理解要穿上成衣图中的旗袍
                # 2图输入：第一张是真人图，第二张是成衣图
                prompt_parts.append("虚拟试衣效果，人物穿着第二张图片中的旗袍")
                prompt_parts.append("将成衣图片中的旗袍应用到第一张图片中的人物身上")
                prompt_parts.append("完整旗袍，全长旗袍，不是分离的上衣和裤子")
                prompt_parts.append("中国传统旗袍，一件式服装，全身覆盖")
                prompt_parts.append("服装匹配，成衣转移，试衣模拟，穿着完全相同的旗袍")
                logger.debug("真人图模式：已添加详细的旗袍描述到提示词（2图输入：真人图+成衣图，生成完整旗袍）")
            elif params.model_type == "ai":
                # AI模式：补充描述（主要描述已在前面添加）
                prompt_parts.append("服装匹配，成衣转移，试衣效果，穿着完全相同的成衣")
                logger.debug("AI模式：已添加补充的试衣效果描述")
        
        # 添加质量描述
        prompt_parts.append("高质量，细节丰富，清晰对焦")
        
        # 组合提示词
        prompt = ", ".join(prompt_parts)
        
        logger.debug(f"构建提示词: {prompt}")
        return prompt


class TryOnSeedreamModel:
    """
    Seedream 4.5模型实现（适配版）
    使用火山引擎方舟官方SDK，使用主项目的配置
    """
    
    def __init__(self, config: Config):
        """
        初始化Seedream模型
        
        Args:
            config: 主项目的配置对象
        """
        self.config = config
        self.api_key = config.ARK_API_KEY
        self.base_url = config.ARK_BASE_URL
        self.model_name = config.ARK_MODEL_NAME
        self.timeout = config.TASK_TIMEOUT_SECONDS
        self.max_retries = config.TASK_MAX_RETRIES
        
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
        if not self.api_key:
            raise ValidationError("火山引擎API密钥未配置")
        if not self.base_url:
            raise ValidationError("火山引擎API地址未配置")
        if not self.model_name:
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
        return TryOnPromptService.build_prompt(params)
    
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

            # 对齐你提供的 Ark 示例：显式关闭 sequential_image_generation，确保一次生成单张图
            sequential_image_generation = "disabled"
            # 是否加水印：默认保持当前行为不加水印，可通过环境变量切换
            # 兼容 "true/false/1/0" 等常见写法
            try_on_watermark_raw = os.getenv("TRY_ON_WATERMARK", "false").strip().lower()
            try_on_watermark = try_on_watermark_raw in {"1", "true", "yes", "y", "on"}
            
            # 构建请求参数
            request_params = {
                "model": self.model_name,
                "prompt": prompt,
                "size": size,
                "response_format": "url",  # 返回URL，然后下载
                "sequential_image_generation": sequential_image_generation,
                "watermark": try_on_watermark
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
                error_text = str(e)
                # Ark 典型错误：InvalidParameter.OversizeImage（输入图片超过 10MiB）
                if "InvalidParameter.OversizeImage" in error_text or "exceeds the limit (10 MiB)" in error_text:
                    raise AIModelError("上传图片过大（Ark 单张输入上限 10MB），请压缩后重试")
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


class TryOnMockAIModel:
    """
    主站 Mock AI（USE_MOCK_AI=true）。
    逻辑对齐 backend/try_on/app/services/ai_models/mock.py，但使用本模块
    GenerateParams / 异常，避免依赖遗留 try_on 包内的 app.* 导入路径。
    """

    def __init__(self, config: Optional[Config] = None):
        self.config = config
        self.mock_delay = float(os.getenv("MOCK_AI_DELAY_SECONDS", "0.5"))
        logger.info(
            "TryOnMockAIModel 初始化完成（测试模式，delay=%.2fs）", self.mock_delay
        )

    async def validate_input(self, params: GenerateParams) -> bool:
        if not params.fabric_images:
            raise ValidationError("至少需要提供一张布料/成衣图片")
        if len(params.fabric_images) > 5:
            raise ValidationError("最多支持5张布料/成衣图片")
        if params.model_type == "real" and not params.real_person_image:
            raise ValidationError("model_type为'real'时，必须提供real_person_image")
        return True

    async def generate(self, params: GenerateParams) -> bytes:
        """生成纯色占位图（JPEG），不调用真实 API。"""
        import asyncio

        try:
            await self.validate_input(params)
            if self.mock_delay > 0:
                await asyncio.sleep(self.mock_delay)

            width, height = 576, 1024
            if params.aspect_ratio == "16:9":
                width, height = 1024, 576
            elif params.aspect_ratio == "1:1":
                width, height = 768, 768
            if params.resolution and "x" in params.resolution:
                try:
                    parts = params.resolution.lower().split("x")
                    width, height = int(parts[0]), int(parts[1])
                except (ValueError, IndexError):
                    pass

            color = (100, 150, 255) if params.model_type == "ai" else (100, 200, 140)
            image = Image.new("RGB", (width, height), color=color)
            try:
                from PIL import ImageDraw, ImageFont

                draw = ImageDraw.Draw(image)
                text = f"Mock Try-On\n{params.shot_type}\n{params.aspect_ratio}"
                font = ImageFont.load_default()
                draw.multiline_text((24, 24), text, fill=(255, 255, 255), font=font)
            except Exception:
                pass

            buf = io.BytesIO()
            image.save(buf, format="JPEG", quality=85)
            data = buf.getvalue()
            logger.info(
                "Mock 图片生成成功: size=%s bytes, %sx%s", len(data), width, height
            )
            return data
        except ValidationError:
            raise
        except Exception as e:
            logger.error("Mock 图片生成失败: %s", e, exc_info=True)
            raise AIModelError(f"Mock 图片生成失败: {str(e)}")

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "name": "Mock AI Model",
            "version": "1.0.0",
            "provider": "mock",
            "is_mock": True,
            "supported_model_types": ["ai", "real"],
            "supported_shot_types": ["full_body", "half_body"],
            "supported_aspect_ratios": ["9:16", "16:9", "1:1"],
        }
