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
    - 初始化数据库连接
    - 初始化 Redis 连接

    关闭时:
    - 关闭数据库连接
    - 关闭 Redis 连接
    """
    logger.info("Starting application...")

    # 初始化数据库
    try:
        from app.infrastructure.database.connection import init_db
        init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize database: {e}")

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
    docs_url="/docs" if settings.app.debug else None,
    redoc_url=None,  # 使用自定义 redoc 路由
)

# 设置中间件
setup_cors(app)
setup_rate_limit(app)  # 限流中间件
app.add_middleware(LoggingMiddleware)

# 设置监控
setup_metrics(app)
setup_health_check(app)

# 注册 API 路由
app.include_router(api_router, prefix=settings.app.api_prefix)


# 自定义 ReDoc 路由，使用国内 CDN
if settings.app.debug:
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
