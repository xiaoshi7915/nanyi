"""
配置管理模块
"""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

# 获取项目根目录（.env文件所在目录）
# config.py在backend/app/目录，需要向上两级到项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """应用配置类"""
    
    # 应用基础配置
    app_name: str = "AI试衣图生图服务"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"
    
    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 15001
    
    # 火山引擎方舟API配置（Seedream 4.5）
    ark_api_key: str  # 火山引擎API Key（sk-开头）
    ark_base_url: str = "https://ark.cn-beijing.volces.com/api/v3"  # 火山引擎API地址
    ark_model_name: str = "doubao-seedream-4-5-251128"  # 模型名称
    # ark_model_name: str = "doubao-seedream-4-0-250828"  # 模型名称
    
    # 阿里云OSS配置
    oss_access_key_id: str
    oss_access_key_secret: str
    oss_bucket_name: str
    oss_endpoint: str
    oss_region: str = "cn-hangzhou"
    oss_bucket_endpoint: Optional[str] = None  # OSS存储桶完整端点（可选，如：https://bucket.oss-cn-hangzhou.aliyuncs.com）
    
    # 限流配置
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000
    rate_limit_cleanup_interval_seconds: int = 3600  # IP令牌桶清理间隔（秒），默认1小时
    rate_limit_ip_retention_hours: int = 24  # IP令牌桶保留时间（小时），超过此时间未使用的IP会被清理
    
    # 图片配置
    max_image_size_mb: int = 10
    allowed_image_formats: str = "jpeg,jpg,png"
    max_images_per_request: int = 5
    
    # 存储配置
    storage_local_path: str = "./storage"
    storage_upload_dir: str = "uploads"  # 通用上传目录（向后兼容）
    storage_fabric_dir: str = "uploads/fabric"  # 成衣图/布料图存储目录
    storage_real_person_dir: str = "uploads/real_person"  # 真人图存储目录
    storage_generated_dir: str = "generated"  # 生成图片存储目录
    
    # 数据库配置（支持多种数据库类型）
    db_type: str = "mysql"  # 数据库类型：mysql, postgresql, sqlite等
    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str = "try_on_user"
    db_password: str = "try_on_password"
    db_name: str = "try_on"
    db_charset: str = "utf8mb4"  # 数据库字符集
    
    # 数据库连接池配置
    db_pool_size: int = 5  # 连接池大小（保持的连接数）
    db_max_overflow: int = 10  # 连接池最大溢出数（超过pool_size后可以创建的额外连接数）
    db_pool_timeout: int = 30  # 从连接池获取连接的超时时间（秒）
    db_pool_recycle: int = 3600  # 连接回收时间（秒），超过此时间的连接会被回收重建
    db_pool_pre_ping: bool = True  # 连接前ping测试，确保连接有效
    
    # CORS配置
    cors_allow_origins: str = "*"  # CORS允许的来源，多个用逗号分隔，如："https://example.com,https://app.example.com"
    cors_allow_credentials: bool = True  # 是否允许携带凭证
    cors_allow_methods: str = "*"  # 允许的HTTP方法，多个用逗号分隔，如："GET,POST,PUT,DELETE"
    cors_allow_headers: str = "*"  # 允许的HTTP头，多个用逗号分隔
    
    # 任务配置
    task_timeout_seconds: int = 300
    task_max_retries: int = 3
    max_concurrent_tasks: int = 5  # 最大并发任务数
    task_cleanup_interval_seconds: int = 3600  # 任务清理间隔（秒），默认1小时
    task_retention_hours: int = 24  # 已完成/失败任务保留时间（小时），超过此时间的任务会被清理
    worker_health_check_interval_seconds: int = 60  # 工作器健康检查间隔（秒），默认1分钟
    worker_restart_on_failure: bool = True  # 工作器异常时是否自动重启
    worker_max_restart_attempts: int = 10  # 工作器最大重启尝试次数（0表示无限）
    
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    @property
    def storage_upload_path(self) -> str:
        """获取上传目录完整路径（向后兼容）"""
        return f"{self.storage_local_path}/{self.storage_upload_dir}"
    
    @property
    def storage_fabric_path(self) -> str:
        """获取成衣图/布料图存储目录完整路径"""
        return f"{self.storage_local_path}/{self.storage_fabric_dir}"
    
    @property
    def storage_real_person_path(self) -> str:
        """获取真人图存储目录完整路径"""
        return f"{self.storage_local_path}/{self.storage_real_person_dir}"
    
    @property
    def storage_generated_path(self) -> str:
        """获取生成目录完整路径"""
        return f"{self.storage_local_path}/{self.storage_generated_dir}"
    
    @property
    def allowed_image_formats_set(self) -> set[str]:
        """获取允许的图片格式集合"""
        return set(self.allowed_image_formats.split(","))
    
    @property
    def cors_allow_origins_list(self) -> list[str]:
        """获取CORS允许的来源列表"""
        if self.cors_allow_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_allow_origins.split(",")]
    
    @property
    def cors_allow_methods_list(self) -> list[str]:
        """获取CORS允许的方法列表"""
        if self.cors_allow_methods == "*":
            return ["*"]
        return [method.strip() for method in self.cors_allow_methods.split(",")]
    
    @property
    def cors_allow_headers_list(self) -> list[str]:
        """获取CORS允许的头列表"""
        if self.cors_allow_headers == "*":
            return ["*"]
        return [header.strip() for header in self.cors_allow_headers.split(",")]
    
    @property
    def db_url(self) -> str:
        """
        获取数据库连接URL
        根据数据库类型生成对应的连接URL
        """
        if self.db_type.lower() == "mysql":
            return f"mysql+pymysql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}?charset={self.db_charset}"
        elif self.db_type.lower() == "postgresql":
            return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        elif self.db_type.lower() == "sqlite":
            # SQLite使用文件路径
            return f"sqlite:///{self.db_name}"
        else:
            # 默认使用MySQL
            return f"mysql+pymysql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}?charset={self.db_charset}"
    
    def validate(self) -> tuple[bool, list[str]]:
        """
        验证配置是否完整和有效
        
        Returns:
            (是否有效, 错误列表)
        """
        errors = []
        
        # 验证必填配置项
        required_configs = {
            "ark_api_key": self.ark_api_key,
            "oss_access_key_id": self.oss_access_key_id,
            "oss_access_key_secret": self.oss_access_key_secret,
            "oss_bucket_name": self.oss_bucket_name,
            "oss_endpoint": self.oss_endpoint,
        }
        
        for config_name, config_value in required_configs.items():
            if not config_value or config_value.strip() == "":
                errors.append(f"必填配置项缺失或为空: {config_name}")
        
        # 验证配置值的有效性
        # 验证端口范围
        if self.port < 1 or self.port > 65535:
            errors.append(f"端口配置无效: {self.port} (应在1-65535之间)")
        
        # 验证日志级别
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_log_levels:
            errors.append(f"日志级别无效: {self.log_level} (有效值: {', '.join(valid_log_levels)})")
        
        # 验证数据库类型
        valid_db_types = ["mysql", "postgresql", "sqlite"]
        if self.db_type.lower() not in valid_db_types:
            errors.append(f"数据库类型无效: {self.db_type} (有效值: {', '.join(valid_db_types)})")
        
        # 验证图片大小限制
        if self.max_image_size_mb < 1 or self.max_image_size_mb > 100:
            errors.append(f"图片大小限制无效: {self.max_image_size_mb}MB (应在1-100MB之间)")
        
        # 验证并发任务数
        if self.max_concurrent_tasks < 1 or self.max_concurrent_tasks > 100:
            errors.append(f"最大并发任务数无效: {self.max_concurrent_tasks} (应在1-100之间)")
        
        return len(errors) == 0, errors
    
    def validate_and_raise(self) -> None:
        """
        验证配置并抛出异常（如果无效）
        
        Raises:
            ConfigurationError: 配置无效时抛出异常
        """
        from app.utils.exceptions import ConfigurationError
        
        is_valid, errors = self.validate()
        if not is_valid:
            error_message = "配置验证失败:\n" + "\n".join(f"  - {error}" for error in errors)
            raise ConfigurationError(
                error_message,
                detail={"errors": errors},
                context={"config_file": str(ENV_FILE) if ENV_FILE.exists() else "未找到.env文件"}
            )


# 全局配置实例
settings = Settings()

