"""
Profile 模块数据库模型

包含用户画像、统计、关注关系、帖子、用户行为、反馈、引导配置、标签
"""

import time
from enum import IntEnum

from sqlalchemy import Column, BigInteger, String, Text, Integer, Index, JSON
from sqlalchemy.dialects.mysql import TINYINT

from app.infrastructure.database.connection import Base
from app.core.snowflake import generate_id_str


def current_timestamp_ms() -> int:
    """获取当前毫秒级时间戳"""
    return int(time.time() * 1000)


def generate_post_id() -> str:
    """生成帖子ID"""
    return generate_id_str()


# ========================= 枚举定义 =========================


class Gender(IntEnum):
    """性别枚举"""
    UNKNOWN = 0
    MALE = 1
    FEMALE = 2
    OTHER = 3


class PostType(IntEnum):
    """帖子类型枚举"""
    VIDEO = 1
    IMAGE = 2
    TEXT = 3


class PostStatus(IntEnum):
    """帖子状态枚举"""
    DRAFT = 0
    NORMAL = 1
    HIDDEN = 2
    DELETED = 3


class ActionType(IntEnum):
    """用户行为类型枚举"""
    VIEW = 0
    LIKE = 1
    COLLECT = 2
    SHARE = 3


class FeedbackType(IntEnum):
    """反馈类型枚举"""
    DISLIKE = 1
    NOT_INTERESTED = 2
    REPORT = 3
    SPAM = 4


class GuideStyle(IntEnum):
    """引导样式枚举"""
    DIALOG = 0
    BAR = 1
    CARD = 2


# ========================= Model 定义 =========================


class UserProfile(Base):
    """
    用户画像表

    存储用户的兴趣标签、技能等级、装备配置等画像数据
    """
    __tablename__ = "user_profiles"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="自增主键")
    user_id = Column(String(20), unique=True, nullable=False, comment="用户ID，关联users.user_id")

    # 画像数据
    interest_tags = Column(JSON, nullable=True, comment="兴趣标签ID列表，如[1,2,3]")
    skill_level = Column(String(20), nullable=True, comment="技能等级：beginner/intermediate/advanced/professional")
    equipment_config = Column(JSON, nullable=True, comment="装备配置")
    profile_data = Column(JSON, nullable=True, comment="其他Profile数据（引导收集的数据）")

    extra = Column(Text, nullable=True, comment="扩展字段")
    create_time = Column(BigInteger, nullable=False, default=current_timestamp_ms, comment="创建时间")
    update_time = Column(BigInteger, nullable=False, default=current_timestamp_ms, onupdate=current_timestamp_ms, comment="更新时间")

    __table_args__ = (
        Index("idx_skill_level", "skill_level"),
        {"comment": "用户画像表"},
    )


class UserStats(Base):
    """
    用户统计表

    存储用户的粉丝数、关注数、帖子数等统计数据
    """
    __tablename__ = "user_stats"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="自增主键")
    user_id = Column(String(20), unique=True, nullable=False, comment="用户ID，关联users.user_id")

    # 统计数据
    follower_count = Column(Integer, nullable=False, default=0, comment="粉丝数")
    following_count = Column(Integer, nullable=False, default=0, comment="关注数")
    post_count = Column(Integer, nullable=False, default=0, comment="帖子数")
    like_count = Column(Integer, nullable=False, default=0, comment="获赞数")

    extra = Column(Text, nullable=True, comment="扩展字段")
    create_time = Column(BigInteger, nullable=False, default=current_timestamp_ms, comment="创建时间")
    update_time = Column(BigInteger, nullable=False, default=current_timestamp_ms, onupdate=current_timestamp_ms, comment="更新时间")

    __table_args__ = (
        {"comment": "用户统计表"},
    )


class UserFollow(Base):
    """
    用户关注关系表
    """
    __tablename__ = "user_follows"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="自增主键")
    follower_id = Column(String(20), nullable=False, comment="关注者ID")
    following_id = Column(String(20), nullable=False, comment="被关注者ID")
    status = Column(TINYINT(unsigned=True), nullable=False, default=1, comment="状态：0-取消关注，1-关注中")

    create_time = Column(BigInteger, nullable=False, default=current_timestamp_ms, comment="创建时间")
    update_time = Column(BigInteger, nullable=False, default=current_timestamp_ms, onupdate=current_timestamp_ms, comment="更新时间")

    __table_args__ = (
        Index("uk_follow_relation", "follower_id", "following_id", unique=True),
        Index("idx_follower_id", "follower_id"),
        Index("idx_following_id", "following_id"),
        {"comment": "用户关注关系表"},
    )


