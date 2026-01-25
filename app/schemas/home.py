"""首页相关数据模型"""

from typing import List, Optional
from pydantic import BaseModel, Field

from .common import Video, Author, PaginationData


# ========================= 标签内容列表 =========================


class Item(BaseModel):
    """内容条目"""

    item_id: str = Field(default="", description="条目唯一id")
    logo: str = Field(default="", description="logo图片")
    title: str = Field(default="", description="标题")
    sub_title: str = Field(default="", description="子标题")
    video: Optional[Video] = Field(default=None, description="视频信息")
    desc: str = Field(default="", description="描述信息")
    rating: str = Field(default="0.0", description="评分")


class Content(BaseModel):
    """内容模型"""

    content_id: str = Field(default="", description="内容唯一id")
    logo: str = Field(default="", description="logo图片")
    title: str = Field(default="", description="标题")
    sub_title: str = Field(default="", description="副标题")
    content_type: int = Field(
        default=0, description="内容类型: 0-默认, 1-装备推荐, 2-AI分析, 3-高光时刻, 4-推荐媒体"
    )
    video: Optional[Video] = Field(default=None, description="视频信息")
    cover_image: str = Field(default="", description="封面图")
    action_type: int = Field(
        default=0, description="点击动作类型: 0-无动作, 1-跳转详情页, 2-跳转外链, 3-跳转视频上传"
    )
    action_url: str = Field(default="", description="跳转链接")
    button_desc: str = Field(default="", description="展示button的文案，不为空时展示button")
    item_list: List[Item] = Field(default_factory=list, description="内容条目列表")


class Tag(BaseModel):
    """标签模型"""

    tag_id: int = Field(default=0, description="标签id")
    tag_name: str = Field(default="", description="标签名")
    tag_icon: str = Field(default="", description="标签图标")
    content_list: List[Content] = Field(default_factory=list, description="内容列表")
    is_selected: bool = Field(default=False, description="是否选中")


class TagContentListRequest(BaseModel):
    """标签内容列表请求"""

    tag_id: int = Field(default=0, description="标签id, 0会下发所有tag列表和第一个tag的内容")


class TagContentListData(BaseModel):
    """标签内容列表响应数据"""

    tag_list: List[Tag] = Field(default_factory=list, description="tag列表")
    first_login: bool = Field(default=False, description="是否第一次登录")


# ========================= 广场Feed =========================


class Post(BaseModel):
    """帖子模型"""

    id: str = Field(default="", description="内容ID")
    post_type: int = Field(default=0, description="内容类型: 1-video, 2-image, 3-text")
    title: str = Field(default="", description="标题")
    description: str = Field(default="", description="描述")
    content: str = Field(default="", description="内容")
    thumbnail_url: str = Field(default="", description="缩略图")
    img_urls: List[str] = Field(default_factory=list, description="图片列表")
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


class FeedRequest(BaseModel):
    """Feed请求"""

    post_id: str = Field(default="", description="帖子id,作为加载更多的游标")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=50, description="每页数量")


class FeedData(PaginationData):
    """Feed响应数据"""

    items: List[Post] = Field(default_factory=list, description="Feed列表")


# ========================= 用户行为 =========================


class UserActionRequest(BaseModel):
    """用户行为请求"""

    comment_id: Optional[str] = Field(default=None, description="评论ID")
    post_id: Optional[str] = Field(default=None, description="内容ID")
    action_type: int = Field(
        default=0, description="行为类型: 0-view, 1-like, 2-unlike, 3-collect, 4-uncollect, 5-share"
    )


class ActionData(BaseModel):
    """用户行为响应数据"""

    action_type: int = Field(default=0, description="行为类型")
    is_active: bool = Field(default=False, description="当前状态")
    count: int = Field(default=0, description="更新后数量")


# ========================= 生成分享链接 =========================


class GenerateShareLinkRequest(BaseModel):
    """生成分享链接请求"""

    post_id: str = Field(description="内容ID")
    share_type: str = Field(default="h5", description="分享类型: h5, deeplink")


class ShareData(BaseModel):
    """分享链接响应数据"""

    share_url: str = Field(default="", description="分享链接")
    share_text: str = Field(default="", description="分享文案")
    share_image: str = Field(default="", description="分享图片")


# ========================= 推荐提示词 =========================


class SuggestedPrompt(BaseModel):
    """推荐提示词"""

    id: str = Field(default="", description="提示词ID")
    text: str = Field(default="", description="提示词文本")
    prompt_type: int = Field(
        default=0, description="提示词类型: 0-通用, 1-追问, 2-深入, 3-切换话题"
    )
    icon: str = Field(default="", description="图标标识")


class SuggestedPromptsRequest(BaseModel):
    """获取推荐提示词请求"""

    scene_type: int = Field(
        default=0, description="场景类型: 0-通用, 1-装备推荐, 2-AI分析, 3-高光时刻, 4-推荐媒体"
    )
    content_id: str = Field(default="", description="内容ID")
    tag_id: int = Field(default=0, description="标签ID")
    count: int = Field(default=3, ge=1, le=5, description="期望数量")


class SuggestedPromptsData(BaseModel):
    """推荐提示词响应数据"""

    prompts: List[SuggestedPrompt] = Field(default_factory=list, description="提示词列表")
    scene_type: int = Field(default=0, description="场景类型")
    content_id: str = Field(default="", description="关联内容ID")
