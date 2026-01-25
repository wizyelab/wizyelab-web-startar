"""聊天相关数据模型"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from .common import Video, Author, PaginationData


# ========================= 思考过程 =========================


class ThinkingStep(BaseModel):
    """思考步骤"""

    step_id: str = Field(default="", description="步骤ID")
    step_order: int = Field(default=0, description="步骤顺序，从1开始")
    title: str = Field(default="", description="步骤标题")
    content: str = Field(default="", description="步骤详细内容")
    step_type: int = Field(
        default=0, description="步骤类型: 0-分析, 1-检索, 2-推理, 3-生成, 4-验证"
    )
    duration_ms: int = Field(default=0, description="步骤耗时(毫秒)")
    status: int = Field(default=3, description="步骤状态: 1-pending, 2-processing, 3-completed")
    video: Optional[Video] = Field(default=None, description="相关视频")
    img_urls: List[str] = Field(default_factory=list, description="相关图片列表")


class Thinking(BaseModel):
    """思考过程"""

    thinking_id: str = Field(default="", description="思考过程ID")
    message_id: str = Field(default="", description="关联的消息ID")
    summary: str = Field(default="", description="思考摘要")
    steps: List[ThinkingStep] = Field(default_factory=list, description="思考步骤列表")
    total_duration_ms: int = Field(default=0, description="总耗时(毫秒)")
    is_expanded: bool = Field(default=False, description="是否默认展开")


# ========================= 推荐提示词 =========================


class SuggestedPrompt(BaseModel):
    """推荐提示词"""

    id: str = Field(default="", description="提示词ID")
    text: str = Field(default="", description="提示词文本")
    prompt_type: int = Field(
        default=0, description="提示词类型: 0-通用, 1-追问, 2-深入, 3-切换话题"
    )
    icon: str = Field(default="", description="图标标识")


# ========================= 附件 =========================


class Attachment(BaseModel):
    """附件"""

    media_type: int = Field(default=0, description="附件类型: 1-video, 2-image, 3-voice")
    url: str = Field(default="", description="附件URL")
    extra: Dict[str, Any] = Field(default_factory=dict, description="扩展数据")


# ========================= 卡片相关 =========================


class Equipment(BaseModel):
    """装备"""

    id: str = Field(default="", description="装备ID")
    name: str = Field(default="", description="装备名称")
    brand: str = Field(default="", description="品牌")
    model: str = Field(default="", description="型号")
    img_urls: List[str] = Field(default_factory=list, description="图片URL列表")
    price: str = Field(default="", description="价格")
    description: str = Field(default="", description="描述")
    tags: List[str] = Field(default_factory=list, description="标签")


class Channel(BaseModel):
    """频道/视频信息"""

    video: Optional[Video] = Field(default=None, description="主视频信息")
    title: str = Field(default="", description="卡片标题")
    import_time: str = Field(default="", description="重要视频时间")
    summary: str = Field(default="", description="视频总结")
    author: Optional[Author] = Field(default=None, description="作者信息")
    rating: str = Field(default="0.0", description="评分")
    display_time: str = Field(default="", description="展示时间")
    user_comment: str = Field(default="", description="用户评论")
    digg_desc: str = Field(default="", description="点赞数文案")


class SocialMediaData(BaseModel):
    """社交媒体数据"""

    youtube: List[Channel] = Field(default_factory=list, description="Youtube视频")
    amazon: List[Channel] = Field(default_factory=list, description="Amazon评论")
    reddit: List[Channel] = Field(default_factory=list, description="Reddit评论")


class Card(BaseModel):
    """卡片"""

    card_type: int = Field(
        default=0, description="卡片类型: 1-装备, 2-ai分析, 3-分析报告, 4-高光时刻"
    )
    title: str = Field(default="", description="卡片标题")
    equipments: Optional[List[Equipment]] = Field(default=None, description="装备列表")
    social_media_data: Optional[SocialMediaData] = Field(default=None, description="媒体数据")
    button_desc: str = Field(default="", description="按钮文案")
    video: Optional[Video] = Field(default=None, description="视频信息")
    summary: str = Field(default="", description="总结")
    channel: Optional[Channel] = Field(default=None, description="第二视频信息")
    img_urls: List[str] = Field(default_factory=list, description="图片列表")


# ========================= 组件 =========================


class Component(BaseModel):
    """组件"""

    text: str = Field(default="", description="文本消息")
    button_left_desc: str = Field(default="", description="左button描述")
    button_right_desc: str = Field(default="", description="右button描述")


class MediaReference(BaseModel):
    """参考媒体源"""

    logo: str = Field(default="", description="logo")
    desc: str = Field(default="", description="描述")


# ========================= 消息 =========================


class MessageItem(BaseModel):
    """消息项"""

    message_id: str = Field(default="", description="消息ID")
    session_id: str = Field(default="", description="会话ID")
    role: int = Field(default=0, description="角色: 1-user, 2-assistant, 3-system")
    content: str = Field(default="", description="消息内容")
    message_type: int = Field(
        default=1, description="消息类型: 1-video, 2-image, 3-text, 4-voice"
    )
    message_style: int = Field(
        default=0, description="消息样式: 0-chat, 1-装备推荐, 2-AI分析, 3-高光时刻, 4-推荐媒体"
    )
    attachments: List[Attachment] = Field(default_factory=list, description="附件列表")
    cards: List[Card] = Field(default_factory=list, description="卡片列表")
    generation_status: int = Field(
        default=3, description="生成状态: 1-pending, 2-generating, 3-completed, 4-failed, 5-stopped"
    )
    create_time: str = Field(default="", description="创建时间")
    display_time: str = Field(default="", description="展示时间")
    media_reference: List[MediaReference] = Field(default_factory=list, description="参考媒体源")
    summary: str = Field(default="", description="总结")
    component: Optional[Component] = Field(default=None, description="组件")
    thinking: Optional[Thinking] = Field(default=None, description="思考过程，仅AI消息有值")
    suggested_prompts: List[SuggestedPrompt] = Field(
        default_factory=list, description="推荐提示词，仅AI消息有值"
    )


# ========================= 会话来源 =========================


class Source(BaseModel):
    """会话来源"""

    home_tag_id: int = Field(default=0, description="首页tag_id")
    home_content_id: str = Field(default="", description="首页content_id")
    source_type: int = Field(
        default=0, description="会话来源: 0-chat对话, 1-装备推荐, 2-AI分析, 3-高光时刻, 4-推荐媒体"
    )


# ========================= 创建会话 =========================


class CreateSessionRequest(BaseModel):
    """创建会话请求"""

    title: str = Field(default="", max_length=200, description="会话标题")
    context: Optional[Dict[str, Any]] = Field(default=None, description="初始上下文")


class SessionData(BaseModel):
    """创建会话响应数据"""

    user_id: str = Field(default="", description="用户ID")
    session_id: str = Field(default="", description="会话ID")
    title: str = Field(default="", description="会话标题")
    create_time: str = Field(default="", description="创建时间")


# ========================= 会话列表 =========================


class SessionItem(BaseModel):
    """会话列表项"""

    session_id: str = Field(default="", description="会话ID")
    session_type: int = Field(default=1, description="会话类型")
    title: str = Field(default="", description="会话标题")
    message_count: int = Field(default=0, description="消息数量")
    is_pinned: bool = Field(default=False, description="是否置顶")
    last_message_at: str = Field(default="", description="最后消息时间")
    last_message_preview: str = Field(default="", description="最后消息预览")
    create_time: str = Field(default="", description="创建时间")


class SessionListRequest(BaseModel):
    """会话列表请求"""

    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=50, description="每页数量")


class SessionListData(PaginationData):
    """会话列表响应数据"""

    items: List[SessionItem] = Field(default_factory=list, description="会话列表")
    user_id: str = Field(default="", description="用户ID")


# ========================= 更新会话 =========================


class UpdateSessionRequest(BaseModel):
    """更新会话请求"""

    session_id: str = Field(description="会话ID")
    title: Optional[str] = Field(default=None, max_length=200, description="会话标题")
    is_pinned: Optional[bool] = Field(default=None, description="是否置顶")
    status: Optional[int] = Field(default=None, description="状态: 1-active, 2-archived")


# ========================= 删除会话 =========================


class DeleteSessionRequest(BaseModel):
    """删除会话请求"""

    session_id: str = Field(description="会话ID")


# ========================= 发送消息 =========================


class SendMessageRequest(BaseModel):
    """发送消息请求"""

    session_id: Optional[str] = Field(default=None, description="会话ID")
    source: Optional[Source] = Field(default=None, description="会话来源")
    content: str = Field(max_length=10000, description="消息内容")
    message_type: int = Field(
        default=3, description="消息类型: 1-video, 2-image, 3-text, 4-voice"
    )
    attachments: List[Attachment] = Field(default_factory=list, description="附件列表")


class MessageResponseData(BaseModel):
    """发送消息响应数据"""

    user_message: Optional[MessageItem] = Field(default=None, description="用户消息")
    ai_message: Optional[MessageItem] = Field(default=None, description="AI回复消息")
    session_updated: bool = Field(default=False, description="会话是否更新")


# ========================= 获取消息列表 =========================


class MessageListRequest(BaseModel):
    """获取消息列表请求"""

    session_id: str = Field(description="会话ID")
    message_id: str = Field(default="", description="消息ID，获取此消息之前的消息")
    limit: int = Field(default=50, ge=1, le=100, description="数量限制")


class MessageListData(BaseModel):
    """消息列表响应数据"""

    items: List[MessageItem] = Field(default_factory=list, description="消息列表")
    has_more: bool = Field(default=False, description="是否有更多")


# ========================= 停止生成 =========================


class StopWordRequest(BaseModel):
    """停止生成请求"""

    session_id: str = Field(description="会话ID")
    message_id: Optional[str] = Field(default=None, description="消息ID")
