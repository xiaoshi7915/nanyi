#!/usr/bin/env python3
"""
测试调用真实模型
"""
import asyncio
import sys
import os
from pathlib import Path

# 添加项目路径
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.services.image_service import image_service
from app.utils.logger import setup_logger, get_logger
from app.config import settings

logger = setup_logger(level="INFO")


async def test_real_model():
    """测试调用真实模型"""
    print("=" * 60)
    print("测试调用真实模型")
    print("=" * 60)
    print(f"USE_MOCK_AI: {os.getenv('USE_MOCK_AI', 'false')}")
    print(f"ARK_API_KEY: {'已设置' if settings.ark_api_key else '未设置'}")
    print(f"模型: {settings.ark_model_name}")
    print()
    
    # 检查是否使用 Mock 模型
    if isinstance(image_service.ai_model, type(image_service.ai_model).__bases__[0] if hasattr(type(image_service.ai_model), '__bases__') else None):
        model_name = type(image_service.ai_model).__name__
        print(f"当前使用的模型: {model_name}")
        
        if "Mock" in model_name:
            print("❌ 警告：正在使用 Mock 模型，请检查 USE_MOCK_AI 环境变量")
        else:
            print(f"✅ 使用真实模型: {model_name}")
    
    print()
    print("模型信息:")
    try:
        model_info = image_service.ai_model.get_model_info()
        for key, value in model_info.items():
            print(f"  {key}: {value}")
    except Exception as e:
        print(f"  ❌ 获取模型信息失败: {e}")
    
    print()
    print("=" * 60)
    print("✅ 测试完成")
    print("=" * 60)
    print()
    print("提示：")
    print("1. 确保 .env 文件中 USE_MOCK_AI=false")
    print("2. 确保 ARK_API_KEY 已正确配置")
    print("3. 可以通过 API 端点 /api/v1/try-on/generate 测试")
    print("4. 支持的自定义提示词参数：prompt")


if __name__ == "__main__":
    asyncio.run(test_real_model())

