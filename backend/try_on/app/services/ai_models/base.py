"""
AI模型抽象基类
定义统一的模型接口，便于后续扩展其他模型
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict


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


class BaseAIModel(ABC):
    """
    AI模型抽象基类
    所有AI模型实现都应该继承此类并实现所有抽象方法
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化模型
        
        Args:
            config: 模型配置字典
        """
        self.config = config
        self._validate_config()
    
    @abstractmethod
    def _validate_config(self) -> bool:
        """
        验证模型配置是否有效
        
        Returns:
            配置是否有效
        
        Raises:
            ValueError: 配置无效时抛出异常
        """
        pass
    
    @abstractmethod
    async def generate(self, params: GenerateParams) -> bytes:
        """
        生成图片
        
        Args:
            params: 生成参数
        
        Returns:
            生成的图片二进制数据
        
        Raises:
            Exception: 生成失败时抛出异常
        """
        pass
    
    @abstractmethod
    async def validate_input(self, params: GenerateParams) -> bool:
        """
        验证输入参数
        
        Args:
            params: 生成参数
        
        Returns:
            参数是否有效
        
        Raises:
            ValueError: 参数无效时抛出异常
        """
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        Returns:
            模型信息字典（名称、版本、支持的功能等）
        """
        pass
    
    def _build_prompt(
        self,
        params: GenerateParams,
        default_style: str = "portrait photography"
    ) -> str:
        """
        构建提示词（可被子类重写）
        
        Args:
            params: 生成参数
            default_style: 默认风格
        
        Returns:
            构建的提示词
        """
        prompt_parts = []
        
        # 添加风格
        if params.style:
            prompt_parts.append(params.style)
        else:
            prompt_parts.append(default_style)
        
        # 添加拍摄类型
        if params.shot_type == "full_body":
            prompt_parts.append("full body shot")
        elif params.shot_type == "half_body":
            prompt_parts.append("half body shot")
        
        # 添加自定义提示词
        if params.prompt:
            prompt_parts.append(params.prompt)
        
        return ", ".join(prompt_parts)
    
    def _parse_aspect_ratio(self, aspect_ratio: str) -> tuple[int, int]:
        """
        解析图像比例字符串
        
        Args:
            aspect_ratio: 比例字符串，如 "9:16", "16:9", "1:1"
        
        Returns:
            (宽度, 高度) 元组
        
        Raises:
            ValueError: 比例格式错误
        """
        try:
            parts = aspect_ratio.split(":")
            if len(parts) != 2:
                raise ValueError(f"无效的比例格式: {aspect_ratio}")
            width = int(parts[0])
            height = int(parts[1])
            return width, height
        except (ValueError, IndexError) as e:
            raise ValueError(f"无法解析图像比例: {aspect_ratio}") from e
    
    def _parse_resolution(self, resolution: str) -> tuple[int, int]:
        """
        解析分辨率字符串
        
        Args:
            resolution: 分辨率字符串，如 "1024x1792"
        
        Returns:
            (宽度, 高度) 元组
        
        Raises:
            ValueError: 分辨率格式错误
        """
        try:
            parts = resolution.split("x")
            if len(parts) != 2:
                raise ValueError(f"无效的分辨率格式: {resolution}")
            width = int(parts[0])
            height = int(parts[1])
            return width, height
        except (ValueError, IndexError) as e:
            raise ValueError(f"无法解析分辨率: {resolution}") from e

