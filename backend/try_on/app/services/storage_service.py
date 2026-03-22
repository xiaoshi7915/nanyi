"""
存储服务模块
支持阿里云OSS上传和本地备份功能
"""
import os
import uuid
import asyncio
import time
from datetime import datetime
from typing import Optional
import oss2
from oss2.exceptions import OssError

from app.config import settings
from app.utils.logger import get_logger
from app.utils.exceptions import StorageError

# 获取日志记录器
logger = get_logger(__name__)


class StorageService:
    """存储服务类，负责OSS上传和本地备份"""
    
    def __init__(self):
        """初始化存储服务"""
        # 初始化OSS客户端
        self.oss_auth = oss2.Auth(
            settings.oss_access_key_id,
            settings.oss_access_key_secret
        )
        self.oss_bucket = oss2.Bucket(
            self.oss_auth,
            settings.oss_endpoint,
            settings.oss_bucket_name
        )
        
        # 确保本地存储目录存在
        self._ensure_local_dirs()
        
        logger.info("存储服务初始化完成")
    
    def _ensure_local_dirs(self) -> None:
        """确保本地存储目录存在"""
        os.makedirs(settings.storage_upload_path, exist_ok=True)
        os.makedirs(settings.storage_fabric_path, exist_ok=True)
        os.makedirs(settings.storage_real_person_path, exist_ok=True)
        os.makedirs(settings.storage_generated_path, exist_ok=True)
        logger.debug(
            f"本地存储目录已确保存在: "
            f"uploads={settings.storage_upload_path}, "
            f"fabric={settings.storage_fabric_path}, "
            f"real_person={settings.storage_real_person_path}, "
            f"generated={settings.storage_generated_path}"
        )
    
    def _generate_file_name(
        self, 
        original_filename: Optional[str] = None, 
        prefix: str = "file",
        fabric_image_name: Optional[str] = None,
        model_type: Optional[str] = None
    ) -> str:
        """
        生成唯一的文件名
        
        Args:
            original_filename: 原始文件名（可选）
            prefix: 文件前缀
            fabric_image_name: 成衣图文件名（不含扩展名）
            model_type: 模特类型（ai 或 real）
        
        Returns:
            唯一文件名
        """
        # 获取文件扩展名
        ext = ""
        if original_filename:
            ext = os.path.splitext(original_filename)[1]
        elif not ext:
            ext = ".jpg"  # 默认扩展名
        
        # 生成时间戳
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 如果提供了成衣图名和模特类型，使用新命名规则：布料成衣图名+AI/真人+时间戳
        if fabric_image_name and model_type:
            # 清理成衣图名（去除特殊字符，只保留字母数字和中文）
            import re
            clean_name = re.sub(r'[^\w\u4e00-\u9fff]', '_', fabric_image_name)
            # 限制长度，避免文件名过长
            if len(clean_name) > 50:
                clean_name = clean_name[:50]
            
            # 根据模特类型设置后缀
            model_suffix = "AI" if model_type == "ai" else "真人"
            filename = f"{clean_name}_{model_suffix}_{timestamp}{ext}"
        else:
            # 使用旧命名规则：前缀_时间戳_UUID.扩展名
            unique_id = str(uuid.uuid4())[:8]
            filename = f"{prefix}_{timestamp}_{unique_id}{ext}"
        
        return filename
    
    def _get_oss_key(self, filename: str, subdir: str = "generated") -> str:
        """
        获取OSS对象键（路径）
        
        Args:
            filename: 文件名
            subdir: 子目录（generated, uploads, fabric, real_person）
        
        Returns:
            OSS对象键
        """
        # 使用日期作为目录结构：generated/2024/01/23/filename.jpg
        # 或 fabric/2024/01/23/filename.jpg
        date_path = datetime.now().strftime("%Y/%m/%d")
        return f"{subdir}/{date_path}/{filename}"
    
    async def upload_to_oss(
        self,
        file_data: bytes,
        filename: Optional[str] = None,
        subdir: str = "generated",
        content_type: str = "image/jpeg",
        max_retries: int = 3
    ) -> str:
        """
        上传文件到阿里云OSS（带重试机制）
        
        Args:
            file_data: 文件二进制数据
            filename: 文件名（可选，不提供则自动生成）
            subdir: 子目录（generated 或 uploads）
            content_type: 文件MIME类型
            max_retries: 最大重试次数
        
        Returns:
            OSS文件URL
        
        Raises:
            StorageError: 上传失败时抛出异常
        """
        file_size = len(file_data)
        retry_count = 0
        last_error = None
        
        # 生成文件名
        if not filename:
            filename = self._generate_file_name(prefix=subdir)
        
        # 获取OSS对象键
        oss_key = self._get_oss_key(filename, subdir)
        
        while retry_count <= max_retries:
            try:
                start_time = time.time()
                logger.info(
                    f"开始上传文件到OSS: oss_key={oss_key}, "
                    f"size={file_size} bytes, retry_count={retry_count}/{max_retries}"
                )
                
                # 使用线程池执行同步的OSS操作（避免阻塞事件循环）
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    lambda: self.oss_bucket.put_object(
                        oss_key,
                        file_data,
                        headers={'Content-Type': content_type}
                    )
                )
                
                # 检查上传结果
                if result.status != 200:
                    raise StorageError(f"OSS上传失败，状态码: {result.status}")
                
                # 构建文件URL
                # 优先使用配置的OSS_BUCKET_ENDPOINT，如果没有则使用默认格式
                if hasattr(settings, 'oss_bucket_endpoint') and settings.oss_bucket_endpoint:
                    file_url = f"{settings.oss_bucket_endpoint}/{oss_key}"
                else:
                    file_url = f"https://{settings.oss_bucket_name}.{settings.oss_endpoint}/{oss_key}"
                
                duration = time.time() - start_time
                logger.info(
                    f"文件上传OSS成功: oss_key={oss_key}, "
                    f"duration={duration:.2f}s, url={file_url}"
                )
                return file_url
                
            except (OssError, Exception) as e:
                last_error = e
                retry_count += 1
                
                # 判断是否可重试
                is_retryable = self._is_retryable_oss_error(e)
                
                if not is_retryable or retry_count > max_retries:
                    logger.error(
                        f"OSS上传失败（不可重试或已达最大重试次数）: "
                        f"oss_key={oss_key}, error={str(e)}, retry_count={retry_count}",
                        exc_info=True
                    )
                    raise StorageError(f"OSS上传失败: {str(e)}")
                else:
                    # 可重试，等待后重试
                    wait_time = min(2 ** retry_count, 30)  # 指数退避，最多30秒
                    logger.warning(
                        f"OSS上传失败，将重试: oss_key={oss_key}, "
                        f"error={str(e)}, retry_count={retry_count}/{max_retries}, "
                        f"wait_time={wait_time}s"
                    )
                    await asyncio.sleep(wait_time)
        
        # 所有重试都失败
        logger.error(
            f"OSS上传最终失败: oss_key={oss_key}, "
            f"max_retries={max_retries}, last_error={str(last_error)}"
        )
        raise StorageError(f"OSS上传失败（已重试{max_retries}次）: {str(last_error)}")
    
    def _is_retryable_oss_error(self, error: Exception) -> bool:
        """
        判断OSS错误是否可重试
        
        Args:
            error: 异常对象
        
        Returns:
            是否可重试
        """
        # OSS特定的可重试错误
        if isinstance(error, OssError):
            # 网络错误、超时等可重试
            error_code = getattr(error, 'code', '')
            retryable_codes = ['RequestTimeout', 'ConnectionTimeout', 'ServiceUnavailable']
            if error_code in retryable_codes:
                return True
        
        # 检查异常消息中的关键词
        error_str = str(error).lower()
        retryable_keywords = [
            "timeout",
            "connection",
            "network",
            "temporary",
            "503",
            "502",
            "504",
        ]
        
        return any(keyword in error_str for keyword in retryable_keywords)
    
    async def save_to_local(
        self,
        file_data: bytes,
        filename: Optional[str] = None,
        subdir: str = "generated"
    ) -> str:
        """
        保存文件到本地（异步执行，避免阻塞）
        
        Args:
            file_data: 文件二进制数据
            filename: 文件名（可选，不提供则自动生成）
            subdir: 子目录（generated, uploads, fabric, real_person）
        
        Returns:
            本地文件路径
        """
        try:
            # 确定存储目录
            if subdir == "generated":
                storage_dir = settings.storage_generated_path
            elif subdir == "fabric":
                storage_dir = settings.storage_fabric_path
            elif subdir == "real_person":
                storage_dir = settings.storage_real_person_path
            elif subdir == "uploads":
                storage_dir = settings.storage_upload_path  # 向后兼容
            else:
                storage_dir = os.path.join(settings.storage_local_path, subdir)
                os.makedirs(storage_dir, exist_ok=True)
            
            # 生成文件名
            if not filename:
                filename = self._generate_file_name(prefix=subdir)
            
            # 构建完整路径
            file_path = os.path.join(storage_dir, filename)
            
            # 使用线程池执行文件写入（避免阻塞事件循环）
            start_time = time.time()
            file_size = len(file_data)
            logger.info(
                f"开始保存文件到本地: file_path={file_path}, size={file_size} bytes"
            )
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self._write_file_sync(file_path, file_data)
            )
            
            duration = time.time() - start_time
            logger.info(
                f"文件保存本地成功: file_path={file_path}, "
                f"duration={duration:.2f}s, size={file_size} bytes"
            )
            return file_path
            
        except Exception as e:
            logger.error(
                f"保存文件到本地失败: file_path={file_path if 'file_path' in locals() else 'N/A'}, "
                f"error={str(e)}", exc_info=True
            )
            raise StorageError(f"保存文件到本地失败: {str(e)}")
    
    def _write_file_sync(self, file_path: str, file_data: bytes) -> None:
        """
        同步写入文件（在线程池中执行）
        
        Args:
            file_path: 文件路径
            file_data: 文件数据
        """
        with open(file_path, "wb") as f:
            f.write(file_data)
    
    async def upload_and_backup(
        self,
        file_data: bytes,
        filename: Optional[str] = None,
        subdir: str = "generated",
        content_type: str = "image/jpeg",
        backup_local: bool = True,
        fabric_image_name: Optional[str] = None,
        model_type: Optional[str] = None
    ) -> dict:
        """
        上传文件到OSS并本地备份
        
        Args:
            file_data: 文件二进制数据
            filename: 文件名（可选，不提供则自动生成）
            subdir: 子目录（generated 或 uploads）
            content_type: 文件MIME类型
            backup_local: 是否本地备份（默认True）
            fabric_image_name: 成衣图文件名（用于生成自定义文件名）
            model_type: 模特类型（用于生成自定义文件名）
        
        Returns:
            包含oss_url和local_path的字典
        """
        # 如果没有提供filename，使用新的命名规则生成
        if not filename:
            filename = self._generate_file_name(
                prefix=subdir,
                fabric_image_name=fabric_image_name,
                model_type=model_type
            )
        
        result = {
            "oss_url": None,
            "local_path": None,
            "filename": filename
        }
        
        try:
            # 上传到OSS
            result["oss_url"] = await self.upload_to_oss(
                file_data,
                result["filename"],
                subdir,
                content_type
            )
            
            # 本地备份
            if backup_local:
                result["local_path"] = await self.save_to_local(
                    file_data,
                    result["filename"],
                    subdir
                )
            
            logger.info(f"文件上传和备份完成: {result}")
            return result
            
        except Exception as e:
            logger.error(f"文件上传和备份失败: {str(e)}", exc_info=True)
            # 如果OSS上传成功但本地备份失败，仍然返回OSS URL
            if result["oss_url"]:
                logger.warning("OSS上传成功但本地备份失败，继续返回OSS URL")
            raise
    
    async def delete_from_oss(self, oss_key: str) -> bool:
        """
        从OSS删除文件
        
        Args:
            oss_key: OSS对象键
        
        Returns:
            是否删除成功
        """
        try:
            logger.info(f"开始从OSS删除文件: {oss_key}")
            result = self.oss_bucket.delete_object(oss_key)
            
            if result.status == 204:
                logger.info(f"文件从OSS删除成功: {oss_key}")
                return True
            else:
                logger.warning(f"文件从OSS删除失败，状态码: {result.status}")
                return False
                
        except Exception as e:
            logger.error(f"从OSS删除文件失败: {str(e)}", exc_info=True)
            return False
    
    async def delete_from_local(self, file_path: str) -> bool:
        """
        从本地删除文件
        
        Args:
            file_path: 本地文件路径
        
        Returns:
            是否删除成功
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"文件从本地删除成功: {file_path}")
                return True
            else:
                logger.warning(f"文件不存在: {file_path}")
                return False
                
        except Exception as e:
            logger.error(f"从本地删除文件失败: {str(e)}", exc_info=True)
            return False
    
    def get_file_size(self, file_data: bytes) -> int:
        """
        获取文件大小（字节）
        
        Args:
            file_data: 文件二进制数据
        
        Returns:
            文件大小（字节）
        """
        return len(file_data)
    
    def format_file_size(self, size_bytes: int) -> str:
        """
        格式化文件大小
        
        Args:
            size_bytes: 文件大小（字节）
        
        Returns:
            格式化后的文件大小字符串
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"


# 全局存储服务实例
storage_service = StorageService()

