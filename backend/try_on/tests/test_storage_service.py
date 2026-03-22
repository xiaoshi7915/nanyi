"""
存储服务单元测试
"""
import pytest
import os
import tempfile
import shutil
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from app.services.storage_service import StorageService
from app.utils.exceptions import StorageError


class TestStorageService:
    """存储服务测试类"""
    
    @pytest.fixture
    def temp_storage_dir(self):
        """创建临时存储目录"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # 清理
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def storage_service(self, temp_storage_dir, monkeypatch):
        """创建存储服务实例（使用mock的OSS）"""
        # Mock OSS配置
        with patch('app.services.storage_service.oss2') as mock_oss2:
            # Mock Auth和Bucket
            mock_auth = MagicMock()
            mock_bucket = MagicMock()
            mock_oss2.Auth.return_value = mock_auth
            mock_oss2.Bucket.return_value = mock_bucket
            
            # 设置测试配置
            monkeypatch.setenv("OSS_ACCESS_KEY_ID", "test_key")
            monkeypatch.setenv("OSS_ACCESS_KEY_SECRET", "test_secret")
            monkeypatch.setenv("OSS_BUCKET_NAME", "test_bucket")
            monkeypatch.setenv("OSS_ENDPOINT", "oss-cn-hangzhou.aliyuncs.com")
            monkeypatch.setenv("STORAGE_LOCAL_PATH", temp_storage_dir)
            
            service = StorageService()
            service.oss_bucket = mock_bucket  # 使用mock的bucket
            return service
    
    def test_generate_file_name(self, storage_service):
        """测试生成文件名"""
        filename = storage_service._generate_file_name(prefix="test")
        assert filename.startswith("test_")
        assert ".jpg" in filename or ".png" in filename
    
    def test_generate_file_name_with_extension(self, storage_service):
        """测试使用原始文件名扩展名"""
        filename = storage_service._generate_file_name(
            original_filename="image.png",
            prefix="test"
        )
        assert filename.endswith(".png")
    
    def test_get_oss_key(self, storage_service):
        """测试生成OSS对象键"""
        oss_key = storage_service._get_oss_key("test.jpg", "generated")
        assert oss_key.startswith("generated/")
        assert "test.jpg" in oss_key
        # 应该包含日期路径
        assert "/" in oss_key.replace("generated/", "").replace("/test.jpg", "")
    
    @pytest.mark.asyncio
    async def test_upload_to_oss_success(self, storage_service):
        """测试成功上传到OSS"""
        test_data = b"test file content"
        
        # Mock OSS响应
        mock_result = MagicMock()
        mock_result.status = 200
        storage_service.oss_bucket.put_object.return_value = mock_result
        
        # 执行上传
        url = await storage_service.upload_to_oss(
            file_data=test_data,
            filename="test.jpg",
            subdir="generated"
        )
        
        # 验证
        assert url is not None
        # URL 应该包含 OSS 端点信息
        assert "oss-cn-hangzhou.aliyuncs.com" in url or "oss" in url.lower()
        assert url.startswith("http")
        storage_service.oss_bucket.put_object.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_upload_to_oss_failure(self, storage_service):
        """测试OSS上传失败"""
        test_data = b"test file content"
        
        # Mock OSS响应失败
        mock_result = MagicMock()
        mock_result.status = 500
        storage_service.oss_bucket.put_object.return_value = mock_result
        
        # 执行上传，应该抛出异常
        with pytest.raises(Exception):
            await storage_service.upload_to_oss(
                file_data=test_data,
                filename="test.jpg"
            )
    
    @pytest.mark.asyncio
    async def test_save_to_local_success(self, storage_service, temp_storage_dir):
        """测试成功保存到本地"""
        test_data = b"test file content"
        
        file_path = await storage_service.save_to_local(
            file_data=test_data,
            filename="test_local.jpg",
            subdir="generated"
        )
        
        # 验证文件存在
        assert os.path.exists(file_path)
        assert file_path.endswith("test_local.jpg")
        
        # 验证文件内容
        with open(file_path, "rb") as f:
            assert f.read() == test_data
    
    @pytest.mark.asyncio
    async def test_save_to_local_auto_filename(self, storage_service):
        """测试自动生成文件名保存到本地"""
        test_data = b"test file content"
        
        file_path = await storage_service.save_to_local(
            file_data=test_data,
            subdir="generated"
        )
        
        # 验证文件存在
        assert os.path.exists(file_path)
        assert "generated_" in os.path.basename(file_path)
    
    @pytest.mark.asyncio
    async def test_upload_and_backup_success(self, storage_service, temp_storage_dir):
        """测试上传和备份成功"""
        test_data = b"test file content"
        
        # Mock OSS响应
        mock_result = MagicMock()
        mock_result.status = 200
        storage_service.oss_bucket.put_object.return_value = mock_result
        
        result = await storage_service.upload_and_backup(
            file_data=test_data,
            filename="test_backup.jpg",
            subdir="generated",
            backup_local=True
        )
        
        # 验证结果
        assert "oss_url" in result
        assert "local_path" in result
        assert "filename" in result
        assert result["oss_url"] is not None
        assert result["local_path"] is not None
        assert os.path.exists(result["local_path"])
    
    @pytest.mark.asyncio
    async def test_upload_and_backup_no_local(self, storage_service):
        """测试只上传不备份"""
        test_data = b"test file content"
        
        # Mock OSS响应
        mock_result = MagicMock()
        mock_result.status = 200
        storage_service.oss_bucket.put_object.return_value = mock_result
        
        result = await storage_service.upload_and_backup(
            file_data=test_data,
            filename="test_no_backup.jpg",
            backup_local=False
        )
        
        # 验证结果
        assert result["oss_url"] is not None
        assert result["local_path"] is None
    
    @pytest.mark.asyncio
    async def test_delete_from_oss_success(self, storage_service):
        """测试从OSS删除文件成功"""
        mock_result = MagicMock()
        mock_result.status = 204
        storage_service.oss_bucket.delete_object.return_value = mock_result
        
        success = await storage_service.delete_from_oss("test/key.jpg")
        assert success is True
    
    @pytest.mark.asyncio
    async def test_delete_from_local_success(self, storage_service, temp_storage_dir):
        """测试从本地删除文件成功"""
        # 先创建一个文件
        test_file = os.path.join(temp_storage_dir, "test_delete.jpg")
        with open(test_file, "wb") as f:
            f.write(b"test content")
        
        # 删除文件
        success = await storage_service.delete_from_local(test_file)
        assert success is True
        assert not os.path.exists(test_file)
    
    @pytest.mark.asyncio
    async def test_delete_from_local_not_exists(self, storage_service):
        """测试删除不存在的文件"""
        success = await storage_service.delete_from_local("/nonexistent/file.jpg")
        assert success is False
    
    def test_get_file_size(self, storage_service):
        """测试获取文件大小"""
        test_data = b"test content"
        size = storage_service.get_file_size(test_data)
        assert size == len(test_data)
    
    def test_format_file_size(self, storage_service):
        """测试格式化文件大小"""
        assert "B" in storage_service.format_file_size(512)
        assert "KB" in storage_service.format_file_size(1024)
        assert "MB" in storage_service.format_file_size(1024 * 1024)
        assert "GB" in storage_service.format_file_size(1024 * 1024 * 1024)

