"""
验证工具单元测试
"""
import pytest
import io
from PIL import Image
from unittest.mock import Mock, AsyncMock
from fastapi import UploadFile
from app.utils.validators import validate_all_images
from app.utils.exceptions import ValidationError


class TestValidators:
    """验证工具测试类"""
    
    @pytest.fixture
    def mock_image_data(self):
        """生成测试图片数据 - 创建一个有效的1x1像素PNG图片"""
        # 创建一个1x1像素的PNG图片
        img = Image.new('RGB', (1, 1), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        return img_bytes.getvalue()
    
    @pytest.fixture
    def mock_upload_file(self, mock_image_data):
        """创建模拟的上传文件"""
        file = Mock(spec=UploadFile)
        file.filename = "test.png"
        file.content_type = "image/png"
        file.size = len(mock_image_data)
        # 每次调用 read 都返回新的数据副本，并支持 seek
        async def read_mock():
            return mock_image_data
        file.read = AsyncMock(side_effect=read_mock)
        file.seek = AsyncMock(return_value=None)
        return file
    
    @pytest.mark.asyncio
    async def test_validate_all_images_success(self, mock_upload_file):
        """测试成功验证图片"""
        # 应该不抛出异常
        await validate_all_images([mock_upload_file], max_size_mb=10)
    
    @pytest.mark.asyncio
    async def test_validate_all_images_invalid_format(self):
        """测试无效的图片格式"""
        file = Mock(spec=UploadFile)
        file.filename = "test.txt"
        file.content_type = "text/plain"
        file.size = 100
        async def read_mock():
            return b"not an image"
        file.read = AsyncMock(side_effect=read_mock)
        file.seek = AsyncMock(return_value=None)
        
        # 应该因为格式不支持而失败
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await validate_all_images([file], max_size_mb=10)
        
        assert exc_info.value.status_code == 400
        assert "格式" in str(exc_info.value.detail) or "不支持" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_validate_all_images_too_large(self):
        """测试图片过大"""
        # 创建一个大的文件数据（但仍然是有效的PNG格式）
        # 创建一个较大的PNG图片
        img = Image.new('RGB', (1000, 1000), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG', optimize=False)
        large_data = img_bytes.getvalue()
        # 如果还不够大，填充数据（但这样会破坏PNG格式，所以我们需要用其他方法）
        # 实际上，我们需要创建一个真正的大文件，但保持PNG格式
        # 为了测试，我们创建一个11MB的数据，但验证器会在大小检查阶段就失败
        large_data = b"x" * (11 * 1024 * 1024)  # 11MB
        
        file = Mock(spec=UploadFile)
        file.filename = "large.png"
        file.content_type = "image/png"
        file.size = len(large_data)
        async def read_mock():
            return large_data
        file.read = AsyncMock(side_effect=read_mock)
        file.seek = AsyncMock(return_value=None)
        
        # 应该因为大小超限而失败（在大小验证阶段）
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await validate_all_images([file], max_size_mb=10)
        
        assert exc_info.value.status_code == 400
        assert "大小" in str(exc_info.value.detail) or "超过" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_validate_all_images_empty_list(self):
        """测试空列表"""
        # 空列表应该不抛出异常（可能由业务逻辑层处理）
        await validate_all_images([], max_size_mb=10)
    
    @pytest.mark.asyncio
    async def test_validate_all_images_multiple_files(self, mock_upload_file):
        """测试验证多个文件"""
        files = [mock_upload_file, mock_upload_file]
        # 应该不抛出异常
        await validate_all_images(files, max_size_mb=10)
    
    @pytest.mark.asyncio
    async def test_validate_all_images_jpeg_format(self):
        """测试JPEG格式验证"""
        # 创建一个有效的JPEG图片
        img = Image.new('RGB', (10, 10), color='blue')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        jpeg_data = img_bytes.getvalue()
        
        file = Mock(spec=UploadFile)
        file.filename = "test.jpg"
        file.content_type = "image/jpeg"
        file.size = len(jpeg_data)
        async def read_mock():
            return jpeg_data
        file.read = AsyncMock(side_effect=read_mock)
        file.seek = AsyncMock(return_value=None)
        
        # 应该成功验证
        await validate_all_images([file], max_size_mb=10)

