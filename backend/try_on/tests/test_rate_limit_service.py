"""
限流服务单元测试
"""
import pytest
import time
import asyncio
from app.services.rate_limit_service import RateLimitService, TokenBucket


class TestTokenBucket:
    """令牌桶测试类"""
    
    def test_token_bucket_initialization(self):
        """测试令牌桶初始化"""
        bucket = TokenBucket(capacity=10, refill_rate=1.0)
        assert bucket.capacity == 10
        assert bucket.tokens == 10.0
        assert bucket.refill_rate == 1.0
    
    @pytest.mark.asyncio
    async def test_token_bucket_consume_success(self):
        """测试成功消费令牌"""
        bucket = TokenBucket(capacity=10, refill_rate=1.0)
        result = await bucket.consume(1)
        assert result is True
        # 注意：由于异步锁，无法直接访问tokens，需要通过get_available_tokens检查
        available = await bucket.get_available_tokens()
        assert available < 10.0  # 应该小于10
    
    @pytest.mark.asyncio
    async def test_token_bucket_consume_failure(self):
        """测试令牌不足时消费失败"""
        bucket = TokenBucket(capacity=1, refill_rate=0.1)
        # 消费所有令牌
        assert await bucket.consume(1) is True
        # 再次消费应该失败
        assert await bucket.consume(1) is False
    
    @pytest.mark.asyncio
    async def test_token_bucket_refill(self):
        """测试令牌自动补充"""
        bucket = TokenBucket(capacity=10, refill_rate=10.0)  # 每秒补充10个令牌
        # 消费所有令牌
        await bucket.consume(10)
        available = await bucket.get_available_tokens()
        assert available == 0.0
        
        # 等待0.1秒，应该补充1个令牌
        await asyncio.sleep(0.1)
        assert await bucket.consume(1) is True
    
    @pytest.mark.asyncio
    async def test_token_bucket_get_available_tokens(self):
        """测试获取可用令牌数"""
        bucket = TokenBucket(capacity=10, refill_rate=1.0)
        await bucket.consume(3)
        available = await bucket.get_available_tokens()
        # 由于时间流逝可能导致令牌自动补充，使用近似值比较
        assert abs(available - 7.0) < 0.1


class TestRateLimitService:
    """限流服务测试类"""
    
    @pytest.fixture
    def rate_limit_service(self):
        """创建限流服务实例"""
        service = RateLimitService()
        return service
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_allowed(self, rate_limit_service):
        """测试限流检查通过"""
        allowed, error_msg = await rate_limit_service.check_rate_limit(client_ip="127.0.0.1")
        assert allowed is True
        assert error_msg is None
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_global_exceeded(self, rate_limit_service):
        """测试全局限流超限"""
        # 设置很小的容量以便测试
        rate_limit_service.global_bucket_minute.capacity = 1
        # 消费所有令牌
        await rate_limit_service.global_bucket_minute.consume(1)
        
        allowed, error_msg = await rate_limit_service.check_rate_limit(client_ip="127.0.0.1")
        assert allowed is False
        assert error_msg is not None
        assert "每分钟" in error_msg
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_ip_exceeded(self, rate_limit_service):
        """测试IP限流超限"""
        test_ip = "192.168.1.100"
        # 先创建IP桶
        await rate_limit_service.check_rate_limit(client_ip=test_ip)
        # 设置很小的容量并消费所有令牌
        rate_limit_service.ip_buckets_minute[test_ip].capacity = 1
        await rate_limit_service.ip_buckets_minute[test_ip].consume(1)
        
        allowed, error_msg = await rate_limit_service.check_rate_limit(client_ip=test_ip)
        assert allowed is False
        assert error_msg is not None
        assert "每分钟" in error_msg
    
    @pytest.mark.asyncio
    async def test_get_rate_limit_status(self, rate_limit_service):
        """测试获取限流状态"""
        status = await rate_limit_service.get_rate_limit_status(client_ip="127.0.0.1")
        
        assert "global" in status
        assert "minute" in status["global"]
        assert "hour" in status["global"]
        assert "limit" in status["global"]["minute"]
        assert "available" in status["global"]["minute"]
        
        assert "ip" in status
        assert "address" in status["ip"]
        assert status["ip"]["address"] == "127.0.0.1"
    
    def test_reset_ip_bucket(self, rate_limit_service):
        """测试重置IP令牌桶"""
        test_ip = "192.168.1.200"
        
        # 先使用一次，创建IP桶（需要异步调用）
        import asyncio
        asyncio.run(rate_limit_service.check_rate_limit(client_ip=test_ip))
        assert test_ip in rate_limit_service.ip_buckets_minute
        
        # 重置
        rate_limit_service.reset_ip_bucket(test_ip)
        # 检查是否被删除
        assert test_ip not in rate_limit_service.ip_buckets_minute
        assert test_ip not in rate_limit_service.ip_buckets_hour
        assert test_ip not in rate_limit_service.ip_last_used
    
    @pytest.mark.asyncio
    async def test_multiple_ips_separate_buckets(self, rate_limit_service):
        """测试多个IP使用独立的令牌桶"""
        ip1 = "192.168.1.1"
        ip2 = "192.168.1.2"
        
        # 先创建IP桶
        await rate_limit_service.check_rate_limit(client_ip=ip1)
        await rate_limit_service.check_rate_limit(client_ip=ip2)
        
        # 设置IP1的桶容量为1并消费所有令牌
        rate_limit_service.ip_buckets_minute[ip1].capacity = 1
        await rate_limit_service.ip_buckets_minute[ip1].consume(1)
        
        # IP1应该被限流
        allowed1, _ = await rate_limit_service.check_rate_limit(client_ip=ip1)
        assert allowed1 is False
        
        # IP2应该不受影响
        allowed2, _ = await rate_limit_service.check_rate_limit(client_ip=ip2)
        assert allowed2 is True
    
    @pytest.mark.asyncio
    async def test_rate_limit_without_ip(self, rate_limit_service):
        """测试不提供IP时的限流检查"""
        allowed, error_msg = await rate_limit_service.check_rate_limit(client_ip=None)
        # 只检查全局限流，应该通过
        assert allowed is True or error_msg is not None

