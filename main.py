"""FastAPI 应用入口文件"""

import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from app.core.config import settings
from app.api.router import api_router
from app.middleware.cors import setup_cors
from app.middleware.request_logging import LoggingMiddleware
from app.middleware.rate_limit import setup_rate_limit
from app.middleware.request_context import RequestContextMiddleware
from app.infrastructure.monitoring.metrics import setup_metrics
from app.infrastructure.monitoring.health import setup_health_check
from app.core.logging import setup_logger

# 设置日志
logger = setup_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理

    启动时:
    - 初始化异步数据库引擎（必须在事件循环运行后）
    - 初始化数据库连接
    - 初始化 Redis 连接

    关闭时:
    - 关闭数据库连接
    - 关闭 Redis 连接
    """
    logger.info("Starting application...")

    # 初始化数据库（同步引擎，先于异步引擎）
    try:
        from app.infrastructure.database.connection import init_db
        init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize database: {e}")

    # 初始化异步数据库引擎（必须在事件循环运行后）
    try:
        from app.infrastructure.database.connection import init_async_engine
        await init_async_engine()
        logger.info("Async database engine initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize async database engine: {e}")

    # 初始化 Redis
    try:
        from app.infrastructure.cache.redis_client import init_redis
        await init_redis()
        logger.info("Redis initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize Redis: {e}")

    # 初始化 OSS
    try:
        from app.infrastructure.storage.oss_client import init_oss
        init_oss()
        logger.info("OSS initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize OSS: {e}")

    # 初始化 OSS CORS（解决前端直传跨域问题）
    try:
        from app.infrastructure.storage.oss_client import init_oss_cors
        init_oss_cors()
        logger.info("OSS CORS initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize OSS CORS: {e}")

    # Firebase 按需初始化（首次使用时自动初始化）

    logger.info("Application started successfully")

    yield

    # 关闭连接
    logger.info("Shutting down application...")

    try:
        from app.infrastructure.database.connection import close_db
        await close_db()
        logger.info("Database connections closed")
    except Exception as e:
        logger.warning(f"Error closing database: {e}")

    try:
        from app.infrastructure.cache.redis_client import close_redis
        await close_redis()
        logger.info("Redis connections closed")
    except Exception as e:
        logger.warning(f"Error closing Redis: {e}")

    try:
        from app.infrastructure.storage.oss_client import close_oss
        close_oss()
        logger.info("OSS client closed")
    except Exception as e:
        logger.warning(f"Error closing OSS: {e}")

    logger.info("Application shutdown complete")


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.app.name,
    version=settings.app.version,
    debug=settings.app.debug,
    description="Wizyelab AI-powered sports assistant API",
    lifespan=lifespan,
    docs_url=None,  # 使用自定义 Swagger UI
    redoc_url=None,  # 使用自定义 redoc 路由
)

# 设置中间件（注意：后添加的先执行）
setup_cors(app)
setup_rate_limit(app)  # 限流中间件
app.add_middleware(LoggingMiddleware)
app.add_middleware(RequestContextMiddleware)  # 请求上下文（最先执行）

# 设置监控
setup_metrics(app)
setup_health_check(app)

# 注册 API 路由
app.include_router(api_router, prefix=settings.app.api_prefix)


# 自定义 Swagger UI 和 ReDoc 路由，使用国内 CDN
if settings.app.debug:
    from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html

    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui():
        return get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=f"{settings.app.name} - Swagger UI",
            swagger_js_url="https://registry.npmmirror.com/swagger-ui-dist/latest/files/swagger-ui-bundle.js",
            swagger_css_url="https://registry.npmmirror.com/swagger-ui-dist/latest/files/swagger-ui.css",
        )

    @app.get("/redoc", include_in_schema=False)
    async def custom_redoc():
        return HTMLResponse("""
<!DOCTYPE html>
<html>
<head>
    <title>API Documentation - ReDoc</title>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { margin: 0; padding: 0; }
    </style>
</head>
<body>
    <redoc spec-url='/openapi.json'></redoc>
    <script src="https://registry.npmmirror.com/redoc/latest/files/bundles/redoc.standalone.js"></script>
</body>
</html>
        """)


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": f"Welcome to {settings.app.name}",
        "version": settings.app.version,
        "docs": "/docs" if settings.app.debug else "disabled",
    }


if __name__ == "__main__":
    # 从配置中读取 uvicorn 配置
    uvicorn.run(
        "main:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=settings.server.reload,
        workers=settings.server.workers if not settings.server.reload else 1,
        log_level=settings.server.log_level,
    )
