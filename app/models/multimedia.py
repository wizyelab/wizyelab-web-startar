"""
多媒体文件相关数据库模型

- 使用 bigint 自增主键
- 使用雪花算法生成业务ID（数字格式）
- 使用 bigint 存储毫秒级时间戳
"""

import time
from enum import IntEnum

from sqlalchemy import Column, BigInteger, String, Text, Integer, Index
from sqlalchemy.dialects.mysql import TINYINT

from app.infrastructure.database.connection import Base
from app.core.snowflake import generate_id_str


def current_timestamp_ms() -> int:
    """获取当前毫秒级时间戳"""
    return int(time.time() * 1000)


def generate_file_id() -> str:
    """生成文件ID（雪花算法，数字字符串格式）"""
    return generate_id_str()


# ========================= 枚举定义 =========================


class FileType(IntEnum):
    """文件类型枚举"""
    VIDEO = 1
    IMAGE = 2
    TEXT = 3
    AUDIO = 4
    OTHER = 5


class StorageType(IntEnum):
    """存储类型枚举"""
    LOCAL = 1
    OSS = 2
    S3 = 3
    COS = 4


class FileStatus(IntEnum):
    """文件状态枚举"""
    UPLOADING = 0
    SUCCESS = 1
    FAILED = 2
    DELETED = 3


# ========================= MIME 类型映射 =========================

TEXT_MIME_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/json",
    "application/xml",
}


def get_file_type_by_mime(mime_type: str) -> int:
    """根据 MIME 类型判断文件类型"""
    if not mime_type:
        return FileType.OTHER

    mime_type = mime_type.lower()

    if mime_type.startswith("video/"):
        return FileType.VIDEO
    elif mime_type.startswith("image/"):
        return FileType.IMAGE
    elif mime_type.startswith("text/") or mime_type in TEXT_MIME_TYPES:
        return FileType.TEXT
    elif mime_type.startswith("audio/"):
        return FileType.AUDIO
    else:
        return FileType.OTHER


def get_file_extension(filename: str) -> str:
    """从文件名提取扩展名"""
    if not filename or "." not in filename:
        return ""
    return filename.rsplit(".", 1)[-1].lower()


# ========================= 数据库模型 =========================


class Multimedia(Base):
    """多媒体文件表"""

    __tablename__ = "multimedia"

    # 主键
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="自增主键")
    file_id = Column(
        String(20), unique=True, nullable=False, default=generate_file_id, comment="文件ID（雪花算法）"
    )

    # 用户关联
    user_id = Column(String(20), nullable=False, comment="上传用户ID")

    # 文件基本信息
    file_type = Column(
        TINYINT(unsigned=True), nullable=False, comment="文件类型：1=视频,2=图片,3=文档,4=音频,5=其他"
    )
    file_name = Column(String(255), nullable=False, comment="原始文件名")
    file_ext = Column(String(20), nullable=False, default="", comment="文件扩展名")
    mime_type = Column(String(100), nullable=False, default="", comment="MIME类型")
    file_size = Column(BigInteger, nullable=False, default=0, comment="文件大小（字节）")

    # 存储信息
    storage_type = Column(
        TINYINT(unsigned=True), nullable=False, default=StorageType.OSS, comment="存储类型：1=本地,2=OSS,3=S3,4=COS"
    )
    original_uri = Column(String(500), nullable=False, default="", comment="原始存储路径（OSS key）")

    # 媒体属性
    width = Column(Integer, nullable=False, default=0, comment="宽度（图片/视频）")
    height = Column(Integer, nullable=False, default=0, comment="高度（图片/视频）")
    duration = Column(Integer, nullable=False, default=0, comment="时长秒数（视频/音频）")
    multi_imgs = Column(Text, nullable=True, comment="多尺寸图片（JSON格式）")

    # 状态与校验
    status = Column(
        TINYINT(unsigned=True), nullable=False, default=FileStatus.UPLOADING, comment="状态：0=上传中,1=成功,2=失败,3=已删除"
    )
    hash_md5 = Column(String(32), nullable=False, default="", comment="文件MD5（用于去重）")
    hash_sha256 = Column(String(64), nullable=False, default="", comment="文件SHA256")

    # 扩展字段
    extra = Column(Text, nullable=True, comment="扩展字段（JSON格式）")

    # 时间戳（毫秒）
    create_time = Column(
        BigInteger, nullable=False, default=current_timestamp_ms, comment="创建时间（毫秒时间戳）"
    )
    update_time = Column(
        BigInteger,
        nullable=False,
        default=current_timestamp_ms,
        onupdate=current_timestamp_ms,
        comment="更新时间（毫秒时间戳）",
    )

    # 索引
    __table_args__ = (
        Index("idx_user_type", "user_id", "file_type"),
        Index("idx_status", "status"),
        Index("idx_hash_md5", "hash_md5"),
        Index("idx_user_md5", "user_id", "hash_md5"),
        {"comment": "多媒体文件表"},
    )

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "file_id": self.file_id,
            "user_id": self.user_id,
            "file_type": self.file_type,
            "file_name": self.file_name,
            "file_ext": self.file_ext,
            "mime_type": self.mime_type,
            "file_size": self.file_size,
            "storage_type": self.storage_type,
            "original_uri": self.original_uri,
            "width": self.width,
            "height": self.height,
            "duration": self.duration,
            "multi_imgs": self.multi_imgs,
            "status": self.status,
            "hash_md5": self.hash_md5,
            "hash_sha256": self.hash_sha256,
            "create_time": self.create_time,
            "update_time": self.update_time,
        }
