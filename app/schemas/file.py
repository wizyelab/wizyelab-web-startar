from typing import List, Optional
from pydantic import BaseModel

from app.schemas.common import BaseResponse


# ========================= 数据模型 =========================

class UploadData(BaseModel):
    """上传数据"""
    key: str
    url: str
    filename: str
    size: int
    content_type: str


class FileInfoData(BaseModel):
    """文件信息数据"""
    key: str
    size: int
    content_type: Optional[str] = None
    last_modified: Optional[str] = None


class SignedUrlData(BaseModel):
    """签名 URL 数据"""
    url: str
    expires_in: int


class UploadUrlData(BaseModel):
    """上传 URL 数据"""
    key: str
    upload_url: str
    expires_in: int


class DeleteData(BaseModel):
    """删除数据"""
    success: bool
    key: str


class BatchDeleteData(BaseModel):
    """批量删除数据"""
    results: dict


class FileExistsData(BaseModel):
    """文件存在检查数据"""
    exists: bool
    key: str


# ========================= 请求模型 =========================

class FileKeyRequest(BaseModel):
    """文件key请求（通用）"""
    key: str


class DownloadRequest(BaseModel):
    """下载请求"""
    key: str
    filename: Optional[str] = None


class FileListRequest(BaseModel):
    """文件列表请求"""
    prefix: str = ""
    max_keys: int = 100
    marker: str = ""


class SignedUrlRequest(BaseModel):
    """签名 URL 请求"""
    key: str
    expires: Optional[int] = 3600
    for_download: bool = False
    filename: Optional[str] = None


class UploadUrlRequest(BaseModel):
    """上传 URL 请求（用于客户端直传）"""
    filename: str
    prefix: str = "uploads"
    category: Optional[str] = None
    content_type: Optional[str] = None
    expires: Optional[int] = 3600


class BatchDeleteRequest(BaseModel):
    """批量删除请求"""
    keys: List[str]


