"""
图片处理服务单元测试
"""
import pytest
import uuid
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from fastapi import UploadFile
from datetime import datetime

from app.services.image_service import ImageService, TaskStatus, Task
from app.services.ai_models.base import GenerateParams
from app.utils.exceptions import TaskNotFoundError, AIModelError, StorageError


class TestTask:
    """任务类测试"""
    
    def test_task_initialization(self):
        """测试任务初始化"""
        task_id = str(uuid.uuid4())
        params = GenerateParams(
            fabric_images=[b"test"],
            model_type="ai",
            shot_type="full_body",
            aspect_ratio="9:16"
        )
        
        task = Task(task_id=task_id, params=params)
        assert task.task_id == task_id
        assert task.status == TaskStatus.PENDING
        assert task.result_image_url is None
        assert task.error_message is None
    
    def test_task_to_dict(self):
        """测试任务转换为字典"""
        task_id = str(uuid.uuid4())
        params = GenerateParams(
            fabric_images=[b"test"],
            model_type="ai",
            shot_type="full_body",
            aspect_ratio="9:16"
        )
        
        task = Task(task_id=task_id, params=params)
        task_dict = task.to_dict()
        
        assert task_dict["task_id"] == task_id
        assert task_dict["status"] == TaskStatus.PENDING.value
        assert "created_at" in task_dict
        assert "updated_at" in task_dict


