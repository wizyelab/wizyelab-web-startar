"""存储模块"""

from app.infrastructure.storage.oss_client import (
    OSSClient,
    oss_client,
    init_oss,
    close_oss,
    get_oss,
)

__all__ = [
    "OSSClient",
    "oss_client",
    "init_oss",
    "close_oss",
    "get_oss",
]
