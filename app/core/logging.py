"""日志工具模块"""

import logging
import sys
from typing import Optional
from pathlib import Path

from app.core.config import settings


def setup_logger(name: Optional[str] = None) -> logging.Logger:
    """
    设置日志记录器

    Args:
        name: 日志记录器名称，默认为根记录器

    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.logging.level.upper(), logging.INFO))

    # 如果已经有处理器，不重复添加
    if logger.handlers:
        return logger

    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.logging.level.upper(), logging.INFO))

    # 创建格式器
    formatter = logging.Formatter(settings.logging.format)
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)

    # 文件日志
    if settings.logging.log_to_file:
        log_path = Path(settings.logging.log_file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        from logging.handlers import RotatingFileHandler

        file_handler = RotatingFileHandler(
            settings.logging.log_file_path,
            maxBytes=settings.logging.log_max_size,
            backupCount=settings.logging.log_backup_count,
        )
        file_handler.setLevel(getattr(logging, settings.logging.level.upper(), logging.INFO))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
