#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片处理服务模块（适配版）
整合AI模型调用和存储服务，处理试衣图片生成流程，使用主项目的配置和服务
"""
import os
import uuid
import asyncio
import time
import threading
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from enum import Enum

from backend.config.config import Config
from backend.utils.logger import logger
from backend.services.try_on_db_service import TryOnDatabaseService
from backend.services.try_on_storage_service import TryOnStorageService
from backend.services.try_on_ai_service import TryOnSeedreamModel, GenerateParams

# 导入异常类
try:
    from backend.exceptions import (
        ValidationError,
        NotFoundError as TaskNotFoundError,
        ServiceError as TaskProcessingError,
        ServiceError as StorageError,
        ServiceError as AIModelError,
        ServiceError as ImageProcessingError,
    )
except ImportError:
    # 如果主项目没有这些异常，创建简单的异常类
    class ValidationError(Exception):
        """参数验证错误"""
        pass
    
    class TaskNotFoundError(Exception):
        """任务不存在错误"""
        pass
    
    class TaskProcessingError(Exception):
        """任务处理错误"""
        pass
    
    class StorageError(Exception):
        """存储服务错误"""
        pass
    
    class AIModelError(Exception):
        """AI模型服务错误"""
        pass
    
    class ImageProcessingError(Exception):
        """图片处理错误"""
        pass


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


class TryOnImageService:
    """
    图片处理服务类（适配版）
    负责处理图片上传、调用AI模型生成、保存结果等
    使用主项目的配置和服务，在后台线程中运行异步任务队列
    """
    
    def __init__(self, config: Config, app=None):
        """
        初始化图片处理服务
        
        Args:
            config: 主项目的配置对象
            app: Flask 应用实例（用于数据库上下文）
        """
        self.config = config
        self.app = app  # 保存 Flask 应用实例，用于在后台线程中创建应用上下文
        
        # 根据环境变量选择AI模型
        # 如果设置了 USE_MOCK_AI=true，使用Mock模型（测试模式，不调用真实API）
        use_mock = os.getenv("USE_MOCK_AI", "false").lower() == "true"
        
        if use_mock:
            logger.info("使用Mock AI模型（测试模式，不调用真实API）")
            # 注意：Mock模型需要单独实现，这里先使用真实模型
            self.ai_model = TryOnSeedreamModel(config)
        else:
            logger.info("使用Seedream AI模型（生产模式）")
            self.ai_model = TryOnSeedreamModel(config)
        
        # 初始化服务依赖
        self.db_service = TryOnDatabaseService(config)
        self.storage_service = TryOnStorageService(config)
        
        # 任务存储（内存作为缓存，数据库是主存储）
        self.tasks: Dict[str, Task] = {}
        
        # 任务处理队列和并发控制（在后台线程的事件循环中运行）
        self._task_queue: Optional[asyncio.Queue] = None  # 将在后台线程中初始化
        self._processing_tasks: Dict[str, asyncio.Task] = {}
        self._max_concurrent_tasks = config.MAX_CONCURRENT_TASKS
        self._task_semaphore: Optional[asyncio.Semaphore] = None  # 将在后台线程中初始化
        
        # 后台线程和事件循环
        self._worker_thread: Optional[threading.Thread] = None
        self._worker_loop: Optional[asyncio.AbstractEventLoop] = None
        self._worker_started = False
        self._worker_restart_count = 0  # 工作器重启次数
        self._worker_last_heartbeat = time.time()  # 工作器最后心跳时间
        self._shutdown_event = threading.Event()
        
        # 任务清理相关
        self._cleanup_started = False
        
        # 工作器健康检查相关
        self._health_check_started = False
        
        # 数据同步相关
        self._sync_started = False
        self._sync_interval_seconds = 300  # 同步间隔：5分钟
        
        logger.info(f"TryOn图片处理服务初始化完成，最大并发任务数: {self._max_concurrent_tasks}")
    
    def _read_upload_file(self, file) -> bytes:
        """
        读取上传文件内容（适配 Flask 的 request.files）
        
        Args:
            file: Flask 上传文件对象（werkzeug.datastructures.FileStorage）
        
        Returns:
            文件二进制数据
        """
        # Flask 的文件对象可以直接读取
        file.seek(0)  # 重置文件指针
        content = file.read()
        file.seek(0)  # 再次重置，以便后续使用
        return content
    
    def _prepare_generate_params(
        self,
        fabric_images: List,
        model_type: str,
        shot_type: str,
        aspect_ratio: str,
        style: str,
        resolution: Optional[str] = None,
        ai_model_id: Optional[str] = None,
        real_person_image: Optional[Any] = None,
        prompt: Optional[str] = None,
        seed: Optional[int] = None,
        steps: Optional[int] = None,
        guidance_scale: Optional[float] = None,
        extra_params: Optional[Dict[str, Any]] = None
    ) -> GenerateParams:
        """
        准备生成参数（同步版本，适配 Flask）
        
        Args:
            fabric_images: 布料/成衣图片列表（Flask FileStorage 对象）
            model_type: 模特类型
            shot_type: 拍摄类型
            aspect_ratio: 图像比例
            style: 风格
            resolution: 分辨率（可选）
            ai_model_id: AI模特ID（可选）
            real_person_image: 真人照片（可选，Flask FileStorage 对象）
            prompt: 自定义提示词（可选）
            seed: 随机种子（可选）
            steps: 生成步数（可选）
            guidance_scale: 引导强度（可选）
            extra_params: 扩展参数（可选）
        
        Returns:
            生成参数对象
        """
        # 读取布料图片（同步读取）
        fabric_images_data = []
        for img in fabric_images:
            img_data = self._read_upload_file(img)
            fabric_images_data.append(img_data)
        
        # 读取真人照片（如果有）
        real_person_image_data = None
        if real_person_image:
            real_person_image_data = self._read_upload_file(real_person_image)
        
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
    
    def create_task(
        self,
        fabric_images: List,
        model_type: str,
        shot_type: str,
        aspect_ratio: str,
        style: str = "portrait_photography",
        resolution: Optional[str] = None,
        ai_model_id: Optional[str] = None,
        real_person_image: Optional[Any] = None,
        model_provider: str = "seedream",
        **kwargs
    ) -> str:
        """
        创建试衣生成任务（同步方法，适配 Flask）
        
        Args:
            fabric_images: 布料/成衣图片列表（Flask FileStorage 对象）
            model_type: 模特类型
            shot_type: 拍摄类型
            aspect_ratio: 图像比例
            style: 风格
            resolution: 分辨率（可选）
            ai_model_id: AI模特ID（可选）
            real_person_image: 真人照片（可选，Flask FileStorage 对象）
            model_provider: 模型提供商（默认seedream）
            **kwargs: 其他参数（prompt, seed等）
        
        Returns:
            任务ID
        """
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 准备生成参数（同步）
        params = self._prepare_generate_params(
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
            # 在 Flask 应用上下文中执行数据库操作
            if self.app:
                with self.app.app_context():
                    self.db_service.save_task(task_dict)
            else:
                from flask import has_app_context, current_app
                if has_app_context():
                    self.db_service.save_task(task_dict)
                else:
                    logger.warning(f"无法获取 Flask 应用上下文，任务将仅保存在内存中: task_id={task_id}")
        except Exception as e:
            logger.warning(f"保存任务到数据库失败（继续使用内存存储）: {str(e)}")
        
        logger.info(
            f"创建试衣生成任务: task_id={task_id}, model_type={model_type}, "
            f"shot_type={shot_type}, fabric_images_count={len(fabric_images)}"
        )
        
        # 启动任务处理工作器（如果尚未启动）
        if not self._worker_started:
            self._start_worker_thread()
        
        # 将任务加入队列（在后台线程的事件循环中）
        self._add_task_to_queue(task_id)
        
        return task_id
    
    def _start_worker_thread(self):
        """
        启动任务处理工作器线程
        在后台线程中运行 asyncio 事件循环
        """
        def worker_thread_func():
            """工作器线程函数"""
            try:
                # 创建新的事件循环（每个线程有自己的事件循环）
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                self._worker_loop = loop
                
                # 初始化队列和信号量
                self._task_queue = asyncio.Queue()
                self._task_semaphore = asyncio.Semaphore(self._max_concurrent_tasks)
                
                # 启动工作器任务
                loop.create_task(self._start_task_worker())
                
                # 启动健康检查
                loop.create_task(self._start_health_check())
                
                # 启动任务清理器
                loop.create_task(self._start_task_cleanup())
                
                # 启动数据同步器
                loop.create_task(self._start_data_sync())
                
                # 运行事件循环直到关闭
                loop.run_until_complete(self._wait_for_shutdown())
                
            except Exception as e:
                logger.error(f"工作器线程异常: {str(e)}", exc_info=True)
            finally:
                # 清理
                if self._worker_loop:
                    self._worker_loop.close()
                self._worker_started = False
        
        # 启动后台线程
        self._worker_thread = threading.Thread(
            target=worker_thread_func,
            name="try_on_worker",
            daemon=True
        )
        self._worker_thread.start()
        self._worker_started = True
        logger.info("任务处理工作器线程已启动")
    
    async def _wait_for_shutdown(self):
        """等待关闭信号"""
        while not self._shutdown_event.is_set():
            await asyncio.sleep(1)
    
    def _add_task_to_queue(self, task_id: str):
        """
        将任务添加到队列（在后台线程的事件循环中）
        
        Args:
            task_id: 任务ID
        """
        if self._worker_loop and not self._worker_loop.is_closed():
            # 在后台线程的事件循环中执行
            asyncio.run_coroutine_threadsafe(
                self._task_queue.put(task_id),
                self._worker_loop
            )
        else:
            logger.warning(f"工作器事件循环未启动，无法添加任务到队列: {task_id}")
    
    async def _start_task_worker(self):
        """
        启动任务处理工作器
        从队列中取出任务并处理
        """
        logger.info("任务处理工作器已启动")
        try:
            while not self._shutdown_event.is_set():
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
            if self.config.WORKER_RESTART_ON_FAILURE:
                if self.config.WORKER_MAX_RESTART_ATTEMPTS == 0 or \
                   self._worker_restart_count < self.config.WORKER_MAX_RESTART_ATTEMPTS:
                    self._worker_restart_count += 1
                    logger.warning(
                        f"工作器将自动重启 (第{self._worker_restart_count}次重启)"
                    )
                    await asyncio.sleep(5)  # 等待5秒后重启
                    # 注意：这里不能直接调用 _start_worker_thread，因为我们在事件循环中
                    # 应该通过主线程重启
                else:
                    logger.error(
                        f"工作器已达到最大重启次数 ({self.config.WORKER_MAX_RESTART_ATTEMPTS})，停止重启"
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
                result = await self.storage_service.upload_and_backup(
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
                task.local_path = result["local_path"]
                
                # #region agent log
                with open('/opt/hanfu/products/.cursor/debug.log', 'a') as f:
                    import json
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"D","location":"try_on_image_service.py:543","message":"存储结果-BEFORE路径转换","data":{"task_id":task_id,"local_path":task.local_path,"oss_url":result.get("oss_url")},"timestamp":int(time.time()*1000)}) + '\n')
                # #endregion
                
                # 如果本地路径在前端文件夹下，转换为前端可访问的 URL
                # 优先使用本地路径（如果在前端文件夹下），否则使用 OSS URL
                if task.local_path:
                    # 获取项目根目录
                    current_file = os.path.abspath(__file__)
                    # backend/services/try_on_image_service.py -> backend -> 项目根目录
                    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
                    frontend_images_path = os.path.join(project_root, 'frontend', 'static', 'images')
                    frontend_images_path = os.path.abspath(frontend_images_path)
                    local_path_abs = os.path.abspath(task.local_path)
                    
                    # #region agent log
                    with open('/opt/hanfu/products/.cursor/debug.log', 'a') as f:
                        import json
                        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"D","location":"try_on_image_service.py:556","message":"路径转换检查","data":{"task_id":task_id,"local_path_abs":local_path_abs,"frontend_images_path":frontend_images_path,"starts_with":local_path_abs.startswith(frontend_images_path)},"timestamp":int(time.time()*1000)}) + '\n')
                    # #endregion
                    
                    if local_path_abs.startswith(frontend_images_path):
                        # 计算相对路径（相对于 frontend/static/images）
                        relative_path = os.path.relpath(local_path_abs, frontend_images_path)
                        # 转换为前端可访问的 URL（使用正斜杠）
                        task.result_image_url = f"/static/images/{relative_path.replace(os.sep, '/')}"
                        logger.info(f"使用前端本地路径作为结果URL: {task.result_image_url} (本地路径: {task.local_path})")
                        
                        # #region agent log
                        with open('/opt/hanfu/products/.cursor/debug.log', 'a') as f:
                            import json
                            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"D","location":"try_on_image_service.py:561","message":"路径转换成功-前端路径","data":{"task_id":task_id,"result_image_url":task.result_image_url,"relative_path":relative_path},"timestamp":int(time.time()*1000)}) + '\n')
                        # #endregion
                    else:
                        # 不在前端文件夹下，使用 OSS URL
                        task.result_image_url = result["oss_url"]
                        logger.info(f"使用OSS URL作为结果URL: {task.result_image_url}")
                        
                        # #region agent log
                        with open('/opt/hanfu/products/.cursor/debug.log', 'a') as f:
                            import json
                            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"D","location":"try_on_image_service.py:565","message":"路径转换-使用OSS","data":{"task_id":task_id,"result_image_url":task.result_image_url},"timestamp":int(time.time()*1000)}) + '\n')
                        # #endregion
                else:
                    # 没有本地路径，使用 OSS URL
                    task.result_image_url = result["oss_url"]
                    
                    # #region agent log
                    with open('/opt/hanfu/products/.cursor/debug.log', 'a') as f:
                        import json
                        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"D","location":"try_on_image_service.py:568","message":"路径转换-无本地路径使用OSS","data":{"task_id":task_id,"result_image_url":task.result_image_url},"timestamp":int(time.time()*1000)}) + '\n')
                    # #endregion
                
                task.status = TaskStatus.COMPLETED
                task.updated_at = datetime.now()
                
                # #region agent log
                with open('/opt/hanfu/products/.cursor/debug.log', 'a') as f:
                    import json
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":"try_on_image_service.py:575","message":"任务完成-BEFORE数据库保存","data":{"task_id":task_id,"status":task.status.value,"result_image_url":task.result_image_url,"local_path":task.local_path},"timestamp":int(time.time()*1000)}) + '\n')
                # #endregion
                
                # 更新数据库（数据库是主存储）
                # 在后台线程中需要使用 Flask 应用上下文
                try:
                    task_dict = task.to_dict()
                    
                    # #region agent log
                    with open('/opt/hanfu/products/.cursor/debug.log', 'a') as f:
                        import json
                        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":"try_on_image_service.py:580","message":"to_dict结果-BEFORE保存","data":{"task_id":task_id,"task_dict_result_image_url":task_dict.get("result_image_url"),"task_dict_local_path":task_dict.get("local_path"),"task_dict_status":task_dict.get("status")},"timestamp":int(time.time()*1000)}) + '\n')
                    # #endregion
                    
                    # 在 Flask 应用上下文中执行数据库操作
                    if self.app:
                        with self.app.app_context():
                            save_result = self.db_service.save_task(task_dict)
                    else:
                        # 如果没有应用实例，尝试从 current_app 获取
                        from flask import has_app_context, current_app
                        if has_app_context():
                            save_result = self.db_service.save_task(task_dict)
                        else:
                            logger.error(f"无法获取 Flask 应用上下文，无法保存任务到数据库: task_id={task_id}")
                            save_result = False
                    
                    # #region agent log
                    with open('/opt/hanfu/products/.cursor/debug.log', 'a') as f:
                        import json
                        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"try_on_image_service.py:595","message":"数据库保存结果","data":{"task_id":task_id,"save_result":save_result,"has_app":self.app is not None},"timestamp":int(time.time()*1000)}) + '\n')
                    # #endregion
                    
                    logger.debug(f"任务状态已同步到数据库: task_id={task_id}")
                except Exception as e:
                    # #region agent log
                    with open('/opt/hanfu/products/.cursor/debug.log', 'a') as f:
                        import json
                        import traceback
                        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"try_on_image_service.py:602","message":"数据库保存异常","data":{"task_id":task_id,"error":str(e),"traceback":traceback.format_exc()},"timestamp":int(time.time()*1000)}) + '\n')
                    # #endregion
                    logger.warning(f"更新任务到数据库失败: {str(e)}", exc_info=True)
                
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
                        # 在 Flask 应用上下文中执行数据库操作
                        if self.app:
                            with self.app.app_context():
                                self.db_service.save_task(task_dict)
                        else:
                            from flask import has_app_context
                            if has_app_context():
                                self.db_service.save_task(task_dict)
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
                        # 在 Flask 应用上下文中执行数据库操作
                        if self.app:
                            with self.app.app_context():
                                self.db_service.save_task(task_dict)
                        else:
                            from flask import has_app_context
                            if has_app_context():
                                self.db_service.save_task(task_dict)
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
            task_dict = self.db_service.get_task(task_id)
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
        # #region agent log
        with open('/opt/hanfu/products/.cursor/debug.log', 'a') as f:
            import json
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"G","location":"try_on_image_service.py:852","message":"get_task_status调用-BEFORE查询","data":{"task_id":task_id},"timestamp":int(time.time()*1000)}) + '\n')
        # #endregion
        
        # 优先从数据库读取（数据库是主存储）
        # 注意：必须始终从数据库读取最新状态，不能依赖内存缓存
        # 关键修复：强制刷新数据库会话，确保读取最新数据
        try:
            # 在 Flask 应用上下文中执行数据库操作
            # 关键修复：强制刷新会话，确保读取最新数据
            if self.app:
                with self.app.app_context():
                    # 强制刷新会话，清除任何缓存
                    from backend.models import db
                    db.session.expire_all()
                    task_dict = self.db_service.get_task(task_id)
            else:
                from flask import has_app_context
                if has_app_context():
                    from backend.models import db
                    db.session.expire_all()
                    task_dict = self.db_service.get_task(task_id)
                else:
                    task_dict = None
            
            if task_dict:
                # #region agent log
                with open('/opt/hanfu/products/.cursor/debug.log', 'a') as f:
                    import json
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"G","location":"try_on_image_service.py:875","message":"get_task_status-从数据库获取","data":{"task_id":task_id,"status":task_dict.get("status"),"result_image_url":task_dict.get("result_image_url")},"timestamp":int(time.time()*1000)}) + '\n')
                # #endregion
                
                # 同步到内存缓存（但返回数据库的最新状态）
                self._sync_task_to_cache(task_dict)
                logger.debug(f"从数据库获取任务状态: task_id={task_id}, status={task_dict.get('status')}")
                return task_dict
        except Exception as e:
            logger.warning(f"从数据库获取任务状态失败: {str(e)}", exc_info=True)
            
            # #region agent log
            with open('/opt/hanfu/products/.cursor/debug.log', 'a') as f:
                import json
                import traceback
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"G","location":"try_on_image_service.py:882","message":"get_task_status-数据库查询异常","data":{"task_id":task_id,"error":str(e),"traceback":traceback.format_exc()},"timestamp":int(time.time()*1000)}) + '\n')
            # #endregion
        
        # 如果数据库中没有，尝试从内存缓存获取（降级方案）
        task = self.tasks.get(task_id)
        if task:
            logger.debug(f"从内存缓存获取任务状态: task_id={task_id}")
            
            # #region agent log
            with open('/opt/hanfu/products/.cursor/debug.log', 'a') as f:
                import json
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"G","location":"try_on_image_service.py:890","message":"get_task_status-从内存缓存获取","data":{"task_id":task_id,"status":task.status.value},"timestamp":int(time.time()*1000)}) + '\n')
            # #endregion
            
            return task.to_dict()
        
        # 都不存在，抛出异常
        # 使用主项目的 NotFoundError（使用 details 参数，不是 detail）
        from backend.exceptions import NotFoundError
        raise NotFoundError(
            message=f"任务不存在: {task_id}",
            resource_type='task',
            resource_id=task_id,
            details={"task_id": task_id}
        )
    
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
        
        while not self._shutdown_event.is_set():
            try:
                # 等待清理间隔
                await asyncio.sleep(self.config.TASK_CLEANUP_INTERVAL_SECONDS)
                
                # 计算清理时间阈值
                cutoff_time = datetime.now() - timedelta(hours=self.config.TASK_RETENTION_HOURS)
                
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
                        f"(保留时间: {self.config.TASK_RETENTION_HOURS}小时)"
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
        
        while not self._shutdown_event.is_set():
            try:
                # 等待健康检查间隔
                await asyncio.sleep(self.config.WORKER_HEALTH_CHECK_INTERVAL_SECONDS)
                
                # 检查工作器是否运行
                worker_alive = (
                    self._worker_started and
                    self._worker_thread is not None and
                    self._worker_thread.is_alive() and
                    self._worker_loop is not None and
                    not self._worker_loop.is_closed()
                )
                
                # 检查心跳时间（如果工作器运行但长时间没有心跳，可能卡住了）
                heartbeat_timeout = self.config.WORKER_HEALTH_CHECK_INTERVAL_SECONDS * 3
                heartbeat_ok = (
                    time.time() - self._worker_last_heartbeat < heartbeat_timeout
                )
                
                # 获取队列长度和正在处理的任务数
                queue_size = self._task_queue.qsize() if self._task_queue else 0
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
                    if self.config.WORKER_RESTART_ON_FAILURE:
                        if self.config.WORKER_MAX_RESTART_ATTEMPTS == 0 or \
                           self._worker_restart_count < self.config.WORKER_MAX_RESTART_ATTEMPTS:
                            logger.warning(
                                f"工作器异常检测到 (alive={worker_alive}, heartbeat_ok={heartbeat_ok})，"
                                f"将自动重启 (第{self._worker_restart_count + 1}次)"
                            )
                            # 注意：在事件循环中不能直接重启线程，需要通过主线程
                            # 这里只记录日志，实际重启应该由外部调用
                        else:
                            logger.error(
                                f"工作器异常但已达到最大重启次数 "
                                f"({self.config.WORKER_MAX_RESTART_ATTEMPTS})，停止重启"
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
        
        while not self._shutdown_event.is_set():
            try:
                # 等待同步间隔
                await asyncio.sleep(self._sync_interval_seconds)
                
                # 同步内存中的任务到数据库（确保数据库是最新的）
                sync_count = 0
                for task_id, task in list(self.tasks.items()):
                    try:
                        # 将内存中的任务状态同步到数据库
                        task_dict = task.to_dict()
                        self.db_service.save_task(task_dict)
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
                            task_dict = self.db_service.get_task(task_id)
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
            self._worker_thread is not None and
            self._worker_thread.is_alive() and
            self._worker_loop is not None and
            not self._worker_loop.is_closed()
        )
        
        heartbeat_age = time.time() - self._worker_last_heartbeat
        
        queue_size = self._task_queue.qsize() if self._task_queue else 0
        
        return {
            "worker_alive": worker_alive,
            "worker_started": self._worker_started,
            "heartbeat_age_seconds": heartbeat_age,
            "queue_size": queue_size,
            "processing_count": len(self._processing_tasks),
            "max_concurrent_tasks": self._max_concurrent_tasks,
            "restart_count": self._worker_restart_count,
            "tasks_in_memory": len(self.tasks)
        }
    
    def shutdown(self):
        """
        关闭服务
        停止后台工作器线程
        """
        logger.info("正在关闭TryOn图片处理服务...")
        self._shutdown_event.set()
        
        # 等待工作器线程结束
        if self._worker_thread and self._worker_thread.is_alive():
            # 停止事件循环
            if self._worker_loop and not self._worker_loop.is_closed():
                self._worker_loop.call_soon_threadsafe(self._worker_loop.stop)
            
            # 等待线程结束（最多等待5秒）
            self._worker_thread.join(timeout=5.0)
            if self._worker_thread.is_alive():
                logger.warning("工作器线程未能在5秒内结束")
        
        logger.info("TryOn图片处理服务已关闭")
