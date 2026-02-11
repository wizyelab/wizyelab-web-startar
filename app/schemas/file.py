from typing import List, Optional
from pydantic import BaseModel, Field


# ========================= 数据模型 =========================

class Image(BaseModel):
    """图片信息"""
    id: str = Field(default="", description="图片id")
    height: int = Field(default=0, description="图片高度")
    width: int = Field(default=0, description="图片宽度")
    format: str = Field(default="", description="图片格式(jpg/png/webp等)")
    size: int = Field(default=0, description="文件大小(字节)")
    main_url: str = Field(default="", description="主链接")
    back_urls: List[str] = Field(default_factory=list, description="备用链接")


class MultiImage(BaseModel):
    """图片多尺寸 URL（图片和视频封面通用）"""
    large: Optional[Image] = Field(default=None, description="大图 (1920x1080)")
    medium: Optional[Image] = Field(default=None, description="中图 (1280x720)")
    small: Optional[Image] = Field(default=None, description="小图 (640x360)")
    thumbnail: Optional[Image] = Field(default=None, description="缩略图 (200x200)")


class MediaUploadResponse(BaseModel):
    """媒体上传响应（增强版）"""
    file_id: str = Field(..., description="文件 ID（雪花算法）")
    file_type: int = Field(..., description="文件类型：1=视频,2=图片,3=文档,4=音频,5=其他")
    file_name: str = Field(..., description="原始文件名")
    file_ext: str = Field(default="", description="文件扩展名")
    file_size: int = Field(default=0, description="文件大小（字节）")
    mime_type: str = Field(default="", description="MIME 类型")
    original_uri: str = Field(default="", description="原始存储路径（OSS key）")
    url: str = Field(default="", description="浏览 URL")
    download_url: str = Field(default="", description="下载 URL（带水印）")
    width: int = Field(default=0, description="宽度（图片/视频）")
    height: int = Field(default=0, description="高度（图片/视频）")
    duration: int = Field(default=0, description="时长秒数（视频/音频）")
    multi_imgs: Optional[MultiImage] = Field(default=None, description="多尺寸图片")
    hash_md5: str = Field(default="", description="文件 MD5")
    is_duplicate: bool = Field(default=False, description="是否为重复文件（秒传）")
    create_time: int = Field(..., description="创建时间（毫秒时间戳）")


# ========================= 响应数据模型 =========================

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


class FileIdRequest(BaseModel):
    """文件ID请求"""
    file_id: str


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
