"""
请求上下文中间件

功能：
1. 解析请求 Header 中的关键参数（x-request-id, x-trace-id, x-user-id 等）
2. 生成 trace_id 用于链路追踪
3. 提供全局请求上下文，其他代码可随时访问
4. 在响应 Header 中添加追踪信息
"""

import time
import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Callable, Optional, Dict, Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import setup_logger
from app.core.snowflake import generate_id_str

logger = setup_logger(__name__)


@dataclass
class RequestContext:
    """
    请求上下文数据类

    存储请求相关的所有上下文信息，可在整个请求生命周期内访问
    """
    # 追踪标识
    request_id: str = ""          # 客户端传入的请求ID
    trace_id: str = ""            # 链路追踪ID（雪花算法生成）
    span_id: str = ""             # 当前 span ID

    # 用户信息
    user_id: str = ""             # 用户ID
    device_id: str = ""           # 设备ID

    # 客户端信息
    client_ip: str = ""           # 客户端IP
    user_agent: str = ""          # User-Agent
    platform: str = ""            # 平台 (ios/android/web)
    app_version: str = ""         # App版本

    # 请求信息
    method: str = ""              # 请求方法
    path: str = ""                # 请求路径
    start_time: float = 0.0       # 请求开始时间

    # 扩展数据
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "request_id": self.request_id,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "user_id": self.user_id,
            "device_id": self.device_id,
            "client_ip": self.client_ip,
            "user_agent": self.user_agent,
            "platform": self.platform,
            "app_version": self.app_version,
            "method": self.method,
            "path": self.path,
            **self.extra,
        }

    def set_extra(self, key: str, value: Any) -> None:
        """设置扩展数据"""
        self.extra[key] = value

    def get_extra(self, key: str, default: Any = None) -> Any:
        """获取扩展数据"""
        return self.extra.get(key, default)


# 全局上下文变量
_request_context: ContextVar[Optional[RequestContext]] = ContextVar(
    "request_context", default=None
)


def get_request_context() -> Optional[RequestContext]:
    """
    获取当前请求上下文

    Returns:
        RequestContext 或 None（如果不在请求上下文中）

    Usage:
        from app.middleware.request_context import get_request_context

        ctx = get_request_context()
        if ctx:
            print(f"当前请求 trace_id: {ctx.trace_id}")
            print(f"当前用户: {ctx.user_id}")
    """
    return _request_context.get()


def get_trace_id() -> str:
    """获取当前 trace_id，常用于日志记录"""
    ctx = get_request_context()
    return ctx.trace_id if ctx else ""


def get_user_id() -> str:
    """获取当前用户 ID"""
    ctx = get_request_context()
    return ctx.user_id if ctx else ""


def get_request_id() -> str:
    """获取当前请求 ID"""
    ctx = get_request_context()
    return ctx.request_id if ctx else ""


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    请求上下文中间件

    解析请求 Header，构建上下文，在响应中添加追踪信息

    支持的请求 Header：
    - X-Request-ID: 客户端请求ID
    - X-Trace-ID: 链路追踪ID（可选，不传则自动生成）
    - X-User-ID: 用户ID
    - X-Device-ID: 设备ID
    - X-Platform: 平台标识 (ios/android/web)
    - X-App-Version: App版本号

    响应 Header：
    - X-Request-ID: 请求ID
    - X-Trace-ID: 链路追踪ID
    - X-Process-Time: 处理时间（毫秒）
    """

    # 需要解析的 Header 映射
    HEADER_MAPPING = {
        "x-request-id": "request_id",
        "x-trace-id": "trace_id",
        "x-span-id": "span_id",
        "x-user-id": "user_id",
        "x-device-id": "device_id",
        "x-platform": "platform",
        "x-app-version": "app_version",
    }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 构建请求上下文
        ctx = self._build_context(request)

        # 设置上下文变量
        token = _request_context.set(ctx)

        try:
            # 处理请求
            response = await call_next(request)

            # 计算处理时间
            process_time_ms = round((time.time() - ctx.start_time) * 1000, 2)

            # 添加响应 Header
            response.headers["X-Request-ID"] = ctx.request_id
            response.headers["X-Trace-ID"] = ctx.trace_id
            response.headers["X-Process-Time"] = str(process_time_ms)

            return response

        except Exception as e:
            logger.error(
                f"请求处理异常: trace_id={ctx.trace_id}, path={ctx.path}, error={str(e)}"
            )
            raise
        finally:
            # 重置上下文
            _request_context.reset(token)

    def _build_context(self, request: Request) -> RequestContext:
        """从请求中构建上下文"""
        ctx = RequestContext()
        ctx.start_time = time.time()
        ctx.method = request.method
        ctx.path = request.url.path

        # 解析 Header
        for header_name, attr_name in self.HEADER_MAPPING.items():
            value = request.headers.get(header_name, "")
            if value:
                setattr(ctx, attr_name, value)

        # 如果没有 request_id，生成一个
        if not ctx.request_id:
            ctx.request_id = generate_id_str()

        # 如果没有 trace_id，使用 request_id 或生成新的
        if not ctx.trace_id:
            ctx.trace_id = ctx.request_id

        # 如果没有 span_id，生成一个
        if not ctx.span_id:
            ctx.span_id = generate_id_str()

        # 获取客户端 IP
        ctx.client_ip = self._get_client_ip(request)

        # 获取 User-Agent
        ctx.user_agent = request.headers.get("user-agent", "")

        return ctx

    def _get_client_ip(self, request: Request) -> str:
        """获取客户端真实 IP"""
        # 检查代理头（按优先级）
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # 直接连接的客户端
        if request.client:
            return request.client.host

        return "unknown"


# 日志过滤器，用于在日志中自动添加 trace_id
class TraceIdLogFilter:
    """
    日志过滤器，自动在日志中添加 trace_id

    Usage:
        import logging
        from app.middleware.request_context import TraceIdLogFilter

        handler = logging.StreamHandler()
        handler.addFilter(TraceIdLogFilter())
    """

    def filter(self, record):
        ctx = get_request_context()
        record.trace_id = ctx.trace_id if ctx else "-"
        record.request_id = ctx.request_id if ctx else "-"
        record.user_id = ctx.user_id if ctx else "-"
        return True
