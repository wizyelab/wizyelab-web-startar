"""详情页相关数据模型"""

from typing import List, Optional
from pydantic import BaseModel, Field

from .common import Video, Author, PaginationData


# ========================= 帖子详情 =========================


class DetailPost(BaseModel):
    """帖子详情模型"""

    id: str = Field(default="", description="帖子ID")
    post_type: int = Field(default=0, description="帖子类型: 1-video, 2-image, 3-text")
    title: str = Field(default="", description="标题")
    description: str = Field(default="", description="描述/正文")
    content: str = Field(default="", description="完整内容文本")
    img_urls: List[str] = Field(default_factory=list, description="图片列表")
    video: Optional[Video] = Field(default=None, description="视频信息")
    author: Optional[Author] = Field(default=None, description="作者信息")
    like_count: int = Field(default=0, description="点赞数")
    comment_count: int = Field(default=0, description="评论数")
    share_count: int = Field(default=0, description="分享数")
    is_liked: bool = Field(default=False, description="是否已点赞")
    is_collected: bool = Field(default=False, description="是否已收藏")
    is_followed: bool = Field(default=False, description="是否已关注作者")
    create_time: str = Field(default="", description="创建时间")
    update_time: str = Field(default="", description="更新时间")
    display_time: str = Field(default="", description="展示时间")


class DetailInfoRequest(BaseModel):
    """获取内容详情请求"""

    post_id: str = Field(description="帖子ID")


class DetailData(BaseModel):
    """内容详情响应数据"""

    post: Optional[DetailPost] = Field(default=None, description="帖子详情")
    related_posts: List[DetailPost] = Field(default_factory=list, description="相关推荐")


# ========================= 评论 =========================


class Comment(BaseModel):
    """评论模型"""

    comment_id: str = Field(default="", description="评论ID")
    post_id: str = Field(default="", description="帖子ID")
    user: Optional[Author] = Field(default=None, description="评论者信息")
    text: str = Field(default="", description="评论内容")
    level: int = Field(default=0, description="评论层级: 0-一级评论, 1-二级回复")
    like_count: int = Field(default=0, description="点赞数")
    reply_count: int = Field(default=0, description="回复数")
    is_liked: bool = Field(default=False, description="是否已点赞")
    parent_id: str = Field(default="", description="父评论ID")
    reply_to_user: Optional[Author] = Field(default=None, description="回复的用户")
    replies: List["Comment"] = Field(default_factory=list, description="子回复列表")
    create_time: str = Field(default="", description="创建时间")
    display_time: str = Field(default="", description="展示时间")
    update_time: str = Field(default="", description="更新时间")


# 处理自引用
Comment.model_rebuild()


class CommentListRequest(BaseModel):
    """获取评论列表请求"""

    post_id: str = Field(description="帖子ID")
    comment_id: str = Field(default="", description="评论ID,通过指定id加载更多")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=50, description="每页数量")
    sort_by: int = Field(default=0, description="排序方式: 0-最新, 1-热门")


class CommentListData(PaginationData):
    """评论列表响应数据"""

    comments: List[Comment] = Field(default_factory=list, description="评论列表")


class CreateCommentRequest(BaseModel):
    """发表评论请求"""

    post_id: str = Field(description="帖子ID")
    text: str = Field(description="评论内容", max_length=1000)
    comment_id: str = Field(default="", description="父评论ID")
    level: int = Field(default=0, description="评论层级")
    reply_to_user_id: str = Field(default="", description="回复的用户ID")


class CreateCommentData(BaseModel):
    """发表评论响应数据"""

    comment_id: str = Field(default="", description="新评论ID")
    comment: Optional[Comment] = Field(default=None, description="评论详情")


class DeleteCommentRequest(BaseModel):
    """删除评论请求"""

    comment_id: str = Field(description="评论ID")


class GetCommentByLevelRequest(BaseModel):
    """获取评论回复列表请求"""

    comment_id: str = Field(description="父评论ID")
    level: int = Field(default=0, description="评论层级")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=50, description="每页数量")


class ReplyListData(BaseModel):
    """回复列表响应数据"""

    items: List[Comment] = Field(default_factory=list, description="回复列表")
    total: int = Field(default=0, description="总数")
    has_more: bool = Field(default=False, description="是否有更多")
