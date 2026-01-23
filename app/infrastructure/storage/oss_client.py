"""阿里云 OSS 客户端模块

提供文件上传、下载、删除等操作的封装。
支持普通上传、分片上传、断点续传等功能。
"""

import logging
import os
from io import BytesIO
from typing import AsyncGenerator, BinaryIO, Dict, List, Optional, Union
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor

import oss2
from oss2 import SizedFileAdapter, determine_part_size
from oss2.models import PartInfo

from app.core.config import settings

logger = logging.getLogger(__name__)


class OSSClient:
    """
    阿里云 OSS 客户端

    支持的功能:
    - 普通文件上传/下载
    - 分片上传/下载（大文件）
    - 断点续传
    - 签名 URL 生成
    - 文件列表查询
    - 文件删除
    """

    def __init__(self):
        self._initialized = False
        self._auth: Optional[oss2.Auth] = None
        self._bucket: Optional[oss2.Bucket] = None
        self._executor: Optional[ThreadPoolExecutor] = None

    def init(self) -> None:
        """初始化 OSS 客户端"""
        if self._initialized:
            return

        config = settings.oss
        if not config.access_key_id or not config.access_key_secret:
            logger.warning("OSS credentials not configured, OSS client not initialized")
            return

        if not config.bucket_name:
            logger.warning("OSS bucket name not configured, OSS client not initialized")
            return

        try:
            # 创建认证对象
            self._auth = oss2.Auth(config.access_key_id, config.access_key_secret)

            # 确定使用的 endpoint
            endpoint = config.endpoint

            # 添加协议前缀
            if config.use_https and not endpoint.startswith("https://"):
                endpoint = f"https://{endpoint}"
            elif not config.use_https and not endpoint.startswith("http://"):
                endpoint = f"http://{endpoint}"

            # 创建 Bucket 对象
            self._bucket = oss2.Bucket(
                self._auth,
                endpoint,
                config.bucket_name,
                connect_timeout=config.connect_timeout
            )

            # 创建线程池用于异步操作
            self._executor = ThreadPoolExecutor(max_workers=config.upload.num_threads)

            self._initialized = True
            logger.info(f"OSS client initialized successfully, bucket: {config.bucket_name}")

        except Exception as e:
            logger.error(f"Failed to initialize OSS client: {e}")
            raise

    def close(self) -> None:
        """关闭 OSS 客户端"""
        if self._executor:
            self._executor.shutdown(wait=True)
            self._executor = None
        self._auth = None
        self._bucket = None
        self._initialized = False
        logger.info("OSS client closed")

    @property
    def bucket(self) -> oss2.Bucket:
        """获取 Bucket 对象"""
        if not self._initialized or not self._bucket:
            raise RuntimeError("OSS client not initialized")
        return self._bucket

    # ========================= 上传操作 =========================

    def put_object(
        self,
        key: str,
        data: Union[str, bytes, BinaryIO],
        content_type: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        progress_callback: Optional[callable] = None
    ) -> oss2.models.PutObjectResult:
        """
        上传对象（简单上传）

        Args:
            key: 对象名称（OSS 中的文件路径）
            data: 文件内容，可以是字符串、字节或文件对象
            content_type: 内容类型
            headers: 自定义 HTTP 头
            progress_callback: 进度回调函数

        Returns:
            上传结果
        """
        _headers = headers or {}
        if content_type:
            _headers["Content-Type"] = content_type

        result = self.bucket.put_object(
            key,
            data,
            headers=_headers if _headers else None,
            progress_callback=progress_callback
        )
        logger.info(f"Object uploaded: {key}, request_id: {result.request_id}")
        return result

    async def put_object_async(
        self,
        key: str,
        data: Union[str, bytes, BinaryIO],
        content_type: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        progress_callback: Optional[callable] = None
    ) -> oss2.models.PutObjectResult:
        """异步上传对象"""
        print(key, data, content_type)
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            lambda: self.put_object(key, data, content_type, headers, progress_callback)
        )

    def put_object_from_file(
        self,
        key: str,
        file_path: str,
        content_type: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        progress_callback: Optional[callable] = None
    ) -> oss2.models.PutObjectResult:
        """
        从本地文件上传

        Args:
            key: 对象名称
            file_path: 本地文件路径
            content_type: 内容类型
            headers: 自定义 HTTP 头
            progress_callback: 进度回调函数

        Returns:
            上传结果
        """
        _headers = headers or {}
        if content_type:
            _headers["Content-Type"] = content_type

        result = self.bucket.put_object_from_file(
            key,
            file_path,
            headers=_headers if _headers else None,
            progress_callback=progress_callback
        )
        logger.info(f"File uploaded: {file_path} -> {key}, request_id: {result.request_id}")
        return result

    async def put_object_from_file_async(
        self,
        key: str,
        file_path: str,
        content_type: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        progress_callback: Optional[callable] = None
    ) -> oss2.models.PutObjectResult:
        """异步从本地文件上传"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            lambda: self.put_object_from_file(key, file_path, content_type, headers, progress_callback)
        )

    def multipart_upload(
        self,
        key: str,
        file_path: str,
        content_type: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        progress_callback: Optional[callable] = None,
        part_size: Optional[int] = None,
        num_threads: Optional[int] = None
    ) -> oss2.models.PutObjectResult:
        """
        分片上传（大文件）

        Args:
            key: 对象名称
            file_path: 本地文件路径
            content_type: 内容类型
            headers: 自定义 HTTP 头
            progress_callback: 进度回调函数
            part_size: 分片大小，默认使用配置值
            num_threads: 并发线程数，默认使用配置值

        Returns:
            上传结果
        """
        config = settings.oss.upload
        _part_size = part_size or config.part_size
        _num_threads = num_threads or config.num_threads

        _headers = headers or {}
        if content_type:
            _headers["Content-Type"] = content_type

        # 使用 oss2 的断点续传上传
        result = oss2.resumable_upload(
            self.bucket,
            key,
            file_path,
            store=oss2.ResumableStore(root="/tmp"),
            multipart_threshold=config.multipart_threshold,
            part_size=_part_size,
            num_threads=_num_threads,
            headers=_headers if _headers else None,
            progress_callback=progress_callback
        )
        logger.info(f"Multipart upload completed: {file_path} -> {key}")
        return result

    async def multipart_upload_async(
        self,
        key: str,
        file_path: str,
        content_type: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        progress_callback: Optional[callable] = None,
        part_size: Optional[int] = None,
        num_threads: Optional[int] = None
    ) -> oss2.models.PutObjectResult:
        """异步分片上传"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            lambda: self.multipart_upload(
                key, file_path, content_type, headers,
                progress_callback, part_size, num_threads
            )
        )

    def upload_file(
        self,
        key: str,
        file_path: str,
        content_type: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        progress_callback: Optional[callable] = None
    ) -> oss2.models.PutObjectResult:
        """
        智能上传文件（自动选择普通上传或分片上传）

        Args:
            key: 对象名称
            file_path: 本地文件路径
            content_type: 内容类型
            headers: 自定义 HTTP 头
            progress_callback: 进度回调函数

        Returns:
            上传结果
        """
        file_size = os.path.getsize(file_path)
        threshold = settings.oss.upload.multipart_threshold

        if file_size > threshold:
            logger.info(f"File size {file_size} > threshold {threshold}, using multipart upload")
            return self.multipart_upload(key, file_path, content_type, headers, progress_callback)
        else:
            return self.put_object_from_file(key, file_path, content_type, headers, progress_callback)

    async def upload_file_async(
        self,
        key: str,
        file_path: str,
        content_type: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        progress_callback: Optional[callable] = None
    ) -> oss2.models.PutObjectResult:
        """异步智能上传文件"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            lambda: self.upload_file(key, file_path, content_type, headers, progress_callback)
        )

    # ========================= 下载操作 =========================

    def get_object(
        self,
        key: str,
        byte_range: Optional[tuple] = None,
        headers: Optional[Dict[str, str]] = None,
        progress_callback: Optional[callable] = None
    ) -> oss2.models.GetObjectResult:
        """
        下载对象

        Args:
            key: 对象名称
            byte_range: 字节范围，如 (0, 99) 表示下载前 100 字节
            headers: 自定义 HTTP 头
            progress_callback: 进度回调函数

        Returns:
            下载结果，通过 .read() 获取内容
        """
        result = self.bucket.get_object(
            key,
            byte_range=byte_range,
            headers=headers,
            progress_callback=progress_callback
        )
        logger.info(f"Object downloaded: {key}, request_id: {result.request_id}")
        return result

    async def get_object_async(
        self,
        key: str,
        byte_range: Optional[tuple] = None,
        headers: Optional[Dict[str, str]] = None,
        progress_callback: Optional[callable] = None
    ) -> oss2.models.GetObjectResult:
        """异步下载对象"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            lambda: self.get_object(key, byte_range, headers, progress_callback)
        )

    def get_object_to_file(
        self,
        key: str,
        file_path: str,
        byte_range: Optional[tuple] = None,
        headers: Optional[Dict[str, str]] = None,
        progress_callback: Optional[callable] = None
    ) -> oss2.models.GetObjectResult:
        """
        下载对象到本地文件

        Args:
            key: 对象名称
            file_path: 本地文件路径
            byte_range: 字节范围
            headers: 自定义 HTTP 头
            progress_callback: 进度回调函数

        Returns:
            下载结果
        """
        result = self.bucket.get_object_to_file(
            key,
            file_path,
            byte_range=byte_range,
            headers=headers,
            progress_callback=progress_callback
        )
        logger.info(f"Object downloaded to file: {key} -> {file_path}, request_id: {result.request_id}")
        return result

    async def get_object_to_file_async(
        self,
        key: str,
        file_path: str,
        byte_range: Optional[tuple] = None,
        headers: Optional[Dict[str, str]] = None,
        progress_callback: Optional[callable] = None
    ) -> oss2.models.GetObjectResult:
        """异步下载对象到本地文件"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            lambda: self.get_object_to_file(key, file_path, byte_range, headers, progress_callback)
        )

    def resumable_download(
        self,
        key: str,
        file_path: str,
        headers: Optional[Dict[str, str]] = None,
        progress_callback: Optional[callable] = None,
        part_size: Optional[int] = None,
        num_threads: Optional[int] = None
    ) -> oss2.models.GetObjectResult:
        """
        断点续传下载（大文件）

        Args:
            key: 对象名称
            file_path: 本地文件路径
            headers: 自定义 HTTP 头
            progress_callback: 进度回调函数
            part_size: 分片大小
            num_threads: 并发线程数

        Returns:
            下载结果
        """
        config = settings.oss.download
        _part_size = part_size or config.part_size
        _num_threads = num_threads or config.num_threads

        result = oss2.resumable_download(
            self.bucket,
            key,
            file_path,
            store=oss2.ResumableDownloadStore(root="/tmp"),
            multiget_threshold=config.multipart_threshold,
            part_size=_part_size,
            num_threads=_num_threads,
            headers=headers,
            progress_callback=progress_callback
        )
        logger.info(f"Resumable download completed: {key} -> {file_path}")
        return result

    async def resumable_download_async(
        self,
        key: str,
        file_path: str,
        headers: Optional[Dict[str, str]] = None,
        progress_callback: Optional[callable] = None,
        part_size: Optional[int] = None,
        num_threads: Optional[int] = None
    ) -> oss2.models.GetObjectResult:
        """异步断点续传下载"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            lambda: self.resumable_download(
                key, file_path, headers, progress_callback, part_size, num_threads
            )
        )

    def download_file(
        self,
        key: str,
        file_path: str,
        headers: Optional[Dict[str, str]] = None,
        progress_callback: Optional[callable] = None
    ) -> oss2.models.GetObjectResult:
        """
        智能下载文件（自动选择普通下载或断点续传）

        Args:
            key: 对象名称
            file_path: 本地文件路径
            headers: 自定义 HTTP 头
            progress_callback: 进度回调函数

        Returns:
            下载结果
        """
        # 先获取文件大小
        meta = self.head_object(key)
        file_size = meta.content_length
        threshold = settings.oss.download.multipart_threshold

        if file_size > threshold:
            logger.info(f"File size {file_size} > threshold {threshold}, using resumable download")
            return self.resumable_download(key, file_path, headers, progress_callback)
        else:
            return self.get_object_to_file(key, file_path, headers=headers, progress_callback=progress_callback)

    async def download_file_async(
        self,
        key: str,
        file_path: str,
        headers: Optional[Dict[str, str]] = None,
        progress_callback: Optional[callable] = None
    ) -> oss2.models.GetObjectResult:
        """异步智能下载文件"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            lambda: self.download_file(key, file_path, headers, progress_callback)
        )

    # ========================= 对象操作 =========================

    def head_object(self, key: str) -> oss2.models.HeadObjectResult:
        """
        获取对象元信息

        Args:
            key: 对象名称

        Returns:
            对象元信息
        """
        return self.bucket.head_object(key)

    async def head_object_async(self, key: str) -> oss2.models.HeadObjectResult:
        """异步获取对象元信息"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, lambda: self.head_object(key))

    def object_exists(self, key: str) -> bool:
        """
        检查对象是否存在

        Args:
            key: 对象名称

        Returns:
            是否存在
        """
        return self.bucket.object_exists(key)

    async def object_exists_async(self, key: str) -> bool:
        """异步检查对象是否存在"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, lambda: self.object_exists(key))

    def delete_object(self, key: str) -> oss2.models.RequestResult:
        """
        删除对象

        Args:
            key: 对象名称

        Returns:
            删除结果
        """
        result = self.bucket.delete_object(key)
        logger.info(f"Object deleted: {key}, request_id: {result.request_id}")
        return result

    async def delete_object_async(self, key: str) -> oss2.models.RequestResult:
        """异步删除对象"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, lambda: self.delete_object(key))

    def batch_delete_objects(self, keys: List[str]) -> oss2.models.BatchDeleteObjectsResult:
        """
        批量删除对象

        Args:
            keys: 对象名称列表

        Returns:
            删除结果
        """
        result = self.bucket.batch_delete_objects(keys)
        logger.info(f"Batch deleted {len(keys)} objects")
        return result

    async def batch_delete_objects_async(self, keys: List[str]) -> oss2.models.BatchDeleteObjectsResult:
        """异步批量删除对象"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, lambda: self.batch_delete_objects(keys))

    def copy_object(
        self,
        source_key: str,
        target_key: str,
        source_bucket: Optional[str] = None
    ) -> oss2.models.PutObjectResult:
        """
        复制对象

        Args:
            source_key: 源对象名称
            target_key: 目标对象名称
            source_bucket: 源 Bucket 名称，默认为当前 Bucket

        Returns:
            复制结果
        """
        _source_bucket = source_bucket or settings.oss.bucket_name
        result = self.bucket.copy_object(_source_bucket, source_key, target_key)
        logger.info(f"Object copied: {source_key} -> {target_key}")
        return result

    async def copy_object_async(
        self,
        source_key: str,
        target_key: str,
        source_bucket: Optional[str] = None
    ) -> oss2.models.PutObjectResult:
        """异步复制对象"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            lambda: self.copy_object(source_key, target_key, source_bucket)
        )

    # ========================= 列表操作 =========================

    def list_objects(
        self,
        prefix: str = "",
        delimiter: str = "",
        marker: str = "",
        max_keys: int = 100
    ) -> oss2.models.ListObjectsResult:
        """
        列举对象

        Args:
            prefix: 前缀过滤
            delimiter: 分隔符，用于分组
            marker: 起始位置
            max_keys: 最大返回数量

        Returns:
            对象列表
        """
        return self.bucket.list_objects(
            prefix=prefix,
            delimiter=delimiter,
            marker=marker,
            max_keys=max_keys
        )

    async def list_objects_async(
        self,
        prefix: str = "",
        delimiter: str = "",
        marker: str = "",
        max_keys: int = 100
    ) -> oss2.models.ListObjectsResult:
        """异步列举对象"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            lambda: self.list_objects(prefix, delimiter, marker, max_keys)
        )

    def list_objects_v2(
        self,
        prefix: str = "",
        delimiter: str = "",
        continuation_token: str = "",
        max_keys: int = 100
    ) -> oss2.models.ListObjectsV2Result:
        """
        列举对象（v2 版本）

        Args:
            prefix: 前缀过滤
            delimiter: 分隔符
            continuation_token: 延续标记
            max_keys: 最大返回数量

        Returns:
            对象列表
        """
        return self.bucket.list_objects_v2(
            prefix=prefix,
            delimiter=delimiter,
            continuation_token=continuation_token,
            max_keys=max_keys
        )

    # ========================= URL 签名 =========================

    def sign_url(
        self,
        method: str,
        key: str,
        expires: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, str]] = None
    ) -> str:
        """
        生成签名 URL

        Args:
            method: HTTP 方法 (GET/PUT)
            key: 对象名称
            expires: 过期时间（秒），默认使用配置值
            headers: 自定义 HTTP 头
            params: URL 参数

        Returns:
            签名 URL
        """
        _expires = expires or settings.oss.url_expire_seconds
        url = self.bucket.sign_url(method, key, _expires, headers=headers, params=params)
        logger.debug(f"Signed URL generated for {key}, expires in {_expires}s")
        return url

    def get_download_url(
        self,
        key: str,
        expires: Optional[int] = None,
        filename: Optional[str] = None
    ) -> str:
        """
        获取下载 URL

        Args:
            key: 对象名称
            expires: 过期时间（秒）
            filename: 下载时的文件名

        Returns:
            下载 URL
        """
        params = {}
        if filename:
            params["response-content-disposition"] = f"attachment; filename={filename}"
        return self.sign_url("GET", key, expires, params=params if params else None)

    def get_upload_url(
        self,
        key: str,
        expires: Optional[int] = None,
        content_type: Optional[str] = None
    ) -> str:
        """
        获取上传 URL（用于客户端直传）

        Args:
            key: 对象名称
            expires: 过期时间（秒）
            content_type: 内容类型

        Returns:
            上传 URL
        """
        headers = {}
        if content_type:
            headers["Content-Type"] = content_type
        return self.sign_url("PUT", key, expires, headers=headers if headers else None)

    # ========================= 工具方法 =========================

    def generate_object_key(
        self,
        filename: str,
        prefix: str = "",
        use_timestamp: bool = True
    ) -> str:
        """
        生成对象 key

        Args:
            filename: 原始文件名
            prefix: 前缀路径
            use_timestamp: 是否使用时间戳

        Returns:
            生成的对象 key
        """
        if use_timestamp:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name, ext = os.path.splitext(filename)
            filename = f"{name}_{timestamp}{ext}"

        if prefix:
            prefix = prefix.rstrip("/")
            return f"{prefix}/{filename}"
        return filename


# 全局 OSS 客户端实例
oss_client = OSSClient()


def init_oss() -> None:
    """初始化全局 OSS 客户端"""
    oss_client.init()


def close_oss() -> None:
    """关闭全局 OSS 客户端"""
    oss_client.close()


def get_oss() -> OSSClient:
    """
    获取 OSS 客户端（用于 FastAPI 依赖注入）

    Returns:
        OSSClient 实例
    """
    if not oss_client._initialized:
        oss_client.init()
    return oss_client
