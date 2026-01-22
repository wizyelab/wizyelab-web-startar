"""公共数据模型"""

from typing import Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


# ========================= 基础响应模型 =========================


class BaseResponse(BaseModel, Generic[T]):
    """基础响应模型"""

    code: int = Field(default=0, description="状态码: 0-正常, 1-异常")
    message: str = Field(default="正确", description="返回信息")
    data: Optional[T] = Field(default=None, description="响应数据")


# ========================= 公共数据模型 =========================


class Video(BaseModel):
    """视频信息"""

    id: str = Field(default="", description="视频id")
    height: int = Field(default=0, description="视频高度")
    width: int = Field(default=0, description="视频宽度")
    duration: int = Field(default=0, description="视频时长(秒)")
    cover_url: str = Field(default="", description="封面图")
    main_url: str = Field(default="", description="主链接")
    back_urls: List[str] = Field(default_factory=list, description="备用链接")


class Author(BaseModel):
    """作者信息"""

    user_id: str = Field(default="", description="用户ID")
    user_name: str = Field(default="", description="用户名")
    avatar: str = Field(default="", description="头像URL")
    is_followed: bool = Field(default=False, description="是否已关注")


# ========================= 分页相关 =========================


class PaginationRequest(BaseModel):
    """分页请求基类"""

    page: int = Field(default=1, ge=1, description="页码，从1开始")
    page_size: int = Field(default=20, ge=1, le=50, description="每页数量，最大50")


class PaginationData(BaseModel):
    """分页数据基类"""

    total: int = Field(default=0, description="总数")
    page: int = Field(default=1, description="当前页")
    page_size: int = Field(default=20, description="每页数量")
    has_more: bool = Field(default=False, description="是否有更多")
