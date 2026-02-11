"""
Alembic 迁移环境配置

从项目配置中读取数据库 URL，导入所有 Model 以支持 autogenerate。
"""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# Alembic Config 对象
config = context.config

# 配置日志
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ---------------------------------------------------------------------------
# 导入项目配置和所有 Model
# ---------------------------------------------------------------------------
from app.core.config import settings
from app.infrastructure.database.connection import Base

# 导入所有 Model，确保它们注册到 Base.metadata
import app.models.user          # noqa: F401
import app.models.profile       # noqa: F401
import app.models.multimedia    # noqa: F401

# 设置 target_metadata 用于 autogenerate
target_metadata = Base.metadata

# 从项目配置动态设置数据库 URL
config.set_main_option("sqlalchemy.url", settings.database_url)


# ---------------------------------------------------------------------------
# 离线模式：生成 SQL 脚本而不连接数据库
# ---------------------------------------------------------------------------
def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# 在线模式：连接数据库执行迁移
# ---------------------------------------------------------------------------
def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