class Post(Base):
    """
    帖子/内容表
    """
    __tablename__ = "posts"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="自增主键")
    post_id = Column(String(20), unique=True, nullable=False, default=generate_post_id, comment="帖子ID")
    user_id = Column(String(20), nullable=False, comment="用户ID")

    # 内容
    post_type = Column(TINYINT(unsigned=True), nullable=False, default=PostType.TEXT, comment="帖子类型：1-视频，2-图片，3-文本")
    title = Column(String(200), nullable=True, comment="标题")
    description = Column(Text, nullable=True, comment="描述")
    content = Column(Text, nullable=True, comment="内容正文")
    images = Column(Text, nullable=True, comment="图片列表JSON(List[Image])")
    video = Column(JSON, nullable=True, comment="视频信息JSON")

    # 统计
    like_count = Column(Integer, nullable=False, default=0, comment="点赞数")
    comment_count = Column(Integer, nullable=False, default=0, comment="评论数")
    share_count = Column(Integer, nullable=False, default=0, comment="分享数")
    view_count = Column(Integer, nullable=False, default=0, comment="浏览数")

    # 状态
    status = Column(TINYINT(unsigned=True), nullable=False, default=PostStatus.NORMAL, comment="状态：0-草稿，1-正常，2-隐藏，3-删除")
    source = Column(TINYINT, nullable=False, default=0, comment="来源：0-ugc, 1-pgc, 2-crawled")
    source_platform = Column(String(50), nullable=True, comment="来源平台")
    source_metadata = Column(JSON, nullable=True, comment="爬取元数据")

    extra = Column(Text, nullable=True, comment="扩展字段")
    create_time = Column(BigInteger, nullable=False, default=current_timestamp_ms, comment="创建时间")
    update_time = Column(BigInteger, nullable=False, default=current_timestamp_ms, onupdate=current_timestamp_ms, comment="更新时间")

    __table_args__ = (
        Index("idx_post_user_id", "user_id"),
        Index("idx_post_type", "post_type"),
        Index("idx_post_status", "status"),
        Index("idx_post_create_time", "create_time"),
        Index("idx_user_status_time", "user_id", "status", "create_time"),
        {"comment": "帖子/内容表"},
    )


class UserAction(Base):
    """
    用户行为表（点赞/收藏/分享）
    """
    __tablename__ = "user_actions"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="自增主键")
    user_id = Column(String(20), nullable=False, comment="用户ID")
    target_type = Column(String(20), nullable=False, comment="目标类型：post/comment")
    target_id = Column(String(20), nullable=False, comment="目标ID")
    action_type = Column(TINYINT(unsigned=True), nullable=False, comment="行为类型：0-浏览，1-点赞，2-收藏，3-分享")
    status = Column(TINYINT(unsigned=True), nullable=False, default=1, comment="是否有效：0-否，1-是")

    extra = Column(Text, nullable=True, comment="扩展字段")
    create_time = Column(BigInteger, nullable=False, default=current_timestamp_ms, comment="创建时间")
    update_time = Column(BigInteger, nullable=False, default=current_timestamp_ms, onupdate=current_timestamp_ms, comment="更新时间")

    __table_args__ = (
        Index("uk_user_action", "user_id", "target_type", "target_id", "action_type", unique=True),
        Index("idx_action_target", "target_type", "target_id"),
        {"comment": "用户行为表"},
    )


