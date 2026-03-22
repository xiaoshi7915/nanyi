"""
提示词管理服务模块
负责构建和管理AI模型生成所需的提示词
"""
from typing import Optional, Dict, Any
from app.services.ai_models.base import GenerateParams
from app.utils.logger import get_logger

# 获取日志记录器
logger = get_logger(__name__)


class PromptService:
    """
    提示词管理服务类
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
    
    def __init__(self):
        """初始化提示词服务"""
        logger.info("提示词管理服务初始化完成")
    
    def build_prompt(
        self,
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
        if style in self.STYLE_TEMPLATES:
            prompt_parts.append(self.STYLE_TEMPLATES[style])
        else:
            # 如果风格不在模板中，直接使用
            prompt_parts.append(style)
        
        # 添加拍摄类型
        # 如果model_type为real，强制使用full_body生成全身照效果
        # 无论用户上传的是全身照、半身照还是登记照，都生成全身照
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
            elif effective_shot_type in self.SHOT_TYPE_DESCRIPTIONS:
                prompt_parts.append(self.SHOT_TYPE_DESCRIPTIONS[effective_shot_type])
        
        # 添加模特类型描述（如果AI模式还没有添加）
        if params.model_type == "ai" and not params.fabric_images:
            # AI模式但没有成衣图的情况（理论上不应该发生）
            prompt_parts.append("真实女模特，照片级真实女性，人类")
            prompt_parts.append("不是机器人，不是AI机器人，不是机械")
            logger.debug("AI模式：已添加真实女模特描述（避免生成机器人）")
        elif params.model_type == "real":
            prompt_parts.append(self.MODEL_TYPE_DESCRIPTIONS[params.model_type])
        
        # 添加成衣相关的描述（真人模式或AI模式的补充）
        if params.fabric_images:
            if params.model_type == "real":
                # 真人图模式：使用更明确和强调性的描述，确保AI理解要穿上成衣图中的旗袍
                # 2图输入：第一张是真人图，第二张是成衣图
                # 明确指定是旗袍，确保生成完整的旗袍，不是上衣+裤子
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
        
        # 添加自定义提示词（如果提供）
        if params.prompt:
            prompt_parts.append(params.prompt)
        
        # 添加质量描述
        prompt_parts.append("高质量，细节丰富，清晰对焦")
        
        # 组合提示词
        prompt = ", ".join(prompt_parts)
        
        logger.debug(f"构建提示词: {prompt}")
        return prompt
    
    def get_style_template(self, style: str) -> Optional[str]:
        """
        获取风格模板
        
        Args:
            style: 风格名称
        
        Returns:
            风格模板字符串，如果不存在返回None
        """
        return self.STYLE_TEMPLATES.get(style)
    
    def add_style_template(self, style: str, template: str) -> None:
        """
        添加自定义风格模板
        
        Args:
            style: 风格名称
            template: 风格模板字符串
        """
        self.STYLE_TEMPLATES[style] = template
        logger.info(f"添加风格模板: {style}")
    
    def list_available_styles(self) -> list[str]:
        """
        列出所有可用的风格
        
        Returns:
            风格名称列表
        """
        return list(self.STYLE_TEMPLATES.keys())


# 全局提示词服务实例
prompt_service = PromptService()

