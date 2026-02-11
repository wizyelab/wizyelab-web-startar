"""
Redis 客户端模块

支持连接池、缓存操作、分布式锁等功能
"""

import json
import asyncio
from typing import Any, Optional, Union
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from redis.asyncio import Redis
from redis.asyncio.connection import ConnectionPool

from app.core.config import settings
from app.core.logging import setup_logger

logger = setup_logger(__name__)


class RedisClient:
    """
    Redis 客户端封装类

    支持:
    - 连接池管理
    - 基本操作 (get, set, delete)
    - 缓存操作 (带 TTL)
    - 分布式锁
    - 发布订阅
    """

    def __init__(self):
        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[Redis] = None
        self._initialized = False
        self._reconnect_lock = asyncio.Lock()
        self._reconnecting = False

    async def init(self) -> None:
        """初始化 Redis 连接池"""
        if self._initialized:
            return

        logger.info("Initializing Redis connection pool...")

        try:
            self._pool = ConnectionPool(
                host=settings.redis.host,
                port=settings.redis.port,
                username=settings.redis.username,
                password=settings.redis.password,
                db=settings.redis.db,
                max_connections=settings.redis.max_connections,
                decode_responses=settings.redis.decode_responses,
                socket_timeout=settings.redis.socket_timeout,
                socket_connect_timeout=settings.redis.socket_connect_timeout,
                # 添加健康检查间隔，自动检测并重建断开的连接
                health_check_interval=30,
                # 添加重试配置
                retry_on_timeout=True,
            )

            self._client = Redis(connection_pool=self._pool)

            # 测试连接
            await self._client.ping()
            self._initialized = True
            logger.info("Redis connection pool initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Redis connection: {e}")
            raise

    async def close(self) -> None:
        """关闭 Redis 连接"""
        if self._client:
            await self._client.close()
        if self._pool:
            await self._pool.disconnect()
        self._initialized = False
        logger.info("Redis connection closed")

    @property
    def client(self) -> Redis:
        """获取 Redis 客户端"""
        if not self._initialized:
            raise RuntimeError("Redis client not initialized. Call init() first.")
        return self._client

    async def _reconnect(self) -> None:
        """重新连接 Redis（带锁防止并发重连）"""
        # 使用锁防止多个请求同时重连
        async with self._reconnect_lock:
            # 如果已经在重连中或已经重连成功，直接返回
            if self._reconnecting:
                return

            # 再次检查连接是否已恢复（可能其他协程已经重连成功）
            if self._initialized and self._client:
                try:
                    await asyncio.wait_for(self._client.ping(), timeout=2.0)
                    return  # 连接正常，无需重连
                except Exception:
                    pass  # 连接仍然有问题，继续重连

            self._reconnecting = True
            try:
                logger.info("Starting Redis reconnection...")
                self._initialized = False

                # 关闭旧连接
                if self._client:
                    try:
                        await asyncio.wait_for(self._client.close(), timeout=5.0)
                    except Exception as e:
                        logger.warning(f"Error closing Redis client: {e}")

                if self._pool:
                    try:
                        await asyncio.wait_for(self._pool.disconnect(), timeout=5.0)
                    except Exception as e:
                        logger.warning(f"Error disconnecting Redis pool: {e}")

                self._client = None
                self._pool = None

                # 等待一小段时间确保连接完全关闭
                await asyncio.sleep(0.1)

                # 重新初始化
                await self.init()
                logger.info("Redis reconnected successfully")
            except Exception as e:
                logger.error(f"Failed to reconnect Redis: {e}")
                raise
            finally:
                self._reconnecting = False

    # =========================================================================
    # 基本操作
    # =========================================================================
    async def get(self, key: str) -> Optional[str]:
        """获取值（带自动重连）"""
        max_retries = 2
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                return await self.client.get(key)
            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                # 连接断开时尝试重新初始化
                if "closed" in error_str or "connection" in error_str or "handler" in error_str:
                    if attempt < max_retries:
                        logger.warning(f"Redis connection error (attempt {attempt + 1}/{max_retries + 1}), reconnecting: {e}")
                        try:
                            await self._reconnect()
                            continue  # 重连成功，重试操作
                        except Exception as reconnect_error:
                            logger.error(f"Redis reconnect failed: {reconnect_error}")
                    else:
                        logger.error(f"Redis connection error after {max_retries + 1} attempts: {e}")
                else:
                    raise

        raise last_error

    async def set(
        self,
        key: str,
        value: Union[str, bytes, int, float],
        ex: Optional[int] = None,
        px: Optional[int] = None,
        nx: bool = False,
        xx: bool = False,
    ) -> bool:
        """
        设置值（带自动重连）

        Args:
            key: 键
            value: 值
            ex: 过期时间（秒）
            px: 过期时间（毫秒）
            nx: 仅当键不存在时设置
            xx: 仅当键存在时设置
        """
        max_retries = 2
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                return await self.client.set(key, value, ex=ex, px=px, nx=nx, xx=xx)
            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                # 连接断开时尝试重新初始化
                if "closed" in error_str or "connection" in error_str or "handler" in error_str:
                    if attempt < max_retries:
                        logger.warning(f"Redis connection error (attempt {attempt + 1}/{max_retries + 1}), reconnecting: {e}")
                        try:
                            await self._reconnect()
                            continue  # 重连成功，重试操作
                        except Exception as reconnect_error:
                            logger.error(f"Redis reconnect failed: {reconnect_error}")
                    else:
                        logger.error(f"Redis connection error after {max_retries + 1} attempts: {e}")
                else:
                    raise

        raise last_error

    async def delete(self, *keys: str) -> int:
        """删除键"""
        return await self.client.delete(*keys)

    async def exists(self, *keys: str) -> int:
        """检查键是否存在"""
        return await self.client.exists(*keys)

    async def expire(self, key: str, seconds: int) -> bool:
        """设置过期时间"""
        return await self.client.expire(key, seconds)

    async def ttl(self, key: str) -> int:
        """获取剩余过期时间"""
        return await self.client.ttl(key)

    # =========================================================================
    # JSON 操作
    # =========================================================================
    async def get_json(self, key: str) -> Optional[Any]:
        """获取 JSON 值"""
        value = await self.get(key)
        if value:
            return json.loads(value)
        return None

    async def set_json(
        self,
        key: str,
        value: Any,
        ex: Optional[int] = None,
    ) -> bool:
        """设置 JSON 值"""
        return await self.set(key, json.dumps(value, ensure_ascii=False), ex=ex)

    # =========================================================================
    # 缓存操作
    # =========================================================================
    async def cache_get(self, key: str) -> Optional[Any]:
        """
        获取缓存值

        自动添加缓存前缀
        """
        cache_key = f"{settings.cache.redis.prefix}{key}"
        return await self.get_json(cache_key)

    async def cache_set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），默认使用配置的 default_ttl
        """
        cache_key = f"{settings.cache.redis.prefix}{key}"
        ttl = ttl or settings.cache.redis.default_ttl
        return await self.set_json(cache_key, value, ex=ttl)

    async def cache_delete(self, key: str) -> int:
        """删除缓存"""
        cache_key = f"{settings.cache.redis.prefix}{key}"
        return await self.delete(cache_key)

    async def cache_clear_pattern(self, pattern: str) -> int:
        """
        清除匹配模式的缓存

        Args:
            pattern: 匹配模式（如 "user:*"）
        """
        cache_pattern = f"{settings.cache.redis.prefix}{pattern}"
        keys = []
        async for key in self.client.scan_iter(match=cache_pattern):
            keys.append(key)
        if keys:
            return await self.delete(*keys)
        return 0

    # =========================================================================
    # 分布式锁
    # =========================================================================
    @asynccontextmanager
    async def lock(
        self,
        name: str,
        timeout: int = 10,
        blocking: bool = True,
        blocking_timeout: float = 5.0,
    ):
        """
        分布式锁上下文管理器

        Args:
            name: 锁名称
            timeout: 锁超时时间（秒）
            blocking: 是否阻塞等待
            blocking_timeout: 阻塞等待超时时间（秒）

        Usage:
            async with redis_client.lock("my_lock"):
                # do something
        """
        lock_key = f"lock:{name}"
        lock = self.client.lock(
            lock_key,
            timeout=timeout,
            blocking=blocking,
            blocking_timeout=blocking_timeout,
        )

        acquired = await lock.acquire()
        if not acquired:
            raise RuntimeError(f"Failed to acquire lock: {name}")

        try:
            yield lock
        finally:
            await lock.release()

    # =========================================================================
    # Hash 操作
    # =========================================================================
    async def hget(self, name: str, key: str) -> Optional[str]:
        """获取 Hash 字段值"""
        return await self.client.hget(name, key)

    async def hset(self, name: str, key: str, value: str) -> int:
        """设置 Hash 字段值"""
        return await self.client.hset(name, key, value)

    async def hgetall(self, name: str) -> dict:
        """获取整个 Hash"""
        return await self.client.hgetall(name)

    async def hdel(self, name: str, *keys: str) -> int:
        """删除 Hash 字段"""
        return await self.client.hdel(name, *keys)

    # =========================================================================
    # List 操作
    # =========================================================================
    async def lpush(self, name: str, *values: str) -> int:
        """从左边推入列表"""
        return await self.client.lpush(name, *values)

    async def rpush(self, name: str, *values: str) -> int:
        """从右边推入列表"""
        return await self.client.rpush(name, *values)

    async def lpop(self, name: str) -> Optional[str]:
        """从左边弹出列表"""
        return await self.client.lpop(name)

    async def rpop(self, name: str) -> Optional[str]:
        """从右边弹出列表"""
        return await self.client.rpop(name)

    async def lrange(self, name: str, start: int, end: int) -> list:
        """获取列表范围"""
        return await self.client.lrange(name, start, end)

    async def llen(self, name: str) -> int:
        """获取列表长度"""
        return await self.client.llen(name)

    # =========================================================================
    # Set 操作
    # =========================================================================
    async def sadd(self, name: str, *values: str) -> int:
        """添加到集合"""
        return await self.client.sadd(name, *values)

    async def srem(self, name: str, *values: str) -> int:
        """从集合移除"""
        return await self.client.srem(name, *values)

    async def smembers(self, name: str) -> set:
        """获取集合所有成员"""
        return await self.client.smembers(name)

    async def sismember(self, name: str, value: str) -> bool:
        """检查是否是集合成员"""
        return await self.client.sismember(name, value)

    # =========================================================================
    # 计数器
    # =========================================================================
    async def incr(self, name: str, amount: int = 1) -> int:
        """增加计数"""
        return await self.client.incr(name, amount)

    async def decr(self, name: str, amount: int = 1) -> int:
        """减少计数"""
        return await self.client.decr(name, amount)

    # =========================================================================
    # 发布订阅
    # =========================================================================
    async def publish(self, channel: str, message: str) -> int:
        """发布消息"""
        return await self.client.publish(channel, message)

    async def subscribe(self, *channels: str):
        """订阅频道"""
        pubsub = self.client.pubsub()
        await pubsub.subscribe(*channels)
        return pubsub


# 全局 Redis 客户端实例
redis_client = RedisClient()


async def init_redis() -> None:
    """初始化 Redis"""
    await redis_client.init()


async def close_redis() -> None:
    """关闭 Redis"""
    await redis_client.close()


async def get_redis() -> RedisClient:
    """获取 Redis 客户端（用于依赖注入）"""
    if not redis_client._initialized:
        await redis_client.init()
    return redis_client
