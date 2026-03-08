"""
Pytest配置文件
提供测试用的fixtures和配置
"""
import pytest
import os
import tempfile
import shutil
import warnings
from typing import Generator
from unittest.mock import Mock, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from fastapi import UploadFile

# 过滤 Pydantic 受保护命名空间警告（这些警告来自 FastAPI 动态创建的模型）
warnings.filterwarnings("ignore", message=".*Field.*has conflict with protected namespace.*")

from app.main import app
from app.config import Settings


@pytest.fixture
def test_settings() -> Settings:
    """
    测试用的配置对象
    使用临时目录和测试配置
    """
    # 创建临时存储目录
    temp_dir = tempfile.mkdtemp()
    
    # 创建测试配置
    settings = Settings(
        app_name="AI试衣图生图服务(测试)",
        debug=True,
        log_level="DEBUG",
        storage_local_path=temp_dir,
        rate_limit_per_minute=1000,  # 测试时放宽限流
        rate_limit_per_hour=100000,
        max_image_size_mb=10,
        max_images_per_request=5,
        # 使用测试用的OSS配置（如果环境变量未设置，使用mock）
        oss_access_key_id=os.getenv("TEST_OSS_ACCESS_KEY_ID", "test_key"),
        oss_access_key_secret=os.getenv("TEST_OSS_ACCESS_KEY_SECRET", "test_secret"),
        oss_bucket_name=os.getenv("TEST_OSS_BUCKET_NAME", "test_bucket"),
        oss_endpoint=os.getenv("TEST_OSS_ENDPOINT", "oss-cn-hangzhou.aliyuncs.com"),
        # 使用测试用的API配置
        ark_api_key=os.getenv("TEST_ARK_API_KEY", "test_api_key"),
        ark_base_url=os.getenv("TEST_ARK_BASE_URL", "https://test.api.com"),
        ark_model_name=os.getenv("TEST_ARK_MODEL_NAME", "test_model"),
    )
    
    yield settings
    
    # 清理临时目录
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


@pytest.fixture
def client() -> TestClient:
    """
    FastAPI测试客户端
    """
    return TestClient(app)


@pytest.fixture
def mock_image_data() -> bytes:
    """
    生成一个简单的测试图片数据（1x1像素的PNG）
    """
    # 最小有效的PNG文件（1x1像素，红色）
    return (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
        b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13'
        b'\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc\xf8'
        b'\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00IEND\xaeB`\x82'
    )


@pytest.fixture
def mock_upload_file(mock_image_data: bytes) -> UploadFile:
    """
    创建模拟的上传文件对象
    """
    file = Mock(spec=UploadFile)
    file.filename = "test_image.png"
    file.content_type = "image/png"
    file.size = len(mock_image_data)
    file.read = AsyncMock(return_value=mock_image_data)
    file.seek = AsyncMock()
    return file


@pytest.fixture
def mock_oss_bucket():
    """
    模拟OSS Bucket对象
    """
    bucket = MagicMock()
    # 模拟put_object返回成功
    put_result = MagicMock()
    put_result.status = 200
    bucket.put_object.return_value = put_result
    
    # 模拟delete_object返回成功
    delete_result = MagicMock()
    delete_result.status = 204
    bucket.delete_object.return_value = delete_result
    
    return bucket


@pytest.fixture
def mock_ai_model():
    """
    模拟AI模型对象
    """
    model = MagicMock()
    # 模拟生成方法返回图片数据
    mock_image_data = b"fake_generated_image_data"
    model.generate = AsyncMock(return_value=mock_image_data)
    model.validate_input = AsyncMock(return_value=True)
    model.get_model_info = MagicMock(return_value={
        "name": "TestModel",
        "version": "1.0",
        "provider": "test"
    })
    return model


@pytest.fixture(autouse=True)
def reset_services():
    """
    每个测试前重置服务状态
    """
    # 在测试前执行
    yield
    # 在测试后执行清理（如果需要）
    pass

