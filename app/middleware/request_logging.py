"""请求日志中间件"""

import time
import json
from typing import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

from app.core.config import settings
from app.core.logging import setup_logger

logger = setup_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    请求日志中间件

    支持:
    - 请求/响应日志记录
    - 结构化日志（JSON 格式）
    - 请求追踪 ID
    """

    async def dispatch(self, request: Request, call_next: Callable):
        # 生成请求 ID
        request_id = request.headers.get("X-Request-ID", str(time.time_ns()))

        # 记录请求开始时间
        start_time = time.time()

        # 提取请求信息
        request_info = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "query_params": str(request.query_params),
            "client_ip": self._get_client_ip(request),
            "user_agent": request.headers.get("User-Agent", ""),
        }

        # 记录请求日志
        if settings.logging.json_format:
            logger.info(f"Request started: {json.dumps(request_info)}")
        else:
            logger.info(f"Request: {request.method} {request.url.path}")

        # 处理请求
        try:
            response = await call_next(request)
            status_code = response.status_code
            error = None
        except Exception as e:
            status_code = 500
            error = str(e)
            raise
        finally:
            # 计算处理时间
            process_time = time.time() - start_time

            # 记录响应日志
            response_info = {
                **request_info,
                "status_code": status_code,
                "process_time_ms": round(process_time * 1000, 2),
            }

            if error:
                response_info["error"] = error

            if settings.logging.json_format:
                log_message = json.dumps(response_info)
            else:
                log_message = (
                    f"Response: {request.method} {request.url.path} - "
                    f"Status: {status_code} - "
                    f"Time: {process_time:.3f}s"
                )

            if status_code >= 500:
                logger.error(log_message)
            elif status_code >= 400:
                logger.warning(log_message)
            else:
                logger.info(log_message)

        # 添加响应头
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))

        return response

    def _get_client_ip(self, request: Request) -> str:
        """获取客户端 IP"""
        # 检查代理头
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # 直接连接的客户端
        if request.client:
            return request.client.host

        return "unknown"