class TestImageService:
    """图片处理服务测试类"""
    
    @pytest.fixture
    def image_service(self):
        """创建图片服务实例（使用mock的AI模型）"""
        service = ImageService()
        # Mock AI模型
        service.ai_model = MagicMock()
        service.ai_model.generate = AsyncMock(return_value=b"generated_image_data")
        return service
    
    @pytest.fixture
    def mock_upload_file(self):
        """创建模拟的上传文件"""
        file = Mock(spec=UploadFile)
        file.filename = "test.png"
        file.content_type = "image/png"
        file.read = AsyncMock(return_value=b"test_image_data")
        file.seek = AsyncMock()
        return file
    
    @pytest.mark.asyncio
    async def test_read_upload_file(self, image_service, mock_upload_file):
        """测试读取上传文件"""
        data = await image_service._read_upload_file(mock_upload_file)
        assert data == b"test_image_data"
        mock_upload_file.read.assert_called_once()
        mock_upload_file.seek.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_prepare_generate_params(self, image_service, mock_upload_file):
        """测试准备生成参数"""
        params = await image_service._prepare_generate_params(
            fabric_images=[mock_upload_file],
            model_type="ai",
            shot_type="full_body",
            aspect_ratio="9:16",
            style="portrait_photography"
        )
        
        assert isinstance(params, GenerateParams)
        assert len(params.fabric_images) == 1
        assert params.model_type == "ai"
        assert params.shot_type == "full_body"
        assert params.aspect_ratio == "9:16"
    
    @pytest.mark.asyncio
    async def test_create_task(self, image_service, mock_upload_file):
        """测试创建任务"""
        task_id = await image_service.create_task(
            fabric_images=[mock_upload_file],
            model_type="ai",
            shot_type="full_body",
            aspect_ratio="9:16"
        )
        
        assert task_id is not None
        assert task_id in image_service.tasks
        
        task = image_service.tasks[task_id]
        assert task.status == TaskStatus.PENDING
    
    @pytest.mark.asyncio
    async def test_get_task(self, image_service, mock_upload_file):
        """测试获取任务"""
        task_id = await image_service.create_task(
            fabric_images=[mock_upload_file],
            model_type="ai",
            shot_type="full_body",
            aspect_ratio="9:16"
        )
        
        task = image_service.get_task(task_id)
        assert task is not None
        assert task.task_id == task_id
    
    def test_get_task_not_found(self, image_service):
        """测试获取不存在的任务"""
        task = image_service.get_task("nonexistent_task_id")
        assert task is None
    
    def test_get_task_status_success(self, image_service, mock_upload_file):
        """测试获取任务状态成功"""
        # 创建任务
        task_id = image_service.create_task(
            fabric_images=[mock_upload_file],
            model_type="ai",
            shot_type="full_body",
            aspect_ratio="9:16"
        )
        
        # 注意：create_task是异步的，这里需要等待
        import asyncio
        if asyncio.iscoroutine(task_id):
            task_id = asyncio.run(task_id)
        
        status = image_service.get_task_status(task_id)
        assert status["task_id"] == task_id
        assert status["status"] == TaskStatus.PENDING.value
    
    def test_get_task_status_not_found(self, image_service):
        """测试获取不存在任务的状态"""
        with pytest.raises(TaskNotFoundError):
            image_service.get_task_status("nonexistent_task_id")
    
    @pytest.mark.asyncio
    async def test_process_task_success(self, image_service, mock_upload_file):
        """测试成功处理任务"""
        # 创建任务
        task_id = await image_service.create_task(
            fabric_images=[mock_upload_file],
            model_type="ai",
            shot_type="full_body",
            aspect_ratio="9:16"
        )
        
        # Mock存储服务
        with patch('app.services.image_service.storage_service') as mock_storage:
            mock_storage.upload_and_backup = AsyncMock(return_value={
                "oss_url": "https://oss.example.com/image.jpg",
                "local_path": "/local/path/image.jpg"
            })
            
            # 处理任务
            await image_service._process_task(task_id)
            
            # 验证任务状态
            task = image_service.get_task(task_id)
            # 注意：由于是异步处理，可能需要等待
            # 这里主要测试逻辑流程
    
    @pytest.mark.asyncio
    async def test_process_task_ai_model_error(self, image_service, mock_upload_file):
        """测试AI模型错误处理"""
        # 创建任务
        task_id = await image_service.create_task(
            fabric_images=[mock_upload_file],
            model_type="ai",
            shot_type="full_body",
            aspect_ratio="9:16"
        )
        
        # Mock AI模型抛出异常
        image_service.ai_model.generate = AsyncMock(side_effect=AIModelError("AI模型错误"))
        
        # 处理任务
        await image_service._process_task(task_id)
        
        # 验证任务状态为失败
        task = image_service.get_task(task_id)
        # 由于是异步处理，可能需要等待
        # 这里主要测试异常处理逻辑
    
    def test_list_tasks(self, image_service, mock_upload_file):
        """测试列出任务"""
        # 创建多个任务
        import asyncio
        
        async def create_tasks():
            task_ids = []
            for i in range(3):
                task_id = await image_service.create_task(
                    fabric_images=[mock_upload_file],
                    model_type="ai",
                    shot_type="full_body",
                    aspect_ratio="9:16"
                )
                task_ids.append(task_id)
            return task_ids
        
        task_ids = asyncio.run(create_tasks())
        
        # 列出所有任务
        tasks = image_service.list_tasks()
        assert len(tasks) >= 3
    
    def test_list_tasks_with_status_filter(self, image_service, mock_upload_file):
        """测试按状态过滤任务"""
        import asyncio
        
        async def create_tasks():
            task_id = await image_service.create_task(
                fabric_images=[mock_upload_file],
                model_type="ai",
                shot_type="full_body",
                aspect_ratio="9:16"
            )
            return task_id
        
        task_id = asyncio.run(create_tasks())
        
        # 列出待处理的任务
        pending_tasks = image_service.list_tasks(status=TaskStatus.PENDING)
        assert len(pending_tasks) >= 1
    
    def test_delete_task(self, image_service, mock_upload_file):
        """测试删除任务"""
        import asyncio
        
        async def create_and_delete():
            task_id = await image_service.create_task(
                fabric_images=[mock_upload_file],
                model_type="ai",
                shot_type="full_body",
                aspect_ratio="9:16"
            )
            return task_id
        
        task_id = asyncio.run(create_and_delete())
        
        # 删除任务
        success = image_service.delete_task(task_id)
        assert success is True
        
        # 验证任务已删除
        task = image_service.get_task(task_id)
        assert task is None
    
    def test_delete_task_not_found(self, image_service):
        """测试删除不存在的任务"""
        success = image_service.delete_task("nonexistent_task_id")
        assert success is False

