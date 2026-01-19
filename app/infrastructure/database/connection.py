"""
数据库连接模块

支持同步和异步数据库操作，基于 SQLAlchemy 2.0
"""

from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator

from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import Session, sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool

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
# 异步数据库引擎
# =============================================================================
async_engine = create_async_engine(
    settings.database_async_url,
    pool_size=settings.database.pool_size,
    max_overflow=settings.database.max_overflow,
    pool_timeout=settings.database.pool_timeout,
    pool_recycle=settings.database.pool_recycle,
    echo=settings.database.echo,
    pool_pre_ping=True,
)

# 异步 Session 工厂
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


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
    logger.info("Initializing database asynchronously...")
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized successfully")


async def close_db():
    """
    关闭数据库连接
    """
    logger.info("Closing database connections...")
    engine.dispose()
    await async_engine.dispose()
    logger.info("Database connections closed")
