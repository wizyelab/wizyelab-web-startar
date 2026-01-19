"""限流中间件

基于 Redis 的分布式限流实现，支持：
- 滑动窗口限流算法
- 按 IP 或用户标识限流
- 不同 API 路径的差异化限流
- 限流信息响应头
"""

import logging
import time
from typing import Callable, Optional, Tuple

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings

logger = logging.getLogger(__name__)


class RateLimitExceeded(Exception):
    """限流异常"""

    def __init__(self, limit: int, window: int, retry_after: int):
        self.limit = limit
        self.window = window
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded: {limit} requests per {window}s")


class RateLimiter:
    """
    分布式限流器

    使用 Redis 实现滑动窗口限流算法
    """

    def __init__(self):
        self._redis = None

    async def _get_redis(self):
        """懒加载 Redis 客户端"""
        if self._redis is None:
            try:
                from app.infrastructure.cache.redis_client import redis_client
                if not redis_client._initialized:
                    await redis_client.init()
                self._redis = redis_client
            except Exception as e:
                logger.warning(f"Failed to get Redis client for rate limiting: {e}")
                return None
        return self._redis

    def _get_identifier(self, request: Request) -> str:
        """
        获取请求标识符

        优先级：
        1. X-Forwarded-For 头（代理后的真实 IP）
        2. X-Real-IP 头
        3. 客户端 IP

        Args:
            request: FastAPI 请求对象

        Returns:
            请求标识符
        """
        # 尝试从代理头获取真实 IP
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # X-Forwarded-For 可能包含多个 IP，取第一个
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # 使用客户端 IP
        if request.client:
            return request.client.host

        return "unknown"

    def _get_api_category(self, path: str) -> Optional[str]:
        """
        根据路径获取 API 类别

        Args:
            path: 请求路径

        Returns:
            API 类别 (chat/open/internal) 或 None
        """
        api_prefix = settings.app.api_prefix

        if path.startswith(f"{api_prefix}/v1/public/"):
            # 检查是否是 chat 相关
            if "/chat" in path:
                return "chat"
            return "open"
        elif path.startswith(f"{api_prefix}/v1/internal/"):
            return "internal"

        return None

    def _get_limit_for_path(self, path: str) -> Tuple[int, int]:
        """
        获取路径对应的限流配置

        Args:
            path: 请求路径

        Returns:
            (limit, window) 元组
        """
        config = settings.rate_limit

        # 获取 API 类别
        category = self._get_api_category(path)

        # 获取对应的限制
        if category and category in config.api_limits:
            limit = config.api_limits[category]
        else:
            limit = config.default_limit

        window = config.default_window

        return limit, window

    async def check_rate_limit(
        self,
        request: Request
    ) -> Tuple[bool, int, int, int, int]:
        """
        检查请求是否超过限流

        使用滑动窗口算法：
        - 使用 Redis 有序集合 (ZSET) 存储请求时间戳
        - 每次请求时清理过期的时间戳
        - 统计当前窗口内的请求数

        Args:
            request: FastAPI 请求对象

        Returns:
            (allowed, remaining, limit, window, retry_after) 元组
            - allowed: 是否允许请求
            - remaining: 剩余请求次数
            - limit: 限制次数
            - window: 时间窗口（秒）
            - retry_after: 需要等待的秒数（仅在被限流时有效）
        """
        identifier = self._get_identifier(request)
        path = request.url.path
        limit, window = self._get_limit_for_path(path)

        # 构造 Redis key
        key = f"wizyelab:ratelimit:{identifier}:{path}"

        redis = await self._get_redis()
        if redis is None:
            # Redis 不可用时，放行请求但记录警告
            logger.warning("Rate limiting disabled: Redis unavailable")
            return True, limit, limit, window, 0

        now = time.time()
        window_start = now - window

        try:
            # 使用 Redis Pipeline 执行原子操作
            pipe = redis._pool.pipeline()

            # 1. 清理过期的请求记录
            pipe.zremrangebyscore(key, 0, window_start)

            # 2. 获取当前窗口内的请求数
            pipe.zcard(key)

            # 3. 添加当前请求时间戳
            pipe.zadd(key, {str(now): now})

            # 4. 设置 key 过期时间
            pipe.expire(key, window + 1)

            # 执行 Pipeline
            results = await pipe.execute()

            # 获取当前请求数（在添加新请求之前）
            current_count = results[1]

            if current_count >= limit:
                # 获取最早的请求时间戳，计算需要等待的时间
                oldest = await redis._pool.zrange(key, 0, 0, withscores=True)
                if oldest:
                    oldest_time = oldest[0][1]
                    retry_after = int(oldest_time + window - now) + 1
                else:
                    retry_after = window

                return False, 0, limit, window, retry_after

            remaining = limit - current_count - 1
            return True, remaining, limit, window, 0

        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # 出错时放行请求
            return True, limit, limit, window, 0

    async def check_rate_limit_simple(
        self,
        request: Request
    ) -> Tuple[bool, int, int, int, int]:
        """
        简单限流检查（使用计数器，适用于 Redis 不支持 ZSET 的情况）

        使用固定窗口算法

        Args:
            request: FastAPI 请求对象

        Returns:
            (allowed, remaining, limit, window, retry_after) 元组
        """
        identifier = self._get_identifier(request)
        path = request.url.path
        limit, window = self._get_limit_for_path(path)

        # 构造 Redis key（使用时间窗口）
        window_key = int(time.time() / window)
        key = f"wizyelab:ratelimit:{identifier}:{path}:{window_key}"

        redis = await self._get_redis()
        if redis is None:
            return True, limit, limit, window, 0

        try:
            # 增加计数并获取当前值
            current = await redis.incr(key)

            # 首次访问时设置过期时间
            if current == 1:
                await redis.expire(key, window + 1)

            if current > limit:
                # 计算需要等待的时间
                ttl = await redis.ttl(key)
                retry_after = ttl if ttl > 0 else window
                return False, 0, limit, window, retry_after

            remaining = limit - current
            return True, remaining, limit, window, 0

        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return True, limit, limit, window, 0


