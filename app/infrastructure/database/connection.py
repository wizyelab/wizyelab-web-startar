"""
数据库连接模块

支持同步和异步数据库操作，基于 SQLAlchemy 2.0
"""

from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator

from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import Session, sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool, NullPool

from app.core.config import settings
from app.core.logging import setup_logger

logger = setup_logger(__name__)

# 创建 Base 类
Base = declarative_base()

# =============================================================================
# 同步数据库引擎
# =============================================================================
engine = create_engine(
    settings.database_url,
    poolclass=QueuePool,
    pool_size=settings.database.pool_size,
    max_overflow=settings.database.max_overflow,
    pool_timeout=settings.database.pool_timeout,
    pool_recycle=settings.database.pool_recycle,
    echo=settings.database.echo,
    pool_pre_ping=True,  # 自动检测连接是否有效
)

# 同步 Session 工厂
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# =============================================================================
# 异步数据库引擎（延迟初始化，避免事件循环不匹配问题）
# =============================================================================
async_engine = None
AsyncSessionLocal = None
_async_engine_initialized = False


async def init_async_engine():
    """
    初始化异步数据库引擎

    必须在事件循环运行后调用（如 FastAPI lifespan 中），
    以确保引擎绑定到正确的事件循环。

    使用 NullPool 禁用连接池，避免在多 worker 模式下
    连接绑定到错误的事件循环（BaseHTTPMiddleware 兼容性问题）。
    """
    global async_engine, AsyncSessionLocal, _async_engine_initialized

    if _async_engine_initialized:
        logger.debug("Async engine already initialized")
        return

    logger.info("Initializing async database engine...")

    # 使用 NullPool 禁用连接池，每次操作创建新连接
    # 这样可以避免连接绑定到错误的事件循环
    async_engine = create_async_engine(
        settings.database_async_url,
        poolclass=NullPool,  # 禁用连接池，解决事件循环不匹配问题
        echo=settings.database.echo,
    )

    AsyncSessionLocal = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )

    _async_engine_initialized = True
    logger.info("Async database engine initialized successfully (using NullPool)")


# =============================================================================
# 数据库连接事件监听
# =============================================================================
@event.listens_for(engine, "connect")
def on_connect(dbapi_connection, connection_record):
    """数据库连接时的回调"""
    logger.debug("Database connection established")


@event.listens_for(engine, "checkout")
def on_checkout(dbapi_connection, connection_record, connection_proxy):
    """从连接池获取连接时的回调"""
    logger.debug("Database connection checked out from pool")


@event.listens_for(engine, "checkin")
def on_checkin(dbapi_connection, connection_record):
    """连接返回连接池时的回调"""
    logger.debug("Database connection returned to pool")


# =============================================================================
# 依赖注入函数
# =============================================================================
def get_db() -> Generator[Session, None, None]:
    """
    获取同步数据库会话

    用于 FastAPI 依赖注入:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取异步数据库会话

    用于 FastAPI 依赖注入:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_async_db)):
            ...
    """
    if not _async_engine_initialized:
        raise RuntimeError(
            "Async database engine not initialized. "
            "Call init_async_engine() in FastAPI lifespan first."
        )

    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    获取同步数据库会话的上下文管理器

    用于非 FastAPI 场景:
        with get_db_context() as db:
            ...
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@asynccontextmanager
async def get_async_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    获取异步数据库会话的上下文管理器

    用于非 FastAPI 场景:
        async with get_async_db_context() as db:
            ...
    """
    if not _async_engine_initialized:
        raise RuntimeError(
            "Async database engine not initialized. "
            "Call init_async_engine() in FastAPI lifespan first."
        )

    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# =============================================================================
# 数据库初始化
# =============================================================================
def init_db():
    """
    初始化数据库，创建所有表
    """
    logger.info("Initializing database...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully")


async def async_init_db():
    """
    异步初始化数据库，创建所有表
    """
    if not _async_engine_initialized:
        raise RuntimeError(
            "Async database engine not initialized. "
            "Call init_async_engine() in FastAPI lifespan first."
        )

    logger.info("Initializing database asynchronously...")
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized successfully")


async def close_db():
    """
    关闭数据库连接
    """
    global _async_engine_initialized

    logger.info("Closing database connections...")
    engine.dispose()

    if async_engine:
        await async_engine.dispose()
        _async_engine_initialized = False

    logger.info("Database connections closed")
