"""缓存模块"""

from .redis_client import (
    RedisClient,
    redis_client,
    init_redis,
    close_redis,
    get_redis,
)

__all__ = [
    "RedisClient",
    "redis_client",
    "init_redis",
    "close_redis",
    "get_redis",
]
