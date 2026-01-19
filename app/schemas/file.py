from typing import List, Optional
from pydantic import BaseModel


# ========================= 请求/响应模型 =========================

class UploadResponse(BaseModel):
    """上传响应"""
    key: str
    url: str
    filename: str
    size: int
    content_type: str


class FileInfoResponse(BaseModel):
    """文件信息响应"""
    key: str
    size: int
    content_type: Optional[str] = None
    last_modified: Optional[str] = None


class SignedUrlRequest(BaseModel):
    """签名 URL 请求"""
    key: str
    expires: Optional[int] = 3600
    for_download: bool = False
    filename: Optional[str] = None


class SignedUrlResponse(BaseModel):
    """签名 URL 响应"""
    url: str
    expires_in: int


class UploadUrlRequest(BaseModel):
    """上传 URL 请求（用于客户端直传）"""
    filename: str
    prefix: str = "uploads"
    category: Optional[str] = None
    content_type: Optional[str] = None
    expires: Optional[int] = 3600


class UploadUrlResponse(BaseModel):
    """上传 URL 响应"""
    key: str
    upload_url: str
    expires_in: int


class DeleteResponse(BaseModel):
    """删除响应"""
    success: bool
    key: str


class BatchDeleteRequest(BaseModel):
    """批量删除请求"""
    keys: List[str]


class BatchDeleteResponse(BaseModel):
    """批量删除响应"""
    results: dict