# 全局限流器实例
rate_limiter = RateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    限流中间件

    功能：
    - 基于 IP 的请求限流
    - 不同 API 路径的差异化限流
    - 限流信息响应头
    - 429 状态码响应
    """

    # 排除的路径（不进行限流）
    EXCLUDED_PATHS = {
        "/",
        "/health",
        "/livez",
        "/readyz",
        "/metrics",
        "/docs",
        "/redoc",
        "/openapi.json",
    }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求"""
        # 检查是否启用限流
        if not settings.rate_limit.enabled:
            return await call_next(request)

        # 检查是否是排除的路径
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)

        # 检查限流
        allowed, remaining, limit, window, retry_after = await rate_limiter.check_rate_limit_simple(request)

        if not allowed:
            # 返回 429 Too Many Requests
            logger.warning(
                f"Rate limit exceeded for {rate_limiter._get_identifier(request)} "
                f"on {request.url.path}"
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too Many Requests",
                    "message": f"Rate limit exceeded. Please retry after {retry_after} seconds.",
                    "retry_after": retry_after,
                },
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Window": str(window),
                    "Retry-After": str(retry_after),
                },
            )

        # 继续处理请求
        response = await call_next(request)

        # 添加限流信息响应头
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Window"] = str(window)

        return response


def setup_rate_limit(app: FastAPI) -> None:
    """
    设置限流中间件

    Args:
        app: FastAPI 应用实例
    """
    if settings.rate_limit.enabled:
        app.add_middleware(RateLimitMiddleware)
        logger.info(
            f"Rate limiting enabled: {settings.rate_limit.default_limit} "
            f"requests per {settings.rate_limit.default_window}s"
        )
    else:
        logger.info("Rate limiting disabled")