class UserFeedback(Base):
    """
    用户反馈表
    """
    __tablename__ = "user_feedbacks"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="自增主键")
    user_id = Column(String(20), nullable=False, comment="用户ID")
    post_id = Column(String(20), nullable=True, comment="帖子ID")
    feedback_type = Column(TINYINT(unsigned=True), nullable=False, comment="反馈类型：1-不喜欢，2-不感兴趣，3-举报，4-垃圾")
    reason = Column(String(200), nullable=True, comment="反馈原因")
    detail = Column(Text, nullable=True, comment="详细描述")
    status = Column(TINYINT(unsigned=True), nullable=False, default=0, comment="处理状态：0-待处理，1-已处理，2-已忽略")
    processed_at = Column(BigInteger, nullable=True, comment="处理时间")

    extra = Column(Text, nullable=True, comment="扩展字段")
    create_time = Column(BigInteger, nullable=False, default=current_timestamp_ms, comment="创建时间")
    update_time = Column(BigInteger, nullable=False, default=current_timestamp_ms, onupdate=current_timestamp_ms, comment="更新时间")

    __table_args__ = (
        Index("idx_feedback_user_id", "user_id"),
        Index("idx_feedback_post_id", "post_id"),
        {"comment": "用户反馈表"},
    )


class GuideItemModel(Base):
    """
    引导配置表
    """
    __tablename__ = "guide_items"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="自增主键")
    tag_id = Column(BigInteger, nullable=False, comment="标签id")
    style = Column(TINYINT(unsigned=True), nullable=False, default=0, comment="引导样式：0-对话式，1-选项条，2-选项卡")
    guide_words = Column(Text, nullable=True, comment="引导话术")
    profile_key = Column(String(50), nullable=True, comment="对应profile字段名")
    sort_order = Column(Integer, nullable=False, default=0, comment="排序")
    options = Column(JSON, nullable=True, comment="选项列表JSON")
    head_img = Column(JSON, nullable=True, comment="Logo上半部分图片")
    body_img = Column(JSON, nullable=True, comment="Logo下半部分图片")
    status = Column(TINYINT(unsigned=True), nullable=False, default=1, comment="状态：0-禁用，1-启用")

    extra = Column(Text, nullable=True, comment="扩展字段")
    create_time = Column(BigInteger, nullable=False, default=current_timestamp_ms, comment="创建时间")
    update_time = Column(BigInteger, nullable=False, default=current_timestamp_ms, onupdate=current_timestamp_ms, comment="更新时间")

    __table_args__ = (
        Index("idx_sort_order", "sort_order"),
        {"comment": "引导配置表"},
    )


class Tag(Base):
    """
    标签表
    """
    __tablename__ = "tags"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="自增主键, 标签ID")
    tag_name = Column(String(50), nullable=False, comment="标签名称：Padel/Tennis/Pickleball")
    tag_icon = Column(String(500), nullable=True, comment="标签图标URL")
    tag_category = Column(String(50), nullable=True, comment="标签分类：sport/equipment/skill")
    sort_order = Column(Integer, nullable=False, default=0, comment="排序，数字越小越靠前")
    status = Column(TINYINT(unsigned=True), nullable=False, default=1, comment="状态：0-禁用，1-启用")

    extra = Column(Text, nullable=True, comment="扩展字段")
    create_time = Column(BigInteger, nullable=False, default=current_timestamp_ms, comment="创建时间")
    update_time = Column(BigInteger, nullable=False, default=current_timestamp_ms, onupdate=current_timestamp_ms, comment="更新时间")

    __table_args__ = (
        Index("idx_sort_order", "sort_order"),
        {"comment": "标签表"},
    )


class UserTag(Base):
    """
    用户标签关联表

    存储用户与标签的多对多关联关系
    """
    __tablename__ = "user_tags"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="自增主键")
    user_id = Column(String(20), nullable=False, comment="用户ID，关联users.user_id")
    tag_id = Column(BigInteger, nullable=False, comment="标签ID，关联tags.id")
    level = Column(String(20), nullable=True, comment="等级：beginner/intermediate/advanced/professional")
    priority = Column(TINYINT(unsigned=True), default=0, comment="优先级/偏好程度，数字越大越优先")
    status = Column(TINYINT(unsigned=True), nullable=False, default=1, comment="状态：0-删除，1-正常")

    extra = Column(Text, nullable=True, comment="扩展字段")
    create_time = Column(BigInteger, nullable=False, default=current_timestamp_ms, comment="创建时间")
    update_time = Column(BigInteger, nullable=False, default=current_timestamp_ms, onupdate=current_timestamp_ms, comment="更新时间")

    __table_args__ = (
        Index("uk_user_tag", "user_id", "tag_id", unique=True),
        {"comment": "用户标签关联表"},
    )
