"""
健康检查模块

提供应用健康状态检查
"""

from typing import Dict, Any, Optional
from enum import Enum

from fastapi import FastAPI, Response
from pydantic import BaseModel

from app.core.config import settings
from app.core.logging import setup_logger

logger = setup_logger(__name__)


class HealthStatus(str, Enum):
    """健康状态"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"


class ComponentHealth(BaseModel):
    """组件健康状态"""
    status: HealthStatus
    message: Optional[str] = None
    latency_ms: Optional[float] = None


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: HealthStatus
    service: str
    version: str
    components: Optional[Dict[str, ComponentHealth]] = None


async def check_database_health() -> ComponentHealth:
    """检查数据库健康状态"""
    import time
    try:
        from sqlalchemy import text
        from app.infrastructure.database.connection import engine
        start = time.time()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        latency = (time.time() - start) * 1000
        return ComponentHealth(
            status=HealthStatus.HEALTHY,
            message="Database connection OK",
            latency_ms=latency,
        )
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return ComponentHealth(
            status=HealthStatus.UNHEALTHY,
            message=str(e),
        )


async def check_redis_health() -> ComponentHealth:
    """检查 Redis 健康状态"""
    import time
    try:
        from app.infrastructure.cache.redis_client import redis_client
        if not redis_client._initialized:
            return ComponentHealth(
                status=HealthStatus.UNHEALTHY,
                message="Redis not initialized",
            )
        start = time.time()
        await redis_client.client.ping()
        latency = (time.time() - start) * 1000
        return ComponentHealth(
            status=HealthStatus.HEALTHY,
            message="Redis connection OK",
            latency_ms=latency,
        )
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return ComponentHealth(
            status=HealthStatus.UNHEALTHY,
            message=str(e),
        )


async def check_llm_health() -> ComponentHealth:
    """检查 LLM 服务健康状态"""
    try:
        # 简单检查配置是否存在
        if settings.llm.api_key:
            return ComponentHealth(
                status=HealthStatus.HEALTHY,
                message="LLM API key configured",
            )
        else:
            return ComponentHealth(
                status=HealthStatus.DEGRADED,
                message="LLM API key not configured",
            )
    except Exception as e:
        logger.error(f"LLM health check failed: {e}")
        return ComponentHealth(
            status=HealthStatus.UNHEALTHY,
            message=str(e),
        )


async def get_health_status(include_details: bool = True) -> HealthResponse:
    """
    获取应用健康状态

    Args:
        include_details: 是否包含组件详情

    Returns:
        健康检查响应
    """
    components = {}
    overall_status = HealthStatus.HEALTHY

    if include_details:
        # 检查数据库
        db_health = await check_database_health()
        components["database"] = db_health
        if db_health.status == HealthStatus.UNHEALTHY:
            overall_status = HealthStatus.UNHEALTHY
        elif db_health.status == HealthStatus.DEGRADED and overall_status == HealthStatus.HEALTHY:
            overall_status = HealthStatus.DEGRADED

        # 检查 Redis
        redis_health = await check_redis_health()
        components["redis"] = redis_health
        if redis_health.status == HealthStatus.UNHEALTHY:
            overall_status = HealthStatus.UNHEALTHY
        elif redis_health.status == HealthStatus.DEGRADED and overall_status == HealthStatus.HEALTHY:
            overall_status = HealthStatus.DEGRADED

        # 检查 LLM
        llm_health = await check_llm_health()
        components["llm"] = llm_health
        if llm_health.status == HealthStatus.DEGRADED and overall_status == HealthStatus.HEALTHY:
            overall_status = HealthStatus.DEGRADED

    return HealthResponse(
        status=overall_status,
        service=settings.app.name,
        version=settings.app.version,
        components=components if include_details else None,
    )


def setup_health_check(app: FastAPI) -> None:
    """
    设置健康检查端点

    Args:
        app: FastAPI 应用实例
    """
    if not settings.monitoring.health_check.enabled:
        logger.info("Health check disabled")
        return

    @app.get(
        settings.monitoring.health_check.endpoint,
        response_model=HealthResponse,
        tags=["health"],
    )
    async def health_check():
        """健康检查端点"""
        health = await get_health_status(
            include_details=settings.monitoring.health_check.include_details
        )

        # 根据状态设置 HTTP 状态码
        status_code = 200
        if health.status == HealthStatus.UNHEALTHY:
            status_code = 503
        elif health.status == HealthStatus.DEGRADED:
            status_code = 200  # 降级状态仍返回 200

        return Response(
            content=health.model_dump_json(),
            media_type="application/json",
            status_code=status_code,
        )

    # 简单的存活检查
    @app.get("/livez", include_in_schema=False)
    async def liveness():
        """存活检查"""
        return {"status": "alive"}

    # 就绪检查
    @app.get("/readyz", include_in_schema=False)
    async def readiness():
        """就绪检查"""
        health = await get_health_status(include_details=False)
        if health.status == HealthStatus.UNHEALTHY:
            return Response(
                content='{"status": "not ready"}',
                media_type="application/json",
                status_code=503,
            )
        return {"status": "ready"}

    logger.info(f"Health check enabled at {settings.monitoring.health_check.endpoint}")
