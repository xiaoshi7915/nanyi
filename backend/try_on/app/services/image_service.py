"""
图片处理服务模块
整合AI模型调用和存储服务，处理试衣图片生成流程
"""
import os
import uuid
import asyncio
import time
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from fastapi import UploadFile

from app.config import settings
from app.utils.logger import get_logger
from app.utils.exceptions import (
    ImageProcessingError,
    TaskNotFoundError,
    TaskProcessingError,
    StorageError,
    AIModelError
)
from app.services.storage_service import storage_service
from app.services.db_service import db_service
from app.services.ai_models.base import GenerateParams
from app.services.ai_models.seedream import SeedreamModel
from app.services.ai_models.mock import MockAIModel

# 获取日志记录器
logger = get_logger(__name__)


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"  # 等待中
    PROCESSING = "processing"  # 处理中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败


class Task:
    """任务类，存储任务信息"""
    
    def __init__(
        self,
        task_id: str,
        params: GenerateParams,
        status: TaskStatus = TaskStatus.PENDING,
        fabric_image_filename: Optional[str] = None
    ):
        """
        初始化任务
        
        Args:
            task_id: 任务ID
            params: 生成参数
            status: 任务状态
            fabric_image_filename: 成衣图原始文件名（用于生成结果文件名）
        """
        self.task_id = task_id
        self.params = params
        self.status = status
        self.fabric_image_filename = fabric_image_filename  # 保存成衣图原始文件名
        self.result_image_url: Optional[str] = None
        self.local_path: Optional[str] = None
        self.error_message: Optional[str] = None
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（包含数据库所需的所有字段）"""
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "model_type": self.params.model_type,
            "shot_type": self.params.shot_type,
            "aspect_ratio": self.params.aspect_ratio,
            "style": self.params.style,
            "resolution": self.params.resolution,
            "ai_model_id": self.params.ai_model_id,
            "prompt": self.params.prompt,
            "result_image_url": self.result_image_url,
            "local_path": self.local_path,
            "error_message": self.error_message,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


class ImageService:
    """
    图片处理服务类
    负责处理图片上传、调用AI模型生成、保存结果等
    """
    
    def __init__(self):
        """初始化图片处理服务"""
        # 根据环境变量选择AI模型
        # 如果设置了 USE_MOCK_AI=true，使用Mock模型（测试模式，不调用真实API）
        import os
        use_mock = os.getenv("USE_MOCK_AI", "false").lower() == "true"
        
        if use_mock:
            logger.info("使用Mock AI模型（测试模式，不调用真实API）")
            self.ai_model = MockAIModel()
        else:
            logger.info("使用Seedream AI模型（生产模式）")
            self.ai_model = SeedreamModel()
        
        # 任务存储（内存作为缓存，数据库是主存储）
        self.tasks: Dict[str, Task] = {}
        
        # 数据同步相关
        self._sync_task: Optional[asyncio.Task] = None
        self._sync_started = False
        self._sync_interval_seconds = 300  # 同步间隔：5分钟
        
        # 任务处理队列和并发控制
        self._task_queue: asyncio.Queue = asyncio.Queue()
        self._processing_tasks: Dict[str, asyncio.Task] = {}
        self._max_concurrent_tasks = settings.max_concurrent_tasks
        self._task_semaphore = asyncio.Semaphore(self._max_concurrent_tasks)
        
        # 启动任务处理工作器
        self._worker_started = False
        self._worker_task: Optional[asyncio.Task] = None
        self._worker_restart_count = 0  # 工作器重启次数
        self._worker_last_heartbeat = time.time()  # 工作器最后心跳时间
        
        # 任务清理相关
        self._cleanup_task: Optional[asyncio.Task] = None
        self._cleanup_started = False
        
        # 工作器健康检查相关
        self._health_check_task: Optional[asyncio.Task] = None
        self._health_check_started = False
        
        logger.info(f"图片处理服务初始化完成，最大并发任务数: {self._max_concurrent_tasks}")
    
    async def _read_upload_file(self, file: UploadFile) -> bytes:
        """
        读取上传文件内容
        
        Args:
            file: FastAPI上传文件对象
        
        Returns:
            文件二进制数据
        """
        content = await file.read()
        await file.seek(0)  # 重置文件指针
        return content
    
    async def _prepare_generate_params(
        self,
        fabric_images: List[UploadFile],
        model_type: str,
        shot_type: str,
        aspect_ratio: str,
        style: str,
        resolution: Optional[str] = None,
        ai_model_id: Optional[str] = None,
        real_person_image: Optional[UploadFile] = None,
        prompt: Optional[str] = None,
        seed: Optional[int] = None,
        steps: Optional[int] = None,
        guidance_scale: Optional[float] = None,
        extra_params: Optional[Dict[str, Any]] = None
    ) -> GenerateParams:
        """
        准备生成参数
        
        Args:
            fabric_images: 布料/成衣图片列表
            model_type: 模特类型
            shot_type: 拍摄类型
            aspect_ratio: 图像比例
            style: 风格
            resolution: 分辨率（可选）
            ai_model_id: AI模特ID（可选）
            real_person_image: 真人照片（可选）
            prompt: 自定义提示词（可选）
            seed: 随机种子（可选）
            steps: 生成步数（可选）
            guidance_scale: 引导强度（可选）
            extra_params: 扩展参数（可选）
        
        Returns:
            生成参数对象
        """
        # 读取布料图片
        fabric_images_data = []
        for img in fabric_images:
            img_data = await self._read_upload_file(img)
            fabric_images_data.append(img_data)
        
        # 读取真人照片（如果有）
        real_person_image_data = None
        if real_person_image:
            real_person_image_data = await self._read_upload_file(real_person_image)
        
        # 构建生成参数
        params = GenerateParams(
            fabric_images=fabric_images_data,
            model_type=model_type,
            shot_type=shot_type,
            aspect_ratio=aspect_ratio,
            style=style,
            resolution=resolution,
            ai_model_id=ai_model_id,
            real_person_image=real_person_image_data,
            prompt=prompt,
            seed=seed,
            steps=steps,
            guidance_scale=guidance_scale,
            extra_params=extra_params or {}
        )
        
        return params
    
    async def create_task(
        self,
        fabric_images: List[UploadFile],
        model_type: str,
        shot_type: str,
        aspect_ratio: str,
        style: str = "portrait_photography",
        resolution: Optional[str] = None,
        ai_model_id: Optional[str] = None,
        real_person_image: Optional[UploadFile] = None,
        model_provider: str = "seedream",
        **kwargs
    ) -> str:
        """
        创建试衣生成任务
        
        Args:
            fabric_images: 布料/成衣图片列表
            model_type: 模特类型
            shot_type: 拍摄类型
            aspect_ratio: 图像比例
            style: 风格
            resolution: 分辨率（可选）
            ai_model_id: AI模特ID（可选）
            real_person_image: 真人照片（可选）
            model_provider: 模型提供商（默认seedream）
            **kwargs: 其他参数（prompt, seed等）
        
        Returns:
            任务ID
        """
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 准备生成参数
        params = await self._prepare_generate_params(
            fabric_images=fabric_images,
            model_type=model_type,
            shot_type=shot_type,
            aspect_ratio=aspect_ratio,
            style=style,
            resolution=resolution,
            ai_model_id=ai_model_id,
            real_person_image=real_person_image,
            **kwargs
        )
        
        # 获取第一张成衣图的原始文件名（用于生成结果文件名）
        fabric_image_filename = None
        if fabric_images and len(fabric_images) > 0:
            # 获取第一张成衣图的文件名（不含扩展名）
            original_filename = fabric_images[0].filename
            if original_filename:
                # 去除扩展名，只保留文件名
                fabric_image_filename = os.path.splitext(original_filename)[0]
        
        # 创建任务
        task = Task(
            task_id=task_id,
            params=params,
            status=TaskStatus.PENDING,
            fabric_image_filename=fabric_image_filename
        )
        
        # 保存任务到内存
        self.tasks[task_id] = task
        
        # 保存任务到数据库
        try:
            task_dict = task.to_dict()
            db_service.save_task(task_dict)
        except Exception as e:
            logger.warning(f"保存任务到数据库失败（继续使用内存存储）: {str(e)}")
        
        logger.info(
            f"创建试衣生成任务: task_id={task_id}, model_type={model_type}, "
            f"shot_type={shot_type}, fabric_images_count={len(fabric_images)}"
        )
        
        # 启动任务处理工作器（如果尚未启动）
        if not self._worker_started:
            self._start_worker_with_monitoring()
        
        # 启动工作器健康检查（如果尚未启动）
        if not self._health_check_started:
            try:
                loop = asyncio.get_event_loop()
                loop.create_task(self._start_health_check())
                self._health_check_started = True
            except RuntimeError:
                asyncio.ensure_future(self._start_health_check())
                self._health_check_started = True
        
        # 启动任务清理器（如果尚未启动）
        if not self._cleanup_started:
            try:
                loop = asyncio.get_event_loop()
                loop.create_task(self._start_task_cleanup())
                self._cleanup_started = True
            except RuntimeError:
                asyncio.ensure_future(self._start_task_cleanup())
                self._cleanup_started = True
        
        # 启动数据同步器（如果尚未启动）
        if not self._sync_started:
            try:
                loop = asyncio.get_event_loop()
                loop.create_task(self._start_data_sync())
                self._sync_started = True
            except RuntimeError:
                asyncio.ensure_future(self._start_data_sync())
                self._sync_started = True
        
        # 将任务加入队列
        await self._task_queue.put(task_id)
        
        return task_id
    
    def _start_worker_with_monitoring(self):
        """
        启动任务处理工作器（带监控和自动重启）
        """
        try:
            # 获取当前事件循环
            loop = asyncio.get_event_loop()
            self._worker_task = loop.create_task(self._start_task_worker())
            self._worker_started = True
        except RuntimeError:
            # 如果没有事件循环，创建一个新的
            self._worker_task = asyncio.ensure_future(self._start_task_worker())
            self._worker_started = True
    
    async def _start_task_worker(self):
        """
        启动任务处理工作器
        从队列中取出任务并处理
        """
        logger.info("任务处理工作器已启动")
        try:
            while True:
                try:
                    # 更新心跳时间
                    self._worker_last_heartbeat = time.time()
                    
                    # 从队列中获取任务ID（阻塞等待，设置超时以便定期更新心跳）
                    try:
                        task_id = await asyncio.wait_for(
                            self._task_queue.get(),
                            timeout=30.0  # 30秒超时，用于定期更新心跳
                        )
                    except asyncio.TimeoutError:
                        # 超时是正常的，继续循环更新心跳
                        continue
                    
                    # 使用信号量控制并发数
                    async with self._task_semaphore:
                        # 创建处理任务
                        process_task = asyncio.create_task(
                            self._process_task_with_retry(task_id)
                        )
                        self._processing_tasks[task_id] = process_task
                        
                        # 等待任务完成（但不阻塞其他任务）
                        try:
                            await process_task
                        finally:
                            # 清理已完成的任务
                            self._processing_tasks.pop(task_id, None)
                            self._task_queue.task_done()
                            
                except asyncio.CancelledError:
                    # 工作器被取消，正常退出
                    logger.info("任务处理工作器被取消")
                    raise
                except Exception as e:
                    logger.error(f"任务处理工作器错误: {str(e)}", exc_info=True)
                    await asyncio.sleep(1)  # 错误后等待1秒再继续
        except Exception as e:
            # 工作器异常退出
            logger.error(f"任务处理工作器异常退出: {str(e)}", exc_info=True)
            self._worker_started = False
            # 如果启用自动重启，则重启工作器
            if settings.worker_restart_on_failure:
                if settings.worker_max_restart_attempts == 0 or \
                   self._worker_restart_count < settings.worker_max_restart_attempts:
                    self._worker_restart_count += 1
                    logger.warning(
                        f"工作器将自动重启 (第{self._worker_restart_count}次重启)"
                    )
                    await asyncio.sleep(5)  # 等待5秒后重启
                    self._start_worker_with_monitoring()
                else:
                    logger.error(
                        f"工作器已达到最大重启次数 ({settings.worker_max_restart_attempts})，停止重启"
                    )
            raise
    
    async def _process_task_with_retry(self, task_id: str, max_retries: int = 3) -> None:
        """
        处理任务（带重试机制）
        
        Args:
            task_id: 任务ID
            max_retries: 最大重试次数
        """
        task = self.tasks.get(task_id)
        if not task:
            logger.error(f"任务不存在: {task_id}")
            return
        
        retry_count = 0
        last_error = None
        
        while retry_count <= max_retries:
            try:
                # 更新任务状态为处理中
                task.status = TaskStatus.PROCESSING
                task.updated_at = datetime.now()
                
                start_time = time.time()
                logger.info(
                    f"开始处理任务: task_id={task_id}, "
                    f"retry_count={retry_count}/{max_retries}, "
                    f"model_type={task.params.model_type}, shot_type={task.params.shot_type}"
                )
                
                # 调用AI模型生成图片
                ai_start_time = time.time()
                image_data = await self.ai_model.generate(task.params)
                ai_duration = time.time() - ai_start_time
                logger.info(
                    f"AI模型生成完成: task_id={task_id}, "
                    f"duration={ai_duration:.2f}s, image_size={len(image_data)} bytes"
                )
                
                # 保存生成的图片到OSS和本地
                # 使用新命名规则：布料成衣图名+AI/真人+时间戳
                storage_start_time = time.time()
                result = await storage_service.upload_and_backup(
                    file_data=image_data,
                    subdir="generated",
                    content_type="image/jpeg",
                    backup_local=True,
                    fabric_image_name=task.fabric_image_filename,  # 传递成衣图文件名
                    model_type=task.params.model_type  # 传递模特类型
                )
                logger.info(f"生成文件名: {result['filename']} (基于成衣图: {task.fabric_image_filename}, 模特类型: {task.params.model_type})")
                storage_duration = time.time() - storage_start_time
                logger.info(
                    f"存储服务完成: task_id={task_id}, "
                    f"duration={storage_duration:.2f}s, "
                    f"oss_url={result.get('oss_url', 'N/A')}"
                )
                
                # 更新任务结果
                task.result_image_url = result["oss_url"]
                task.local_path = result["local_path"]
                task.status = TaskStatus.COMPLETED
                task.updated_at = datetime.now()
                
                # 更新数据库（数据库是主存储）
                try:
                    task_dict = task.to_dict()
                    db_service.save_task(task_dict)
                    logger.debug(f"任务状态已同步到数据库: task_id={task_id}")
                except Exception as e:
                    logger.warning(f"更新任务到数据库失败: {str(e)}")
                
                total_duration = time.time() - start_time
                logger.info(
                    f"任务处理完成: task_id={task_id}, "
                    f"total_duration={total_duration:.2f}s, "
                    f"image_url={task.result_image_url}, "
                    f"local_path={task.local_path}"
                )
                return  # 成功，退出重试循环
                
            except (AIModelError, StorageError) as e:
                # 业务异常，判断是否可重试
                last_error = e
                retry_count += 1
                
                # 判断是否可重试（网络错误、超时等可重试）
                is_retryable = self._is_retryable_error(e)
                
                if not is_retryable or retry_count > max_retries:
                    # 不可重试或达到最大重试次数
                    task.status = TaskStatus.FAILED
                    task.error_message = str(e)
                    task.updated_at = datetime.now()
                    # 更新数据库（数据库是主存储）
                    try:
                        task_dict = task.to_dict()
                        db_service.save_task(task_dict)
                        logger.debug(f"任务失败状态已同步到数据库: task_id={task_id}")
                    except Exception as e:
                        logger.warning(f"更新任务到数据库失败: {str(e)}")
                    logger.error(
                        f"任务处理失败（不可重试或已达最大重试次数）: "
                        f"task_id={task_id}, error={str(e)}, retry_count={retry_count}"
                    )
                    return
                else:
                    # 可重试，等待后重试
                    wait_time = min(2 ** retry_count, 60)  # 指数退避，最多60秒
                    logger.warning(
                        f"任务处理失败，将重试: task_id={task_id}, "
                        f"error={str(e)}, retry_count={retry_count}/{max_retries}, "
                        f"wait_time={wait_time}s"
                    )
                    await asyncio.sleep(wait_time)
                    
            except Exception as e:
                # 未知异常，判断是否可重试
                last_error = e
                retry_count += 1
                
                is_retryable = self._is_retryable_error(e)
                
                if not is_retryable or retry_count > max_retries:
                    task.status = TaskStatus.FAILED
                    task.error_message = f"任务处理失败: {str(e)}"
                    task.updated_at = datetime.now()
                    # 更新数据库（数据库是主存储）
                    try:
                        task_dict = task.to_dict()
                        db_service.save_task(task_dict)
                        logger.debug(f"任务失败状态已同步到数据库: task_id={task_id}")
                    except Exception as e:
                        logger.warning(f"更新任务到数据库失败: {str(e)}")
                    logger.error(
                        f"任务处理失败（未知异常）: task_id={task_id}, "
                        f"error={str(e)}, retry_count={retry_count}", exc_info=True
                    )
                    raise TaskProcessingError(
                        f"任务处理失败: {str(e)}", 
                        detail={"task_id": task_id, "retry_count": retry_count}
                    )
                else:
                    wait_time = min(2 ** retry_count, 60)
                    logger.warning(
                        f"任务处理失败（未知异常），将重试: task_id={task_id}, "
                        f"error={str(e)}, retry_count={retry_count}/{max_retries}, "
                        f"wait_time={wait_time}s", exc_info=True
                    )
                    await asyncio.sleep(wait_time)
        
        # 所有重试都失败
        task.status = TaskStatus.FAILED
        task.error_message = f"任务处理失败（已重试{max_retries}次）: {str(last_error)}"
        task.updated_at = datetime.now()
        logger.error(
            f"任务处理最终失败: task_id={task_id}, "
            f"max_retries={max_retries}, last_error={str(last_error)}"
        )
    
    def _is_retryable_error(self, error: Exception) -> bool:
        """
        判断错误是否可重试
        
        Args:
            error: 异常对象
        
        Returns:
            是否可重试
        """
        # 网络错误、超时错误等可重试
        retryable_errors = (
            TimeoutError,
            ConnectionError,
            OSError,
        )
        
        # 检查异常类型
        if isinstance(error, retryable_errors):
            return True
        
        # 检查异常消息中的关键词
        error_str = str(error).lower()
        retryable_keywords = [
            "timeout",
            "connection",
            "network",
            "temporary",
            "retry",
            "503",  # 服务不可用
            "502",  # 网关错误
            "504",  # 网关超时
        ]
        
        return any(keyword in error_str for keyword in retryable_keywords)
    
    async def _process_task(self, task_id: str) -> None:
        """
        处理任务（异步执行）- 保持向后兼容
        实际调用带重试的版本
        
        Args:
            task_id: 任务ID
        """
        await self._process_task_with_retry(task_id)
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """
        获取任务信息（优先从数据库读取，内存作为缓存）
        
        Args:
            task_id: 任务ID
        
        Returns:
            任务对象，如果不存在返回None
        """
        # 优先从数据库读取
        try:
            task_dict = db_service.get_task(task_id)
            if task_dict:
                # 同步到内存缓存
                self._sync_task_to_cache(task_dict)
                # 返回内存中的任务对象（如果存在）
                return self.tasks.get(task_id)
        except Exception as e:
            logger.warning(f"从数据库获取任务失败: {str(e)}")
        
        # 如果数据库中没有，返回内存缓存
        return self.tasks.get(task_id)
    
    def _sync_task_to_cache(self, task_dict: Dict[str, Any]) -> None:
        """
        将数据库中的任务同步到内存缓存
        
        Args:
            task_dict: 任务字典
        """
        task_id = task_dict.get("task_id")
        if not task_id:
            return
        
        # 如果内存中已有任务，更新它
        if task_id in self.tasks:
            task = self.tasks[task_id]
            # 更新任务状态（从数据库同步）
            task.status = TaskStatus(task_dict.get("status", "pending"))
            task.result_image_url = task_dict.get("result_image_url")
            task.local_path = task_dict.get("local_path")
            task.error_message = task_dict.get("error_message")
            # 注意：不更新created_at和updated_at，保持数据库的值
            if task_dict.get("created_at"):
                task.created_at = task_dict.get("created_at")
            if task_dict.get("updated_at"):
                task.updated_at = task_dict.get("updated_at")
        else:
            # 如果内存中没有，创建一个新的任务对象（但需要从字典重建params）
            # 注意：这里无法完全重建params，所以只创建基本任务对象
            # 实际使用中，应该优先从数据库读取
            logger.debug(f"任务不在内存缓存中，无法完全重建: task_id={task_id}")
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        获取任务状态（优先从数据库读取，内存作为缓存）
        
        Args:
            task_id: 任务ID
        
        Returns:
            任务状态字典
        
        Raises:
            TaskNotFoundError: 任务不存在时抛出异常
        """
        # 优先从数据库读取（数据库是主存储）
        try:
            task_dict = db_service.get_task(task_id)
            if task_dict:
                # 同步到内存缓存
                self._sync_task_to_cache(task_dict)
                logger.debug(f"从数据库获取任务状态: task_id={task_id}")
                return task_dict
        except Exception as e:
            logger.warning(f"从数据库获取任务状态失败: {str(e)}")
        
        # 如果数据库中没有，尝试从内存缓存获取
        task = self.tasks.get(task_id)
        if task:
            logger.debug(f"从内存缓存获取任务状态: task_id={task_id}")
            return task.to_dict()
        
        # 都不存在，抛出异常
        raise TaskNotFoundError(f"任务不存在: {task_id}", detail={"task_id": task_id})
    
    def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        列出任务
        
        Args:
            status: 任务状态过滤（可选）
            limit: 返回数量限制
        
        Returns:
            任务列表
        """
        tasks = list(self.tasks.values())
        
        # 按状态过滤
        if status:
            tasks = [t for t in tasks if t.status == status]
        
        # 按创建时间排序（最新的在前）
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        
        # 限制数量
        tasks = tasks[:limit]
        
        return [task.to_dict() for task in tasks]
    
    def delete_task(self, task_id: str) -> bool:
        """
        删除任务
        
        Args:
            task_id: 任务ID
        
        Returns:
            是否删除成功
        """
        if task_id in self.tasks:
            del self.tasks[task_id]
            logger.info(f"删除任务: {task_id}")
            return True
        return False
    
    async def _start_task_cleanup(self):
        """
        启动任务清理器
        定期清理已完成或失败的任务，防止内存泄漏
        """
        logger.info("任务清理器已启动")
        from datetime import timedelta
        
        while True:
            try:
                # 等待清理间隔
                await asyncio.sleep(settings.task_cleanup_interval_seconds)
                
                # 计算清理时间阈值
                cutoff_time = datetime.now() - timedelta(hours=settings.task_retention_hours)
                
                # 查找需要清理的任务（已完成或失败，且超过保留时间）
                tasks_to_remove = []
                for task_id, task in self.tasks.items():
                    # 只清理已完成或失败的任务
                    if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
                        # 检查任务更新时间是否超过保留时间
                        if task.updated_at < cutoff_time:
                            tasks_to_remove.append(task_id)
                
                # 执行清理
                if tasks_to_remove:
                    for task_id in tasks_to_remove:
                        del self.tasks[task_id]
                    logger.info(
                        f"任务清理完成: 清理了{len(tasks_to_remove)}个任务 "
                        f"(保留时间: {settings.task_retention_hours}小时)"
                    )
                else:
                    logger.debug("任务清理检查完成: 无需清理的任务")
                    
            except Exception as e:
                logger.error(f"任务清理器错误: {str(e)}", exc_info=True)
                await asyncio.sleep(60)  # 错误后等待1分钟再继续
    
    async def _start_health_check(self):
        """
        启动工作器健康检查
        定期检查工作器状态，如果工作器异常则自动重启
        """
        logger.info("工作器健康检查已启动")
        
        while True:
            try:
                # 等待健康检查间隔
                await asyncio.sleep(settings.worker_health_check_interval_seconds)
                
                # 检查工作器是否运行
                worker_alive = (
                    self._worker_started and
                    self._worker_task is not None and
                    not self._worker_task.done()
                )
                
                # 检查心跳时间（如果工作器运行但长时间没有心跳，可能卡住了）
                heartbeat_timeout = settings.worker_health_check_interval_seconds * 3
                heartbeat_ok = (
                    time.time() - self._worker_last_heartbeat < heartbeat_timeout
                )
                
                # 获取队列长度和正在处理的任务数
                queue_size = self._task_queue.qsize()
                processing_count = len(self._processing_tasks)
                
                # 记录健康状态
                logger.debug(
                    f"工作器健康检查: worker_alive={worker_alive}, "
                    f"heartbeat_ok={heartbeat_ok}, queue_size={queue_size}, "
                    f"processing_count={processing_count}, "
                    f"restart_count={self._worker_restart_count}"
                )
                
                # 如果工作器不存活或心跳超时，尝试重启
                if not worker_alive or not heartbeat_ok:
                    if settings.worker_restart_on_failure:
                        if settings.worker_max_restart_attempts == 0 or \
                           self._worker_restart_count < settings.worker_max_restart_attempts:
                            logger.warning(
                                f"工作器异常检测到 (alive={worker_alive}, heartbeat_ok={heartbeat_ok})，"
                                f"将自动重启 (第{self._worker_restart_count + 1}次)"
                            )
                            # 取消旧的工作器任务（如果存在）
                            if self._worker_task and not self._worker_task.done():
                                self._worker_task.cancel()
                            # 重置状态并重启
                            self._worker_started = False
                            self._worker_restart_count += 1
                            await asyncio.sleep(2)  # 等待2秒
                            self._start_worker_with_monitoring()
                        else:
                            logger.error(
                                f"工作器异常但已达到最大重启次数 "
                                f"({settings.worker_max_restart_attempts})，停止重启"
                            )
                    else:
                        logger.warning(
                            f"工作器异常检测到但自动重启已禁用 "
                            f"(alive={worker_alive}, heartbeat_ok={heartbeat_ok})"
                        )
                    
            except Exception as e:
                logger.error(f"工作器健康检查错误: {str(e)}", exc_info=True)
                await asyncio.sleep(60)  # 错误后等待1分钟再继续
    
    async def _start_data_sync(self):
        """
        启动数据同步器
        定期从数据库同步任务状态到内存缓存，确保数据一致性
        """
        logger.info("数据同步器已启动")
        
        while True:
            try:
                # 等待同步间隔
                await asyncio.sleep(self._sync_interval_seconds)
                
                # 同步内存中的任务到数据库（确保数据库是最新的）
                sync_count = 0
                for task_id, task in list(self.tasks.items()):
                    try:
                        # 将内存中的任务状态同步到数据库
                        task_dict = task.to_dict()
                        db_service.save_task(task_dict)
                        sync_count += 1
                    except Exception as e:
                        logger.warning(f"同步任务到数据库失败: task_id={task_id}, error={str(e)}")
                
                if sync_count > 0:
                    logger.debug(f"数据同步完成: 同步了{sync_count}个任务到数据库")
                
                # 从数据库同步最新状态到内存（对于已完成/失败的任务）
                try:
                    # 获取内存中所有任务的ID
                    memory_task_ids = set(self.tasks.keys())
                    
                    # 从数据库获取这些任务的最新状态
                    for task_id in memory_task_ids:
                        try:
                            task_dict = db_service.get_task(task_id)
                            if task_dict:
                                # 同步到内存缓存
                                self._sync_task_to_cache(task_dict)
                        except Exception as e:
                            logger.debug(f"从数据库同步任务失败: task_id={task_id}, error={str(e)}")
                    
                    logger.debug("从数据库同步任务状态到内存缓存完成")
                except Exception as e:
                    logger.warning(f"从数据库同步任务状态失败: {str(e)}")
                    
            except Exception as e:
                logger.error(f"数据同步器错误: {str(e)}", exc_info=True)
                await asyncio.sleep(60)  # 错误后等待1分钟再继续
    
    def get_worker_status(self) -> Dict[str, Any]:
        """
        获取工作器状态信息
        
        Returns:
            工作器状态字典
        """
        worker_alive = (
            self._worker_started and
            self._worker_task is not None and
            not self._worker_task.done()
        )
        
        heartbeat_age = time.time() - self._worker_last_heartbeat
        
        return {
            "worker_alive": worker_alive,
            "worker_started": self._worker_started,
            "heartbeat_age_seconds": heartbeat_age,
            "queue_size": self._task_queue.qsize(),
            "processing_count": len(self._processing_tasks),
            "max_concurrent_tasks": self._max_concurrent_tasks,
            "restart_count": self._worker_restart_count,
            "tasks_in_memory": len(self.tasks)
        }


# 全局图片处理服务实例
image_service = ImageService()

