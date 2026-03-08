"""
FastAPI应用入口
"""
import warnings
# 过滤 Pydantic 受保护命名空间警告（来自 FastAPI 动态生成的 Form 模型）
warnings.filterwarnings("ignore", message=".*Field.*has conflict with protected namespace.*", category=UserWarning)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from fastapi.exceptions import RequestValidationError

from app.config import settings
from app.utils.logger import setup_logger, get_logger
from app.utils.exceptions import BaseAppException
from app.utils.exception_handler import app_exception_handler, validation_exception_handler
from app.api.v1 import try_on

# 设置日志
logger = setup_logger(level=settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    - 启动时：初始化资源、验证配置
    - 关闭时：清理资源
    """
    # 启动时执行
    logger.info(f"启动 {settings.app_name} v{settings.app_version}")
    logger.info(f"日志级别: {settings.log_level}")
    logger.info(f"调试模式: {settings.debug}")
    
    # 验证配置（启动时验证所有必填配置）
    try:
        logger.info("正在验证配置...")
        settings.validate_and_raise()
        logger.info("配置验证通过")
    except Exception as e:
        logger.error(f"配置验证失败: {str(e)}", exc_info=True)
        raise
    
    # 创建必要的目录
    import os
    os.makedirs(settings.storage_upload_path, exist_ok=True)
    os.makedirs(settings.storage_fabric_path, exist_ok=True)
    os.makedirs(settings.storage_real_person_path, exist_ok=True)
    os.makedirs(settings.storage_generated_path, exist_ok=True)
    logger.info(
        f"存储目录已创建: "
        f"uploads={settings.storage_upload_path}, "
        f"fabric={settings.storage_fabric_path}, "
        f"real_person={settings.storage_real_person_path}, "
        f"generated={settings.storage_generated_path}"
    )
    
    yield
    
    # 关闭时执行
    logger.info(f"关闭 {settings.app_name}")


# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="基于图生图技术的AI试衣服务API",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 配置CORS（从环境变量读取）
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins_list,  # 从环境变量读取，生产环境应限制具体域名
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods_list,
    allow_headers=settings.cors_allow_headers_list,
)

# 注册异常处理器
app.add_exception_handler(BaseAppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# 注册路由
app.include_router(try_on.router, prefix="/api/v1", tags=["试衣服务"])


@app.get("/")
async def root():
    """根路径，返回API信息"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": settings.app_name
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )

