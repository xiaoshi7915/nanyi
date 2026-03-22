"""
限流服务模块
基于令牌桶算法实现API限流功能
支持按IP或全局限流，可配置化限流规则
"""
import time
import asyncio
from typing import Dict, Optional

from app.config import settings
from app.utils.logger import get_logger

# 获取日志记录器
logger = get_logger(__name__)


class TokenBucket:
    """
    令牌桶类
    实现令牌桶算法的核心逻辑（异步版本）
    """
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        初始化令牌桶
        
        Args:
            capacity: 桶容量（最大令牌数）
            refill_rate: 令牌补充速率（令牌/秒）
        """
        self.capacity = capacity  # 桶容量
        self.tokens = float(capacity)  # 当前令牌数
        self.refill_rate = refill_rate  # 补充速率
        self.last_refill = time.time()  # 上次补充时间
        self.lock = asyncio.Lock()  # 异步锁，保证异步环境下的线程安全
    
    def _refill(self) -> None:
        """补充令牌（内部方法，不需要锁）"""
        now = time.time()
        # 计算时间差
        elapsed = now - self.last_refill
        # 计算应该补充的令牌数
        tokens_to_add = elapsed * self.refill_rate
        # 更新令牌数（不超过容量）
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        # 更新上次补充时间
        self.last_refill = now
    
    async def consume(self, tokens: int = 1) -> bool:
        """
        消费令牌（异步方法）
        
        Args:
            tokens: 需要消费的令牌数（默认1）
        
        Returns:
            是否成功消费令牌
        """
        async with self.lock:
            # 先补充令牌
            self._refill()
            # 检查是否有足够的令牌
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    async def get_available_tokens(self) -> float:
        """
        获取当前可用令牌数（异步方法）
        
        Returns:
            可用令牌数
        """
        async with self.lock:
            self._refill()
            return self.tokens


class RateLimitService:
    """
    限流服务类
    管理多个令牌桶，支持按IP或全局限流
    """
    
    def __init__(self):
        """初始化限流服务"""
        # 全局令牌桶（每分钟）
        self.global_bucket_minute = TokenBucket(
            capacity=settings.rate_limit_per_minute,
            refill_rate=settings.rate_limit_per_minute / 60.0  # 每秒补充的令牌数
        )
        
        # 全局令牌桶（每小时）
        self.global_bucket_hour = TokenBucket(
            capacity=settings.rate_limit_per_hour,
            refill_rate=settings.rate_limit_per_hour / 3600.0  # 每秒补充的令牌数
        )
        
        # 按IP的令牌桶字典（每分钟）
        self.ip_buckets_minute: Dict[str, TokenBucket] = {}
        
        # 按IP的令牌桶字典（每小时）
        self.ip_buckets_hour: Dict[str, TokenBucket] = {}
        
        # IP最后使用时间记录（用于清理）
        self.ip_last_used: Dict[str, float] = {}
        
        # 清理任务
        self._cleanup_task: Optional[asyncio.Task] = None
        self._cleanup_started = False
        
        logger.info(f"限流服务初始化完成 - 每分钟限制: {settings.rate_limit_per_minute}, 每小时限制: {settings.rate_limit_per_hour}")
    
    async def check_rate_limit(
        self,
        client_ip: Optional[str] = None,
        check_global: bool = True,
        check_ip: bool = True
    ) -> tuple[bool, Optional[str]]:
        """
        检查是否超过限流（异步方法）
        
        Args:
            client_ip: 客户端IP地址（可选）
            check_global: 是否检查全局限流（默认True）
            check_ip: 是否检查IP限流（默认True）
        
        Returns:
            (是否允许, 错误信息)
        """
        # 检查全局限流
        if check_global:
            if not await self.global_bucket_minute.consume():
                logger.warning("全局限流：每分钟请求数超限")
                return False, "请求过于频繁，请稍后再试（每分钟限制）"
            
            if not await self.global_bucket_hour.consume():
                logger.warning("全局限流：每小时请求数超限")
                return False, "请求过于频繁，请稍后再试（每小时限制）"
        
        # 检查IP限流
        if check_ip and client_ip:
            # 启动清理任务（如果尚未启动）
            if not self._cleanup_started:
                try:
                    loop = asyncio.get_event_loop()
                    loop.create_task(self._start_ip_cleanup())
                    self._cleanup_started = True
                except RuntimeError:
                    asyncio.ensure_future(self._start_ip_cleanup())
                    self._cleanup_started = True
            
            # 获取或创建IP令牌桶
            if client_ip not in self.ip_buckets_minute:
                self.ip_buckets_minute[client_ip] = TokenBucket(
                    capacity=settings.rate_limit_per_minute,
                    refill_rate=settings.rate_limit_per_minute / 60.0
                )
            if client_ip not in self.ip_buckets_hour:
                self.ip_buckets_hour[client_ip] = TokenBucket(
                    capacity=settings.rate_limit_per_hour,
                    refill_rate=settings.rate_limit_per_hour / 3600.0
                )
            
            # 更新IP最后使用时间
            self.ip_last_used[client_ip] = time.time()
            
            # 检查限流
            if not await self.ip_buckets_minute[client_ip].consume():
                logger.warning(f"IP限流：{client_ip} 每分钟请求数超限")
                return False, "您的请求过于频繁，请稍后再试（每分钟限制）"
            
            if not await self.ip_buckets_hour[client_ip].consume():
                logger.warning(f"IP限流：{client_ip} 每小时请求数超限")
                return False, "您的请求过于频繁，请稍后再试（每小时限制）"
        
        return True, None
    
    async def get_rate_limit_status(
        self,
        client_ip: Optional[str] = None
    ) -> dict:
        """
        获取限流状态信息（异步方法）
        
        Args:
            client_ip: 客户端IP地址（可选）
        
        Returns:
            限流状态字典
        """
        status = {
            "global": {
                "minute": {
                    "limit": settings.rate_limit_per_minute,
                    "available": int(await self.global_bucket_minute.get_available_tokens())
                },
                "hour": {
                    "limit": settings.rate_limit_per_hour,
                    "available": int(await self.global_bucket_hour.get_available_tokens())
                }
            }
        }
        
        if client_ip:
            # 如果IP不存在，创建默认令牌桶
            if client_ip not in self.ip_buckets_minute:
                self.ip_buckets_minute[client_ip] = TokenBucket(
                    capacity=settings.rate_limit_per_minute,
                    refill_rate=settings.rate_limit_per_minute / 60.0
                )
            if client_ip not in self.ip_buckets_hour:
                self.ip_buckets_hour[client_ip] = TokenBucket(
                    capacity=settings.rate_limit_per_hour,
                    refill_rate=settings.rate_limit_per_hour / 3600.0
                )
            
            status["ip"] = {
                "address": client_ip,
                "minute": {
                    "limit": settings.rate_limit_per_minute,
                    "available": int(await self.ip_buckets_minute[client_ip].get_available_tokens())
                },
                "hour": {
                    "limit": settings.rate_limit_per_hour,
                    "available": int(await self.ip_buckets_hour[client_ip].get_available_tokens())
                }
            }
        
        return status
    
    def reset_ip_bucket(self, client_ip: str) -> None:
        """
        重置指定IP的令牌桶（用于测试或管理）
        
        Args:
            client_ip: 客户端IP地址
        """
        if client_ip in self.ip_buckets_minute:
            del self.ip_buckets_minute[client_ip]
        if client_ip in self.ip_buckets_hour:
            del self.ip_buckets_hour[client_ip]
        if client_ip in self.ip_last_used:
            del self.ip_last_used[client_ip]
        logger.info(f"已重置IP {client_ip} 的限流桶")
    
    async def _start_ip_cleanup(self):
        """
        启动IP令牌桶清理器
        定期清理长时间未使用的IP令牌桶，防止内存泄漏
        """
        logger.info("IP令牌桶清理器已启动")
        
        while True:
            try:
                # 等待清理间隔
                await asyncio.sleep(settings.rate_limit_cleanup_interval_seconds)
                
                # 计算清理时间阈值
                cutoff_time = time.time() - (settings.rate_limit_ip_retention_hours * 3600)
                
                # 查找需要清理的IP（超过保留时间未使用）
                ips_to_remove = []
                for ip, last_used in self.ip_last_used.items():
                    if last_used < cutoff_time:
                        ips_to_remove.append(ip)
                
                # 执行清理
                if ips_to_remove:
                    for ip in ips_to_remove:
                        self.ip_buckets_minute.pop(ip, None)
                        self.ip_buckets_hour.pop(ip, None)
                        self.ip_last_used.pop(ip, None)
                    logger.info(
                        f"IP令牌桶清理完成: 清理了{len(ips_to_remove)}个IP "
                        f"(保留时间: {settings.rate_limit_ip_retention_hours}小时)"
                    )
                else:
                    logger.debug("IP令牌桶清理检查完成: 无需清理的IP")
                    
            except Exception as e:
                logger.error(f"IP令牌桶清理器错误: {str(e)}", exc_info=True)
                await asyncio.sleep(60)  # 错误后等待1分钟再继续


# 全局限流服务实例
rate_limit_service = RateLimitService()

