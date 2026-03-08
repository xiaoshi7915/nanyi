"""
API集成测试
测试完整的API请求流程
"""
import pytest
import io
from PIL import Image
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from app.main import app


class TestTryOnAPI:
    """试衣API集成测试类"""
    
    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_image_data(self):
        """生成测试图片数据 - 创建一个有效的1x1像素PNG图片"""
        # 创建一个1x1像素的PNG图片
        img = Image.new('RGB', (1, 1), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        return img_bytes.getvalue()
    
    def test_root_endpoint(self, client):
        """测试根端点"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "status" in data
    
    def test_health_check(self, client):
        """测试健康检查端点"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    @patch('app.api.v1.try_on.rate_limit_service')
    @patch('app.api.v1.try_on.image_service')
    def test_generate_try_on_success(
        self,
        mock_image_service,
        mock_rate_limit,
        client,
        mock_image_data
    ):
        """测试成功生成试衣效果图"""
        # Mock限流服务
        mock_rate_limit.check_rate_limit.return_value = (True, None)
        
        # Mock图片服务
        mock_image_service.create_task = AsyncMock(return_value="test_task_id_123")
        
        # 准备请求数据
        files = {
            "fabric_images": ("test.png", mock_image_data, "image/png")
        }
        data = {
            "model_type": "ai",
            "shot_type": "full_body",
            "aspect_ratio": "9:16",
            "style": "portrait_photography"
        }
        
        # 发送请求
        response = client.post("/api/v1/try-on/generate", files=files, data=data)
        
        # 验证响应
        assert response.status_code == 200
        response_data = response.json()
        assert "task_id" in response_data
        assert response_data["status"] == "processing"
    
    @patch('app.api.v1.try_on.rate_limit_service')
    def test_generate_try_on_rate_limit_exceeded(
        self,
        mock_rate_limit,
        client,
        mock_image_data
    ):
        """测试限流拒绝请求"""
        # Mock限流服务返回拒绝
        mock_rate_limit.check_rate_limit.return_value = (False, "请求过于频繁")
        
        # 准备请求数据
        files = {
            "fabric_images": ("test.png", mock_image_data, "image/png")
        }
        data = {
            "model_type": "ai",
            "shot_type": "full_body",
            "aspect_ratio": "9:16"
        }
        
        # 发送请求
        response = client.post("/api/v1/try-on/generate", files=files, data=data)
        
        # 验证响应（应该返回限流错误）
        assert response.status_code in [429, 400]  # 限流错误或业务错误
    
    @patch('app.api.v1.try_on.rate_limit_service')
    @patch('app.api.v1.try_on.image_service')
    def test_get_task_status_success(
        self,
        mock_image_service,
        mock_rate_limit,
        client
    ):
        """测试成功查询任务状态"""
        # Mock限流服务
        mock_rate_limit.check_rate_limit.return_value = (True, None)
        
        # Mock图片服务
        mock_image_service.get_task_status.return_value = {
            "task_id": "test_task_id_123",
            "status": "processing",
            "result_image_url": None,
            "local_path": None,
            "error_message": None,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00"
        }
        
        # 发送请求
        response = client.get("/api/v1/try-on/status/test_task_id_123")
        
        # 验证响应
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["task_id"] == "test_task_id_123"
        assert response_data["status"] == "processing"
    
    @patch('app.api.v1.try_on.rate_limit_service')
    @patch('app.api.v1.try_on.image_service')
    def test_get_task_status_not_found(
        self,
        mock_image_service,
        mock_rate_limit,
        client
    ):
        """测试查询不存在的任务"""
        # Mock限流服务
        mock_rate_limit.check_rate_limit.return_value = (True, None)
        
        # Mock图片服务抛出任务不存在异常
        from app.utils.exceptions import TaskNotFoundError
        mock_image_service.get_task_status.side_effect = TaskNotFoundError(
            "任务不存在: test_task_id_999"
        )
        
        # 发送请求
        response = client.get("/api/v1/try-on/status/test_task_id_999")
        
        # 验证响应（应该返回404或400）
        assert response.status_code in [404, 400]
    
    @patch('app.api.v1.try_on.rate_limit_service')
    def test_generate_try_on_missing_required_fields(
        self,
        mock_rate_limit,
        client,
        mock_image_data
    ):
        """测试缺少必需字段"""
        # Mock限流服务
        mock_rate_limit.check_rate_limit.return_value = (True, None)
        
        # 准备请求数据（缺少必需字段）
        files = {
            "fabric_images": ("test.png", mock_image_data, "image/png")
        }
        data = {
            # 缺少 model_type, shot_type, aspect_ratio
        }
        
        # 发送请求
        response = client.post("/api/v1/try-on/generate", files=files, data=data)
        
        # 验证响应（应该返回验证错误）
        assert response.status_code == 422  # FastAPI验证错误
    
    @patch('app.api.v1.try_on.rate_limit_service')
    def test_generate_try_on_invalid_model_type(
        self,
        mock_rate_limit,
        client,
        mock_image_data
    ):
        """测试无效的模特类型"""
        # Mock限流服务
        mock_rate_limit.check_rate_limit.return_value = (True, None)
        
        # 准备请求数据
        files = {
            "fabric_images": ("test.png", mock_image_data, "image/png")
        }
        data = {
            "model_type": "invalid_type",  # 无效的类型
            "shot_type": "full_body",
            "aspect_ratio": "9:16"
        }
        
        # 发送请求
        response = client.post("/api/v1/try-on/generate", files=files, data=data)
        
        # 验证响应（应该返回验证错误或业务错误）
        assert response.status_code in [400, 422]
    
    @patch('app.api.v1.try_on.rate_limit_service')
    @patch('app.api.v1.try_on.image_service')
    def test_generate_try_on_real_person_missing(
        self,
        mock_image_service,
        mock_rate_limit,
        client,
        mock_image_data
    ):
        """测试真人模特模式但缺少真人照片"""
        # Mock限流服务
        mock_rate_limit.check_rate_limit.return_value = (True, None)
        
        # 准备请求数据（model_type为real但没有real_person_image）
        files = {
            "fabric_images": ("test.png", mock_image_data, "image/png")
        }
        data = {
            "model_type": "real",  # 真人模特
            "shot_type": "full_body",
            "aspect_ratio": "9:16"
        }
        
        # 发送请求
        response = client.post("/api/v1/try-on/generate", files=files, data=data)
        
        # 验证响应（应该返回验证错误）
        assert response.status_code in [400, 422]

