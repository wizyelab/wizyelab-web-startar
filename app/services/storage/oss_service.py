"""OSS 服务层

提供文件存储的业务逻辑封装，包括：
- 文件上传（支持直传和服务端中转）
- 文件下载
- 文件管理
- 签名 URL 生成
"""

import logging
import mimetypes
import os
import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from io import BytesIO
from typing import BinaryIO, Dict, List, Optional, Union

from fastapi import UploadFile

from app.core.config import settings
from app.infrastructure.storage.oss_client import OSSClient, oss_client

logger = logging.getLogger(__name__)


class FileCategory(str, Enum):
    """文件分类"""
    IMAGE = "images"
    VIDEO = "videos"
    AUDIO = "audios"
    DOCUMENT = "documents"
    OTHER = "others"


@dataclass
class UploadResult:
    """上传结果"""
    key: str
    url: str
    filename: str
    size: int
    content_type: str
    etag: str


@dataclass
class FileInfo:
    """文件信息"""
    key: str
    size: int
    last_modified: datetime
    etag: str
    content_type: Optional[str] = None


class OSSService:
    """
    OSS 服务类

    提供文件存储的业务逻辑封装
    """

    # MIME 类型映射到文件分类
    CATEGORY_MAPPING = {
        "image": FileCategory.IMAGE,
        "video": FileCategory.VIDEO,
        "audio": FileCategory.AUDIO,
        "application/pdf": FileCategory.DOCUMENT,
        "application/msword": FileCategory.DOCUMENT,
        "application/vnd.openxmlformats": FileCategory.DOCUMENT,
        "text": FileCategory.DOCUMENT,
    }

    def __init__(self, client: Optional[OSSClient] = None):
        self._client = client or oss_client

    @property
    def client(self) -> OSSClient:
        """获取 OSS 客户端"""
        if not self._client._initialized:
            self._client.init()
        return self._client

    def _get_category(self, content_type: str) -> FileCategory:
        """根据内容类型获取文件分类"""
        if not content_type:
            return FileCategory.OTHER

        for prefix, category in self.CATEGORY_MAPPING.items():
            if content_type.startswith(prefix):
                return category
        return FileCategory.OTHER

    def _generate_key(
        self,
        filename: str,
        category: Optional[FileCategory] = None,
        prefix: str = "",
        use_uuid: bool = True
    ) -> str:
        """
        生成文件存储 key

        格式: {prefix}/{category}/{date}/{uuid}_{filename}
        例如: uploads/images/2024/01/15/abc123_photo.jpg

        Args:
            filename: 原始文件名
            category: 文件分类
            prefix: 自定义前缀
            use_uuid: 是否使用 UUID

        Returns:
            生成的 key
        """
        # 获取文件扩展名
        _, ext = os.path.splitext(filename)
        ext = ext.lower()

        # 生成日期路径
        date_path = datetime.now().strftime("%Y/%m/%d")

        # 生成文件名
        if use_uuid:
            unique_id = uuid.uuid4().hex[:12]
            safe_filename = f"{unique_id}{ext}"
        else:
            safe_filename = filename

        # 组装 key
        parts = []
        if prefix:
            parts.append(prefix.strip("/"))
        if category:
            parts.append(category.value)
        parts.append(date_path)
        parts.append(safe_filename)

        return "/".join(parts)

    def _guess_content_type(self, filename: str) -> str:
        """猜测文件的内容类型"""
        content_type, _ = mimetypes.guess_type(filename)
        return content_type or "application/octet-stream"

    # ========================= 上传操作 =========================

    async def upload_file(
        self,
        file: UploadFile,
        prefix: str = "uploads",
        category: Optional[FileCategory] = None,
        custom_key: Optional[str] = None,
        progress_callback: Optional[callable] = None
    ) -> UploadResult:
        """
        上传文件（FastAPI UploadFile）

        Args:
            file: FastAPI 上传文件对象
            prefix: 存储前缀
            category: 文件分类，如果不指定则自动检测
            custom_key: 自定义 key，如果指定则忽略自动生成
            progress_callback: 进度回调

        Returns:
            上传结果
        """
        filename = file.filename or "unknown"
        content_type = file.content_type or self._guess_content_type(filename)

        # 自动检测分类
        if category is None:
            category = self._get_category(content_type)

        # 生成 key
        key = custom_key or self._generate_key(filename, category, prefix)

        # 读取文件内容
        content = await file.read()
        size = len(content)

        # 上传
        result = await self.client.put_object_async(
            key,
            content,
            content_type=content_type,
            progress_callback=progress_callback
        )

        # 生成访问 URL
        url = self.get_public_url(key)

        logger.info(f"File uploaded: {filename} -> {key}, size: {size}")

        return UploadResult(
            key=key,
            url=url,
            filename=filename,
            size=size,
            content_type=content_type,
            etag=result.etag
        )

    async def upload_bytes(
        self,
        data: bytes,
        filename: str,
        prefix: str = "uploads",
        category: Optional[FileCategory] = None,
        content_type: Optional[str] = None,
        custom_key: Optional[str] = None,
        progress_callback: Optional[callable] = None
    ) -> UploadResult:
        """
        上传字节数据

        Args:
            data: 字节数据
            filename: 文件名
            prefix: 存储前缀
            category: 文件分类
            content_type: 内容类型
            custom_key: 自定义 key
            progress_callback: 进度回调

        Returns:
            上传结果
        """
        _content_type = content_type or self._guess_content_type(filename)

        if category is None:
            category = self._get_category(_content_type)

        key = custom_key or self._generate_key(filename, category, prefix)

        result = await self.client.put_object_async(
            key,
            data,
            content_type=_content_type,
            progress_callback=progress_callback
        )

        url = self.get_public_url(key)

        return UploadResult(
            key=key,
            url=url,
            filename=filename,
            size=len(data),
            content_type=_content_type,
            etag=result.etag
        )

    async def upload_local_file(
        self,
        file_path: str,
        prefix: str = "uploads",
        category: Optional[FileCategory] = None,
        custom_key: Optional[str] = None,
        progress_callback: Optional[callable] = None
    ) -> UploadResult:
        """
        上传本地文件

        Args:
            file_path: 本地文件路径
            prefix: 存储前缀
            category: 文件分类
            custom_key: 自定义 key
            progress_callback: 进度回调

        Returns:
            上传结果
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        filename = os.path.basename(file_path)
        content_type = self._guess_content_type(filename)
        size = os.path.getsize(file_path)

        if category is None:
            category = self._get_category(content_type)

        key = custom_key or self._generate_key(filename, category, prefix)

        result = await self.client.upload_file_async(
            key,
            file_path,
            content_type=content_type,
            progress_callback=progress_callback
        )

        url = self.get_public_url(key)

        return UploadResult(
            key=key,
            url=url,
            filename=filename,
            size=size,
            content_type=content_type,
            etag=result.etag
        )

    # ========================= 下载操作 =========================

    async def download_file(
        self,
        key: str,
        progress_callback: Optional[callable] = None
    ) -> bytes:
        """
        下载文件到内存

        Args:
            key: 对象 key
            progress_callback: 进度回调

        Returns:
            文件内容
        """
        result = await self.client.get_object_async(key, progress_callback=progress_callback)
        return result.read()

    async def download_to_file(
        self,
        key: str,
        file_path: str,
        progress_callback: Optional[callable] = None
    ) -> str:
        """
        下载文件到本地

        Args:
            key: 对象 key
            file_path: 本地保存路径
            progress_callback: 进度回调

        Returns:
            本地文件路径
        """
        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        await self.client.download_file_async(
            key,
            file_path,
            progress_callback=progress_callback
        )
        return file_path

    # ========================= 文件操作 =========================

    async def delete_file(self, key: str) -> bool:
        """
        删除文件

        Args:
            key: 对象 key

        Returns:
            是否成功
        """
        try:
            await self.client.delete_object_async(key)
            logger.info(f"File deleted: {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete file {key}: {e}")
            return False

    async def delete_files(self, keys: List[str]) -> Dict[str, bool]:
        """
        批量删除文件

        Args:
            keys: 对象 key 列表

        Returns:
            删除结果字典
        """
        try:
            await self.client.batch_delete_objects_async(keys)
            return {key: True for key in keys}
        except Exception as e:
            logger.error(f"Failed to batch delete files: {e}")
            return {key: False for key in keys}

    async def file_exists(self, key: str) -> bool:
        """
        检查文件是否存在

        Args:
            key: 对象 key

        Returns:
            是否存在
        """
        return await self.client.object_exists_async(key)

    async def get_file_info(self, key: str) -> Optional[FileInfo]:
        """
        获取文件信息

        Args:
            key: 对象 key

        Returns:
            文件信息，不存在返回 None
        """
        try:
            meta = await self.client.head_object_async(key)
            return FileInfo(
                key=key,
                size=meta.content_length,
                last_modified=meta.last_modified,
                etag=meta.etag,
                content_type=meta.content_type
            )
        except Exception:
            return None

    async def copy_file(
        self,
        source_key: str,
        target_key: str
    ) -> bool:
        """
        复制文件

        Args:
            source_key: 源文件 key
            target_key: 目标文件 key

        Returns:
            是否成功
        """
        try:
            await self.client.copy_object_async(source_key, target_key)
            logger.info(f"File copied: {source_key} -> {target_key}")
            return True
        except Exception as e:
            logger.error(f"Failed to copy file: {e}")
            return False

    async def move_file(
        self,
        source_key: str,
        target_key: str
    ) -> bool:
        """
        移动文件

        Args:
            source_key: 源文件 key
            target_key: 目标文件 key

        Returns:
            是否成功
        """
        if await self.copy_file(source_key, target_key):
            return await self.delete_file(source_key)
        return False

    # ========================= 列表操作 =========================

    async def list_files(
        self,
        prefix: str = "",
        max_keys: int = 100,
        marker: str = ""
    ) -> List[FileInfo]:
        """
        列举文件

        Args:
            prefix: 前缀过滤
            max_keys: 最大返回数量
            marker: 起始位置

        Returns:
            文件信息列表
        """
        result = await self.client.list_objects_async(
            prefix=prefix,
            max_keys=max_keys,
            marker=marker
        )

        files = []
        for obj in result.object_list:
            files.append(FileInfo(
                key=obj.key,
                size=obj.size,
                last_modified=obj.last_modified,
                etag=obj.etag
            ))
        return files

    # ========================= URL 生成 =========================

    def get_public_url(self, key: str) -> str:
        """
        获取公开访问 URL（需要 Bucket 设置为公开读）

        Args:
            key: 对象 key

        Returns:
            公开 URL
        """
        config = settings.oss
        protocol = "https" if config.use_https else "http"
        return f"{protocol}://{config.bucket_name}.{config.endpoint}/{key}"

    def get_signed_url(
        self,
        key: str,
        expires: Optional[int] = None,
        for_download: bool = False,
        filename: Optional[str] = None
    ) -> str:
        """
        获取签名 URL

        Args:
            key: 对象 key
            expires: 过期时间（秒）
            for_download: 是否用于下载（设置 Content-Disposition）
            filename: 下载时的文件名

        Returns:
            签名 URL
        """
        if for_download:
            return self.client.get_download_url(key, expires, filename)
        return self.client.sign_url("GET", key, expires)

    def get_upload_url(
        self,
        key: str,
        expires: Optional[int] = None,
        content_type: Optional[str] = None
    ) -> str:
        """
        获取上传 URL（用于客户端直传）

        Args:
            key: 对象 key
            expires: 过期时间（秒）
            content_type: 内容类型

        Returns:
            上传 URL
        """
        return self.client.get_upload_url(key, expires, content_type)

    def generate_upload_key(
        self,
        filename: str,
        prefix: str = "uploads",
        category: Optional[FileCategory] = None
    ) -> str:
        """
        预生成上传 key（用于客户端直传场景）

        Args:
            filename: 文件名
            prefix: 存储前缀
            category: 文件分类

        Returns:
            生成的 key
        """
        if category is None:
            content_type = self._guess_content_type(filename)
            category = self._get_category(content_type)
        return self._generate_key(filename, category, prefix)


# 全局服务实例
oss_service = OSSService()
