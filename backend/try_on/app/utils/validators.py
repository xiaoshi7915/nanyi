"""
验证工具模块
"""
import os
import io
from typing import BinaryIO
from PIL import Image
from fastapi import UploadFile, HTTPException, status


# 允许的图片格式
ALLOWED_IMAGE_FORMATS = {"image/jpeg", "image/jpg", "image/png"}
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}

# 图片文件的Magic Number（文件头签名）
# JPEG: FF D8 FF
# PNG: 89 50 4E 47 0D 0A 1A 0A
IMAGE_MAGIC_NUMBERS = {
    b'\xff\xd8\xff': 'jpeg',  # JPEG文件头
    b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a': 'png',  # PNG文件头
}


def validate_image_file(file: UploadFile) -> None:
    """
    验证上传的图片文件
    
    Args:
        file: FastAPI上传文件对象
    
    Raises:
        HTTPException: 如果文件格式不支持
    """
    # 检查文件类型
    if file.content_type not in ALLOWED_IMAGE_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的图片格式：{file.content_type}。支持的格式：{', '.join(ALLOWED_IMAGE_FORMATS)}"
        )
    
    # 检查文件扩展名
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件扩展名：{file_ext}。支持的扩展名：{', '.join(ALLOWED_IMAGE_EXTENSIONS)}"
        )


async def validate_image_size(file: UploadFile, max_size_mb: int = 10) -> None:
    """
    验证图片文件大小
    
    Args:
        file: FastAPI上传文件对象
        max_size_mb: 最大文件大小（MB）
    
    Raises:
        HTTPException: 如果文件大小超限
    """
    # 读取文件内容以获取大小（支持异步）
    file_data = await file.read()
    file_size = len(file_data)
    # 重置文件指针（通过创建新的 SpooledTemporaryFile）
    await file.seek(0)
    
    max_size_bytes = max_size_mb * 1024 * 1024
    
    if file_size > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"图片大小超过限制：{file_size / 1024 / 1024:.2f}MB，最大允许：{max_size_mb}MB"
        )


def _validate_image_magic_number(file_data: bytes) -> bool:
    """
    验证图片文件的Magic Number（文件头签名）
    用于检测文件是否真的是图片文件，防止恶意文件上传
    
    Args:
        file_data: 文件二进制数据
    
    Returns:
        是否为有效的图片文件
    """
    if not file_data or len(file_data) < 3:
        return False
    
    # 检查JPEG文件头（至少需要3字节）
    if file_data[:3] == b'\xff\xd8\xff':
        return True
    
    # 检查PNG文件头（需要8字节）
    if len(file_data) >= 8 and file_data[:8] == b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a':
        return True
    
    return False


async def validate_image_content(file: UploadFile) -> None:
    """
    验证图片内容是否有效（通过Magic Number和PIL验证）
    
    Args:
        file: FastAPI上传文件对象
    
    Raises:
        HTTPException: 如果图片内容无效
    """
    try:
        # 读取文件内容（支持异步）
        file_data = await file.read()
        
        # 首先验证Magic Number（文件头签名）
        if not _validate_image_magic_number(file_data):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文件内容验证失败：不是有效的图片文件（Magic Number不匹配）"
            )
        
        # 使用 BytesIO 创建文件对象
        image_file = io.BytesIO(file_data)
        image = Image.open(image_file)
        # 验证图片
        image.verify()
        # 重置文件指针
        await file.seek(0)
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的图片文件：{str(e)}"
        )


async def validate_all_images(files: list[UploadFile], max_size_mb: int = 10) -> None:
    """
    批量验证图片文件
    
    Args:
        files: 图片文件列表
        max_size_mb: 最大文件大小（MB）
    
    Raises:
        HTTPException: 如果任何文件验证失败
    """
    for file in files:
        validate_image_file(file)
        await validate_image_size(file, max_size_mb)
        await validate_image_content(file)

