"""
请求上下文中间件

功能：
1. 解析请求 Header 中的关键参数（x-request-id, x-trace-id, x-user-id 等）
2. 生成 trace_id 用于链路追踪
3. 提供全局请求上下文，其他代码可随时访问
4. 在响应 Header 中添加追踪信息
5. 解析 session_id（从 Header 或 Cookie）获取 user_id
6. 登录成功后在响应中设置 session_id（Header 和 Cookie）
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
from app.core.config import settings

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
    session_id: str = ""          # Session ID

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
            "session_id": self.session_id,
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


def get_session_id() -> str:
    """获取当前 session ID"""
    ctx = get_request_context()
    return ctx.session_id if ctx else ""


# 用于在登录成功后设置 session_id 到响应中
_pending_session_id: ContextVar[Optional[str]] = ContextVar(
    "pending_session_id", default=None
)


def set_session_id_for_response(session_id: str) -> None:
    """
    设置 session_id，将在响应时添加到 Header 和 Cookie

    在登录成功后调用此函数，中间件会自动将 session_id 添加到响应中

    Usage:
        from app.middleware.request_context import set_session_id_for_response

        # 登录成功后
        set_session_id_for_response(session_id)
    """
    _pending_session_id.set(session_id)
    # 同时更新当前上下文
    ctx = get_request_context()
    if ctx:
        ctx.session_id = session_id


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    请求上下文中间件

    解析请求 Header，构建上下文，在响应中添加追踪信息

    支持的请求 Header：
    - X-Request-ID: 客户端请求ID
    - X-Trace-ID: 链路追踪ID（可选，不传则自动生成）
    - X-Session-ID: 会话ID（用于身份认证）
    - X-Device-ID: 设备ID
    - X-Platform: 平台标识 (ios/android/web)
    - X-App-Version: App版本号

    也支持从 Cookie 读取 session_id

    响应 Header：
    - X-Request-ID: 请求ID
    - X-Trace-ID: 链路追踪ID
    - X-Process-Time: 处理时间（毫秒）
    - X-Session-ID: 会话ID（登录成功时设置）
    """

    # 需要解析的 Header 映射
    HEADER_MAPPING = {
        "x-request-id": "request_id",
        "x-trace-id": "trace_id",
        "x-span-id": "span_id",
        "x-device-id": "device_id",
        "x-platform": "platform",
        "x-app-version": "app_version",
    }

    # 不需要 session 认证的路径前缀
    SKIP_AUTH_PATHS = {
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/metrics",
    }

    # 不需要 session 认证的路径（精确匹配）
    SKIP_AUTH_EXACT_PATHS = {
        "/joiiee/api/v1/internal/account/login",
        "/joiiee/api/v1/internal/account/send_verify_code",
    }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 构建请求上下文
        ctx = self._build_context(request)

        # 解析 session 获取 user_id（异步操作）
        await self._resolve_session(request, ctx)

        # 设置上下文变量
        token = _request_context.set(ctx)
        pending_token = _pending_session_id.set(None)

        try:
            # 处理请求
            response = await call_next(request)

            # 计算处理时间
            process_time_ms = round((time.time() - ctx.start_time) * 1000, 2)

            # 添加响应 Header
            response.headers["X-Request-ID"] = ctx.request_id
            response.headers["X-Trace-ID"] = ctx.trace_id
            response.headers["X-Process-Time"] = str(process_time_ms)

            # 如果有待设置的 session_id（登录成功），添加到响应
            pending_session = _pending_session_id.get()
            if pending_session:
                self._set_session_response(response, pending_session)

            return response

        except Exception as e:
            logger.error(
                f"请求处理异常: trace_id={ctx.trace_id}, path={ctx.path}, error={str(e)}"
            )
            raise
        finally:
            # 重置上下文
            _request_context.reset(token)
            _pending_session_id.reset(pending_token)

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

    async def _resolve_session(self, request: Request, ctx: RequestContext) -> None:
        """
        解析 session，从 Header 或 Cookie 获取 session_id，并查询 user_id

        优先级：Header > Cookie
        """
        # 检查是否需要跳过认证
        if self._should_skip_auth(request.url.path):
            return

        # 1. 优先从 Header 获取 session_id
        session_id = request.headers.get(settings.session.header_name.lower(), "")

        # 2. 如果 Header 没有，从 Cookie 获取
        if not session_id:
            session_id = request.cookies.get(settings.session.cookie_name, "")

        if not session_id:
            return

        ctx.session_id = session_id

        # 3. 从 Redis 获取 user_id
        try:
            from app.services.auth_service import auth_service
            user_id = await auth_service.get_user_id_by_session(session_id)
            if user_id:
                ctx.user_id = user_id
                logger.debug(f"Session 解析成功: session_id={session_id}, user_id={user_id}")
        except Exception as e:
            logger.warning(f"Session 解析失败: session_id={session_id}, error={e}")

    def _should_skip_auth(self, path: str) -> bool:
        """判断是否需要跳过认证"""
        # 精确匹配
        if path in self.SKIP_AUTH_EXACT_PATHS:
            return True

        # 前缀匹配
        for skip_path in self.SKIP_AUTH_PATHS:
            if path.startswith(skip_path):
                return True

        return False

    def _set_session_response(self, response: Response, session_id: str) -> None:
        """在响应中设置 session_id（Header 和 Cookie）"""
        # 设置 Header（移动端使用）
        response.headers[settings.session.header_name] = session_id

        # 设置 Cookie（Web 端使用）
        max_age = settings.session.ttl_days * 24 * 3600
        response.set_cookie(
            key=settings.session.cookie_name,
            value=session_id,
            max_age=max_age,
            httponly=settings.session.cookie_httponly,
            secure=settings.session.cookie_secure,
            samesite=settings.session.cookie_samesite,
        )

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
