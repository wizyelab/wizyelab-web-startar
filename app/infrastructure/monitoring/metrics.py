"""
监控打点模块

支持:
- Prometheus 指标收集
- 请求追踪
- 性能监控
"""

import time
from typing import Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST

from app.core.config import settings
from app.core.logging import setup_logger

logger = setup_logger(__name__)


# =============================================================================
# Prometheus 指标定义
# =============================================================================

# 请求计数器
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status_code"],
)

# 请求延迟直方图
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0],
)

# 活跃请求数
ACTIVE_REQUESTS = Gauge(
    "http_requests_active",
    "Number of active HTTP requests",
    ["method", "endpoint"],
)

# 请求大小直方图
REQUEST_SIZE = Histogram(
    "http_request_size_bytes",
    "HTTP request size in bytes",
    ["method", "endpoint"],
    buckets=[100, 1000, 10000, 100000, 1000000],
)

# 响应大小直方图
RESPONSE_SIZE = Histogram(
    "http_response_size_bytes",
    "HTTP response size in bytes",
    ["method", "endpoint"],
    buckets=[100, 1000, 10000, 100000, 1000000],
)

# 应用信息
APP_INFO = Info(
    "app_info",
    "Application information",
)

# Agent 调用计数
AGENT_CALLS = Counter(
    "agent_calls_total",
    "Total number of agent calls",
    ["agent_type", "status"],
)

# Agent 调用延迟
AGENT_LATENCY = Histogram(
    "agent_call_duration_seconds",
    "Agent call latency in seconds",
    ["agent_type"],
    buckets=[0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
)

# LLM 调用计数
LLM_CALLS = Counter(
    "llm_calls_total",
    "Total number of LLM calls",
    ["model", "status"],
)

# LLM Token 使用量
LLM_TOKENS = Counter(
    "llm_tokens_total",
    "Total number of LLM tokens used",
    ["model", "type"],  # type: prompt, completion
)

# 数据库连接数
DB_CONNECTIONS = Gauge(
    "db_connections_active",
    "Number of active database connections",
)

# Redis 连接数
REDIS_CONNECTIONS = Gauge(
    "redis_connections_active",
    "Number of active Redis connections",
)

# 缓存命中率
CACHE_HITS = Counter(
    "cache_hits_total",
    "Total number of cache hits",
    ["cache_type"],  # local, redis
)

CACHE_MISSES = Counter(
    "cache_misses_total",
    "Total number of cache misses",
    ["cache_type"],
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Prometheus 指标中间件

    收集 HTTP 请求的各项指标
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 跳过 metrics 端点自身
        if request.url.path == settings.monitoring.prometheus.endpoint:
            return await call_next(request)

        method = request.method
        endpoint = self._get_endpoint(request)

        # 记录活跃请求
        ACTIVE_REQUESTS.labels(method=method, endpoint=endpoint).inc()

        # 记录请求大小
        content_length = request.headers.get("content-length")
        if content_length:
            REQUEST_SIZE.labels(method=method, endpoint=endpoint).observe(int(content_length))

        # 记录请求开始时间
        start_time = time.time()

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            status_code = 500
            raise
        finally:
            # 记录请求延迟
            latency = time.time() - start_time
            REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(latency)

            # 记录请求计数
            REQUEST_COUNT.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code,
            ).inc()

            # 减少活跃请求计数
            ACTIVE_REQUESTS.labels(method=method, endpoint=endpoint).dec()

        # 记录响应大小
        response_size = response.headers.get("content-length")
        if response_size:
            RESPONSE_SIZE.labels(method=method, endpoint=endpoint).observe(int(response_size))

        return response

    def _get_endpoint(self, request: Request) -> str:
        """获取端点路径（去除路径参数）"""
        # 获取匹配的路由
        if hasattr(request, "scope") and "route" in request.scope:
            route = request.scope["route"]
            if hasattr(route, "path"):
                return route.path

        # 回退到原始路径
        return request.url.path


def setup_metrics(app: FastAPI) -> None:
    """
    设置 Prometheus 指标

    Args:
        app: FastAPI 应用实例
    """
    if not settings.monitoring.prometheus.enabled:
        logger.info("Prometheus metrics disabled")
        return

    # 设置应用信息
    APP_INFO.info({
        "name": settings.app.name,
        "version": settings.app.version,
    })

    # 添加中间件
    app.add_middleware(MetricsMiddleware)

    # 添加 metrics 端点
    @app.get(settings.monitoring.prometheus.endpoint, include_in_schema=False)
    async def metrics():
        """Prometheus 指标端点"""
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST,
        )

    logger.info(f"Prometheus metrics enabled at {settings.monitoring.prometheus.endpoint}")


# =============================================================================
# 打点辅助函数
# =============================================================================

def record_agent_call(agent_type: str, success: bool, latency: float) -> None:
    """
    记录 Agent 调用

    Args:
        agent_type: Agent 类型
        success: 是否成功
        latency: 延迟时间（秒）
    """
    status = "success" if success else "error"
    AGENT_CALLS.labels(agent_type=agent_type, status=status).inc()
    AGENT_LATENCY.labels(agent_type=agent_type).observe(latency)


def record_llm_call(model: str, success: bool, prompt_tokens: int = 0, completion_tokens: int = 0) -> None:
    """
    记录 LLM 调用

    Args:
        model: 模型名称
        success: 是否成功
        prompt_tokens: 提示词 token 数
        completion_tokens: 完成 token 数
    """
    status = "success" if success else "error"
    LLM_CALLS.labels(model=model, status=status).inc()

    if prompt_tokens > 0:
        LLM_TOKENS.labels(model=model, type="prompt").inc(prompt_tokens)
    if completion_tokens > 0:
        LLM_TOKENS.labels(model=model, type="completion").inc(completion_tokens)


def record_cache_access(cache_type: str, hit: bool) -> None:
    """
    记录缓存访问

    Args:
        cache_type: 缓存类型 (local, redis)
        hit: 是否命中
    """
    if hit:
        CACHE_HITS.labels(cache_type=cache_type).inc()
    else:
        CACHE_MISSES.labels(cache_type=cache_type).inc()


def set_db_connections(count: int) -> None:
    """设置数据库连接数"""
    DB_CONNECTIONS.set(count)


def set_redis_connections(count: int) -> None:
    """设置 Redis 连接数"""
    REDIS_CONNECTIONS.set(count)
