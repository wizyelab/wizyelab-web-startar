"""
数据库模型基类

提供常用的模型字段和方法
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, DateTime, Boolean, String
from sqlalchemy.orm import declared_attr

from app.infrastructure.database.connection import Base


class TimestampMixin:
    """时间戳混入类"""

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="创建时间"
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="更新时间"
    )


class SoftDeleteMixin:
    """软删除混入类"""

    is_deleted = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否删除"
    )
    deleted_at = Column(
        DateTime,
        nullable=True,
        comment="删除时间"
    )

    def soft_delete(self):
        """软删除"""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()


class BaseModel(Base, TimestampMixin):
    """
    基础模型类

    包含:
    - id: 主键
    - created_at: 创建时间
    - updated_at: 更新时间
    """
    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")

    @declared_attr
    def __tablename__(cls):
        """自动生成表名（类名转下划线格式）"""
        import re
        name = cls.__name__
        return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()

    def to_dict(self) -> dict:
        """转换为字典"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class BaseModelWithSoftDelete(BaseModel, SoftDeleteMixin):
    """
    带软删除的基础模型类

    包含:
    - id: 主键
    - created_at: 创建时间
    - updated_at: 更新时间
    - is_deleted: 是否删除
    - deleted_at: 删除时间
    """
    __abstract__ = True
