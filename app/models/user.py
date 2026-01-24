"""
用户相关数据库模型

基于 database_cache_design.md 设计:
- 使用 bigint 自增主键
- 使用雪花算法生成业务ID（数字格式）
- 使用 bigint 存储毫秒级时间戳
"""

import uuid
import time
from typing import Optional

from sqlalchemy import Column, BigInteger, String, Text, SmallInteger, Index
from sqlalchemy.dialects.mysql import TINYINT

from app.infrastructure.database.connection import Base
from app.core.snowflake import generate_id_str


def generate_uuid() -> str:
    """生成UUID字符串（保留用于 session_id 等）"""
    return str(uuid.uuid4())


def generate_user_id() -> str:
    """生成用户ID（雪花算法，数字字符串格式）"""
    return generate_id_str()


def current_timestamp_ms() -> int:
    """获取当前毫秒级时间戳"""
    return int(time.time() * 1000)


class User(Base):
    """
    用户信息表

    对应 database_cache_design.md 中的 users 表
    """

    __tablename__ = "users"

    # 主键
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="自增主键")
    user_id = Column(
        String(20), unique=True, nullable=False, default=generate_user_id, comment="用户ID（雪花算法）"
    )

    # Firebase相关
    firebase_uid = Column(String(128), unique=True, nullable=True, comment="Firebase UID")

    # 基本信息
    phone = Column(String(20), unique=True, nullable=True, comment="手机号")
    email = Column(String(255), unique=True, nullable=True, comment="邮箱")
    user_name = Column(String(50), nullable=True, comment="用户名")
    avatar = Column(String(500), nullable=True, comment="头像URL")
    bio = Column(String(500), nullable=True, comment="个人简介")
    gender = Column(
        TINYINT(unsigned=True), nullable=False, default=0, comment="性别：0-未知，1-男，2-女，3-其他"
    )
    location = Column(String(100), nullable=True, comment="位置")

    # 登录相关
    login_provider = Column(
        String(20), nullable=True, comment="登录方式：google/apple/email/phone"
    )
    provider_token = Column(Text, nullable=True, comment="第三方登录Token")

    # 状态
    status = Column(
        TINYINT(unsigned=True), nullable=False, default=1, comment="状态：0-删除，1-正常"
    )

    # 扩展字段
    extra = Column(Text, nullable=True, comment="扩展字段")

    # 时间戳（毫秒）
    create_time = Column(
        BigInteger, nullable=False, default=current_timestamp_ms, comment="创建时间"
    )
    update_time = Column(
        BigInteger,
        nullable=False,
        default=current_timestamp_ms,
        onupdate=current_timestamp_ms,
        comment="更新时间",
    )

    # 索引
    __table_args__ = (
        Index("idx_create_time", "create_time"),
        {"comment": "用户信息表"},
    )

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "firebase_uid": self.firebase_uid,
            "phone": self.phone,
            "email": self.email,
            "user_name": self.user_name,
            "avatar": self.avatar,
            "bio": self.bio,
            "gender": self.gender,
            "location": self.location,
            "login_provider": self.login_provider,
            "status": self.status,
            "create_time": self.create_time,
            "update_time": self.update_time,
        }


class UserDevice(Base):
    """
    用户设备表

    对应 database_cache_design.md 中的 user_devices 表
    """

    __tablename__ = "user_devices"

    # 主键
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="自增主键")

    # 关联
    user_id = Column(String(20), nullable=False, comment="用户ID，关联users.user_id")
    device_id = Column(String(100), nullable=False, comment="设备ID")

    # 设备信息
    device_type = Column(String(20), nullable=True, comment="设备类型：ios/android")
    device_name = Column(String(100), nullable=True, comment="设备名称")
    push_token = Column(String(500), nullable=True, comment="推送Token")
    app_version = Column(String(20), nullable=True, comment="App版本")
    os_version = Column(String(20), nullable=True, comment="系统版本")

    # 状态
    is_active = Column(
        TINYINT(unsigned=True), nullable=False, default=1, comment="是否激活：0-否，1-是"
    )
    last_active_at = Column(BigInteger, nullable=True, comment="最后活跃时间")

    # 扩展字段
    extra = Column(Text, nullable=True, comment="扩展字段")

    # 时间戳（毫秒）
    create_time = Column(
        BigInteger, nullable=False, default=current_timestamp_ms, comment="创建时间"
    )
    update_time = Column(
        BigInteger,
        nullable=False,
        default=current_timestamp_ms,
        onupdate=current_timestamp_ms,
        comment="更新时间",
    )

    # 索引
    __table_args__ = (
        Index("uk_user_device", "user_id", "device_id", unique=True),
        Index("idx_user_id", "user_id"),
        Index("idx_device_id", "device_id"),
        {"comment": "用户设备表"},
    )

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "device_id": self.device_id,
            "device_type": self.device_type,
            "device_name": self.device_name,
            "is_active": self.is_active,
            "last_active_at": self.last_active_at,
            "create_time": self.create_time,
            "update_time": self.update_time,
        }


class UserSession(Base):
    """
    用户会话记录表

    对应 database_cache_design.md 中的 user_sessions 表
    """

    __tablename__ = "user_sessions"

    # 主键
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="自增主键")
    session_id = Column(
        String(36), unique=True, nullable=False, default=generate_uuid, comment="会话ID（UUID）"
    )

    # 关联
    user_id = Column(String(20), nullable=False, comment="用户ID，关联users.user_id")
    device_id = Column(String(100), nullable=False, comment="设备ID")

    # Token
    custom_token = Column(Text, nullable=True, comment="自定义Token")
    refresh_token = Column(Text, nullable=True, comment="刷新Token")

    # 登录信息
    login_ip = Column(String(50), nullable=True, comment="登录IP")
    login_location = Column(String(100), nullable=True, comment="登录地点")

    # 状态
    is_valid = Column(
        TINYINT(unsigned=True), nullable=False, default=1, comment="是否有效：0-否，1-是"
    )
    expires_at = Column(BigInteger, nullable=True, comment="过期时间")
    last_used_at = Column(BigInteger, nullable=True, comment="最后使用时间")

    # 扩展字段
    extra = Column(Text, nullable=True, comment="扩展字段")

    # 时间戳（毫秒）
    create_time = Column(
        BigInteger, nullable=False, default=current_timestamp_ms, comment="创建时间（即登录时间）"
    )
    update_time = Column(
        BigInteger,
        nullable=False,
        default=current_timestamp_ms,
        onupdate=current_timestamp_ms,
        comment="更新时间",
    )

    # 索引
    __table_args__ = (
        Index("idx_user_id", "user_id"),
        Index("idx_device_id", "device_id"),
        Index("idx_expires_at", "expires_at"),
        Index("idx_user_device", "user_id", "device_id"),
        {"comment": "用户会话记录表"},
    )

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "device_id": self.device_id,
            "is_valid": self.is_valid,
            "expires_at": self.expires_at,
            "last_used_at": self.last_used_at,
            "create_time": self.create_time,
            "update_time": self.update_time,
        }
