"""Profile相关数据模型"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from .common import Video, Image, Author, PaginationData


# ========================= 用户Profile =========================


class ProfileInfoRequest(BaseModel):
    """获取用户Profile请求"""

    user_id: str = Field(description="目标用户ID")


class ProfileData(BaseModel):
    """用户Profile响应数据"""

    user_id: str = Field(default="", description="用户ID")
    user_name: str = Field(default="", description="用户名")
    avatar: str = Field(default="", description="头像URL")
    bio: str = Field(default="", description="个人简介")
    gender: int = Field(default=0, description="性别: 1-male, 2-female, 3-other")
    location: str = Field(default="", description="位置")
    interest_tags: List[int] = Field(default_factory=list, description="兴趣标签ID列表")
    follower_count: int = Field(default=0, description="粉丝数")
    following_count: int = Field(default=0, description="关注数")
    post_count: int = Field(default=0, description="帖子数")
    is_followed: bool = Field(default=False, description="是否已关注")
    is_self: bool = Field(default=False, description="是否本人")


# ========================= 引导列表 =========================


class OptionItem(BaseModel):
    """选项条目"""

    content: str = Field(default="", description="展示内容")
    description: str = Field(default="", description="选项描述")
    icon_url: str = Field(default="", description="图标URL")


class GuideItem(BaseModel):
    """引导项"""

    id: int = Field(default=0, description="引导项ID")
    tag_id: int = Field(default=0, description="关联标签ID")
    style: int = Field(default=0, description="引导样式: 0-无样式, 1-选项条, 2-选项卡")
    guide_words: str = Field(default="", description="引导话术")
    profile_key: str = Field(default="", description="profile页的字段名")
    sort: int = Field(default=0, description="排序")
    options: List[OptionItem] = Field(default_factory=list, description="选项列表")
    head_img: Optional[Image] = Field(default=None, description="Logo上半部分图片")
    body_img: Optional[Image] = Field(default=None, description="Logo下半部分图片")


class GuideData(BaseModel):
    """引导列表响应数据"""

    items: List[GuideItem] = Field(default_factory=list, description="引导项列表")
    total_steps: int = Field(default=0, description="总步骤数")


# ========================= 引导列表请求 =========================


class GuideListRequest(BaseModel):
    """获取引导列表请求"""

    tag_id: int = Field(default=0, description="标签ID，0=全部")


# ========================= 更新Profile =========================


class ProfileUpdateRequest(BaseModel):
    """更新Profile请求"""

    name: Optional[str] = Field(default=None, max_length=50, description="用户名")
    avatar: Optional[str] = Field(default=None, description="头像URL")
    bio: Optional[str] = Field(default=None, max_length=500, description="个人简介")
    gender: Optional[int] = Field(default=None, description="性别: 1-male, 2-female, 3-other")
    location: Optional[str] = Field(default=None, description="位置")
    onboarding: Optional[Dict[str, Any]] = Field(
        default=None,
        description="用户onboarding数据，JSON格式"
    )
    extra: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="on-boarding问答数据，格式: [{question: str, answer: str, ...}, ...]"
    )

    model_config = {"extra": "allow"}


# ========================= 用户帖子列表 =========================


class ProfilePost(BaseModel):
    """用户帖子模型"""

    id: str = Field(default="", description="内容ID")
    post_type: int = Field(default=0, description="内容类型: 1-video, 2-image, 3-text")
    title: str = Field(default="", description="标题")
    description: str = Field(default="", description="描述")
    content: str = Field(default="", description="内容")
    images: List[Image] = Field(default_factory=list, description="图片列表")
    video: Optional[Video] = Field(default=None, description="视频信息")
    author: Optional[Author] = Field(default=None, description="作者信息")
    like_count: int = Field(default=0, description="点赞数")
    comment_count: int = Field(default=0, description="评论数")
    share_count: int = Field(default=0, description="分享数")
    is_liked: bool = Field(default=False, description="是否已点赞")
    is_collected: bool = Field(default=False, description="是否已收藏")
    create_time: str = Field(default="", description="创建时间")
    update_time: str = Field(default="", description="更新时间")
    display_time: str = Field(default="", description="展示时间")


class ProfilePostsRequest(BaseModel):
    """用户帖子列表请求"""

    user_id: str = Field(description="用户ID")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=50, description="每页数量")


class ProfilePostsData(PaginationData):
    """用户帖子列表响应数据"""

    items: List[ProfilePost] = Field(default_factory=list, description="帖子列表")


# ========================= 创建帖子 =========================


class CreatePostRequest(BaseModel):
    """创建帖子请求"""

    post_type: int = Field(description="帖子类型: 1-video, 2-image, 3-text")
    title: str = Field(default="", max_length=200, description="标题")
    description: str = Field(default="", max_length=2000, description="描述/正文")
    content: str = Field(default="", description="内容")
    images: List[Image] = Field(default_factory=list, description="图片列表")
    video: Optional[Video] = Field(default=None, description="视频信息")
    tags: List[int] = Field(default_factory=list, description="标签ID列表")


class CreatePostData(BaseModel):
    """创建帖子响应数据"""

    post_id: str = Field(default="", description="帖子ID")


# ========================= 删除帖子 =========================


class DeletePostRequest(BaseModel):
    """删除帖子请求"""

    post_id: str = Field(description="帖子ID")


# ========================= 关注取关 =========================


class FollowRequest(BaseModel):
    """关注/取关请求"""

    target_user_id: str = Field(description="目标用户ID")
    is_follow: bool = Field(default=True, description="动作类型")


class FollowData(BaseModel):
    """关注响应数据"""

    is_followed: bool = Field(default=False, description="是否已关注")
    follower_count: int = Field(default=0, description="目标用户粉丝数")


# ========================= 粉丝/关注列表 =========================


class FollowersRequest(BaseModel):
    """获取粉丝/关注列表请求"""

    user_id: str = Field(description="用户ID")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=50, description="每页数量")


class UserItem(BaseModel):
    """用户列表项"""

    user_id: str = Field(default="", description="用户ID")
    user_name: str = Field(default="", description="用户名")
    avatar: str = Field(default="", description="头像URL")
    bio: str = Field(default="", description="个人简介")
    is_following: bool = Field(default=False, description="是否已关注")


class FollowListData(BaseModel):
    """粉丝/关注列表响应数据"""

    items: List[UserItem] = Field(default_factory=list, description="用户列表")
    total: int = Field(default=0, description="总数")
    has_more: bool = Field(default=False, description="是否有更多")


# ========================= 用户反馈 =========================


class FeedbackRequest(BaseModel):
    """用户反馈请求"""

    post_id: Optional[str] = Field(default=None, description="内容ID")
    feedback_type: int = Field(
        description="反馈类型: 1-dislike, 2-not_interested, 3-report, 4-spam"
    )
    reason: Optional[str] = Field(default=None, max_length=200, description="反馈原因")
    detail: Optional[str] = Field(default=None, max_length=1000, description="详细描述")
