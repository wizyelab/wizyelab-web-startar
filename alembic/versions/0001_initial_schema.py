"""initial schema: create all tables

Revision ID: 0001_initial
Revises:
Create Date: 2026-02-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '0001_initial'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables."""

    # ==================== users ====================
    op.create_table(
        'users',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='自增主键'),
        sa.Column('user_id', sa.String(20), nullable=False, comment='用户ID（雪花算法）'),
        sa.Column('firebase_uid', sa.String(128), nullable=True, comment='Firebase UID'),
        sa.Column('phone', sa.String(20), nullable=True, comment='手机号'),
        sa.Column('email', sa.String(255), nullable=True, comment='邮箱'),
        sa.Column('user_name', sa.String(50), nullable=True, comment='用户名'),
        sa.Column('avatar', sa.String(500), nullable=True, comment='头像URL'),
        sa.Column('bio', sa.String(500), nullable=True, comment='个人简介'),
        sa.Column('gender', mysql.TINYINT(unsigned=True), nullable=False, server_default='0', comment='性别：0-未知，1-男，2-女，3-其他'),
        sa.Column('location', sa.String(100), nullable=True, comment='位置'),
        sa.Column('login_provider', sa.String(20), nullable=True, comment='登录方式：google/apple/email/phone'),
        sa.Column('provider_token', sa.Text(), nullable=True, comment='第三方登录Token'),
        sa.Column('status', mysql.TINYINT(unsigned=True), nullable=False, server_default='1', comment='状态：0-删除，1-正常'),
        sa.Column('onboarding', sa.JSON(), nullable=True, comment='用户onboarding数据'),
        sa.Column('extra', sa.Text(), nullable=True, comment='扩展字段'),
        sa.Column('create_time', sa.BigInteger(), nullable=False, comment='创建时间'),
        sa.Column('update_time', sa.BigInteger(), nullable=False, comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
        sa.UniqueConstraint('firebase_uid'),
        sa.UniqueConstraint('phone'),
        sa.UniqueConstraint('email'),
        comment='用户信息表',
    )
    op.create_index('idx_create_time', 'users', ['create_time'])

    # ==================== user_devices ====================
    op.create_table(
        'user_devices',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='自增主键'),
        sa.Column('user_id', sa.String(20), nullable=False, comment='用户ID，关联users.user_id'),
        sa.Column('device_id', sa.String(100), nullable=False, comment='设备ID'),
        sa.Column('device_type', sa.String(20), nullable=True, comment='设备类型：ios/android'),
        sa.Column('device_name', sa.String(100), nullable=True, comment='设备名称'),
        sa.Column('push_token', sa.String(500), nullable=True, comment='推送Token'),
        sa.Column('app_version', sa.String(20), nullable=True, comment='App版本'),
        sa.Column('os_version', sa.String(20), nullable=True, comment='系统版本'),
        sa.Column('is_active', mysql.TINYINT(unsigned=True), nullable=False, server_default='1', comment='是否激活：0-否，1-是'),
        sa.Column('last_active_at', sa.BigInteger(), nullable=True, comment='最后活跃时间'),
        sa.Column('extra', sa.Text(), nullable=True, comment='扩展字段'),
        sa.Column('create_time', sa.BigInteger(), nullable=False, comment='创建时间'),
        sa.Column('update_time', sa.BigInteger(), nullable=False, comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        comment='用户设备表',
    )
    op.create_index('uk_user_device', 'user_devices', ['user_id', 'device_id'], unique=True)
    op.create_index('idx_user_id', 'user_devices', ['user_id'])
    op.create_index('idx_device_id', 'user_devices', ['device_id'])

    # ==================== user_sessions ====================
    op.create_table(
        'user_sessions',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='自增主键'),
        sa.Column('session_id', sa.String(36), nullable=False, comment='会话ID（UUID）'),
        sa.Column('user_id', sa.String(20), nullable=False, comment='用户ID，关联users.user_id'),
        sa.Column('device_id', sa.String(100), nullable=False, comment='设备ID'),
        sa.Column('custom_token', sa.Text(), nullable=True, comment='自定义Token'),
        sa.Column('refresh_token', sa.Text(), nullable=True, comment='刷新Token'),
        sa.Column('login_ip', sa.String(50), nullable=True, comment='登录IP'),
        sa.Column('login_location', sa.String(100), nullable=True, comment='登录地点'),
        sa.Column('is_valid', mysql.TINYINT(unsigned=True), nullable=False, server_default='1', comment='是否有效：0-否，1-是'),
        sa.Column('expires_at', sa.BigInteger(), nullable=True, comment='过期时间'),
        sa.Column('last_used_at', sa.BigInteger(), nullable=True, comment='最后使用时间'),
        sa.Column('extra', sa.Text(), nullable=True, comment='扩展字段'),
        sa.Column('create_time', sa.BigInteger(), nullable=False, comment='创建时间（即登录时间）'),
        sa.Column('update_time', sa.BigInteger(), nullable=False, comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id'),
        comment='用户会话记录表',
    )
    op.create_index('idx_session_user_id', 'user_sessions', ['user_id'])
    op.create_index('idx_session_device_id', 'user_sessions', ['device_id'])
    op.create_index('idx_expires_at', 'user_sessions', ['expires_at'])
    op.create_index('idx_user_device', 'user_sessions', ['user_id', 'device_id'])

    # ==================== user_profiles ====================
    op.create_table(
        'user_profiles',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='自增主键'),
        sa.Column('user_id', sa.String(20), nullable=False, comment='用户ID，关联users.user_id'),
        sa.Column('interest_tags', sa.JSON(), nullable=True, comment='兴趣标签ID列表，如[1,2,3]'),
        sa.Column('skill_level', sa.String(20), nullable=True, comment='技能等级：beginner/intermediate/advanced/professional'),
        sa.Column('equipment_config', sa.JSON(), nullable=True, comment='装备配置'),
        sa.Column('profile_data', sa.JSON(), nullable=True, comment='其他Profile数据（引导收集的数据）'),
        sa.Column('extra', sa.Text(), nullable=True, comment='扩展字段'),
        sa.Column('create_time', sa.BigInteger(), nullable=False, comment='创建时间'),
        sa.Column('update_time', sa.BigInteger(), nullable=False, comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
        comment='用户画像表',
    )
    op.create_index('idx_skill_level', 'user_profiles', ['skill_level'])

    # ==================== user_stats ====================
    op.create_table(
        'user_stats',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='自增主键'),
        sa.Column('user_id', sa.String(20), nullable=False, comment='用户ID，关联users.user_id'),
        sa.Column('follower_count', sa.Integer(), nullable=False, server_default='0', comment='粉丝数'),
        sa.Column('following_count', sa.Integer(), nullable=False, server_default='0', comment='关注数'),
        sa.Column('post_count', sa.Integer(), nullable=False, server_default='0', comment='帖子数'),
        sa.Column('like_count', sa.Integer(), nullable=False, server_default='0', comment='获赞数'),
        sa.Column('extra', sa.Text(), nullable=True, comment='扩展字段'),
        sa.Column('create_time', sa.BigInteger(), nullable=False, comment='创建时间'),
        sa.Column('update_time', sa.BigInteger(), nullable=False, comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
        comment='用户统计表',
    )

    # ==================== user_follows ====================
    op.create_table(
        'user_follows',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='自增主键'),
        sa.Column('follower_id', sa.String(20), nullable=False, comment='关注者ID'),
        sa.Column('following_id', sa.String(20), nullable=False, comment='被关注者ID'),
        sa.Column('status', mysql.TINYINT(unsigned=True), nullable=False, server_default='1', comment='状态：0-取消关注，1-关注中'),
        sa.Column('create_time', sa.BigInteger(), nullable=False, comment='创建时间'),
        sa.Column('update_time', sa.BigInteger(), nullable=False, comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        comment='用户关注关系表',
    )
    op.create_index('uk_follow_relation', 'user_follows', ['follower_id', 'following_id'], unique=True)
    op.create_index('idx_follower_id', 'user_follows', ['follower_id'])
    op.create_index('idx_following_id', 'user_follows', ['following_id'])

    # ==================== posts ====================
    op.create_table(
        'posts',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='自增主键'),
        sa.Column('post_id', sa.String(20), nullable=False, comment='帖子ID'),
        sa.Column('user_id', sa.String(20), nullable=False, comment='用户ID'),
        sa.Column('post_type', mysql.TINYINT(unsigned=True), nullable=False, server_default='3', comment='帖子类型：1-视频，2-图片，3-文本'),
        sa.Column('title', sa.String(200), nullable=True, comment='标题'),
        sa.Column('description', sa.Text(), nullable=True, comment='描述'),
        sa.Column('content', sa.Text(), nullable=True, comment='内容正文'),
        sa.Column('images', sa.Text(), nullable=True, comment='图片列表JSON(List[Image])'),
        sa.Column('video', sa.JSON(), nullable=True, comment='视频信息JSON'),
        sa.Column('like_count', sa.Integer(), nullable=False, server_default='0', comment='点赞数'),
        sa.Column('comment_count', sa.Integer(), nullable=False, server_default='0', comment='评论数'),
        sa.Column('share_count', sa.Integer(), nullable=False, server_default='0', comment='分享数'),
        sa.Column('view_count', sa.Integer(), nullable=False, server_default='0', comment='浏览数'),
        sa.Column('status', mysql.TINYINT(unsigned=True), nullable=False, server_default='1', comment='状态：0-草稿，1-正常，2-隐藏，3-删除'),
        sa.Column('source', mysql.TINYINT(), nullable=False, server_default='0', comment='来源：0-ugc, 1-pgc, 2-crawled'),
        sa.Column('source_platform', sa.String(50), nullable=True, comment='来源平台'),
        sa.Column('source_metadata', sa.JSON(), nullable=True, comment='爬取元数据'),
        sa.Column('extra', sa.Text(), nullable=True, comment='扩展字段'),
        sa.Column('create_time', sa.BigInteger(), nullable=False, comment='创建时间'),
        sa.Column('update_time', sa.BigInteger(), nullable=False, comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('post_id'),
        comment='帖子/内容表',
    )
    op.create_index('idx_post_user_id', 'posts', ['user_id'])
    op.create_index('idx_post_type', 'posts', ['post_type'])
    op.create_index('idx_post_status', 'posts', ['status'])
    op.create_index('idx_post_create_time', 'posts', ['create_time'])
    op.create_index('idx_user_status_time', 'posts', ['user_id', 'status', 'create_time'])

    # ==================== user_actions ====================
    op.create_table(
        'user_actions',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='自增主键'),
        sa.Column('user_id', sa.String(20), nullable=False, comment='用户ID'),
        sa.Column('target_type', sa.String(20), nullable=False, comment='目标类型：post/comment'),
        sa.Column('target_id', sa.String(20), nullable=False, comment='目标ID'),
        sa.Column('action_type', mysql.TINYINT(unsigned=True), nullable=False, comment='行为类型：0-浏览，1-点赞，2-收藏，3-分享'),
        sa.Column('status', mysql.TINYINT(unsigned=True), nullable=False, server_default='1', comment='是否有效：0-否，1-是'),
        sa.Column('extra', sa.Text(), nullable=True, comment='扩展字段'),
        sa.Column('create_time', sa.BigInteger(), nullable=False, comment='创建时间'),
        sa.Column('update_time', sa.BigInteger(), nullable=False, comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        comment='用户行为表',
    )
    op.create_index('uk_user_action', 'user_actions', ['user_id', 'target_type', 'target_id', 'action_type'], unique=True)
    op.create_index('idx_action_target', 'user_actions', ['target_type', 'target_id'])

    # ==================== user_feedbacks ====================
    op.create_table(
        'user_feedbacks',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='自增主键'),
        sa.Column('user_id', sa.String(20), nullable=False, comment='用户ID'),
        sa.Column('post_id', sa.String(20), nullable=True, comment='帖子ID'),
        sa.Column('feedback_type', mysql.TINYINT(unsigned=True), nullable=False, comment='反馈类型：1-不喜欢，2-不感兴趣，3-举报，4-垃圾'),
        sa.Column('reason', sa.String(200), nullable=True, comment='反馈原因'),
        sa.Column('detail', sa.Text(), nullable=True, comment='详细描述'),
        sa.Column('status', mysql.TINYINT(unsigned=True), nullable=False, server_default='0', comment='处理状态：0-待处理，1-已处理，2-已忽略'),
        sa.Column('processed_at', sa.BigInteger(), nullable=True, comment='处理时间'),
        sa.Column('extra', sa.Text(), nullable=True, comment='扩展字段'),
        sa.Column('create_time', sa.BigInteger(), nullable=False, comment='创建时间'),
        sa.Column('update_time', sa.BigInteger(), nullable=False, comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        comment='用户反馈表',
    )
    op.create_index('idx_feedback_user_id', 'user_feedbacks', ['user_id'])
    op.create_index('idx_feedback_post_id', 'user_feedbacks', ['post_id'])

    # ==================== guide_items ====================
    op.create_table(
        'guide_items',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='自增主键'),
        sa.Column('tag_id', sa.BigInteger(), nullable=False, comment='标签id'),
        sa.Column('style', mysql.TINYINT(unsigned=True), nullable=False, server_default='0', comment='引导样式：0-对话式，1-选项条，2-选项卡'),
        sa.Column('guide_words', sa.Text(), nullable=True, comment='引导话术'),
        sa.Column('profile_key', sa.String(50), nullable=True, comment='对应profile字段名'),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0', comment='排序'),
        sa.Column('options', sa.JSON(), nullable=True, comment='选项列表JSON'),
        sa.Column('head_img', sa.JSON(), nullable=True, comment='Logo上半部分图片'),
        sa.Column('body_img', sa.JSON(), nullable=True, comment='Logo下半部分图片'),
        sa.Column('status', mysql.TINYINT(unsigned=True), nullable=False, server_default='1', comment='状态：0-禁用，1-启用'),
        sa.Column('extra', sa.Text(), nullable=True, comment='扩展字段'),
        sa.Column('create_time', sa.BigInteger(), nullable=False, comment='创建时间'),
        sa.Column('update_time', sa.BigInteger(), nullable=False, comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        comment='引导配置表',
    )
    op.create_index('idx_sort_order', 'guide_items', ['sort_order'])

    # ==================== tags ====================
    op.create_table(
        'tags',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='自增主键, 标签ID'),
        sa.Column('tag_name', sa.String(50), nullable=False, comment='标签名称：Padel/Tennis/Pickleball'),
        sa.Column('tag_icon', sa.String(500), nullable=True, comment='标签图标URL'),
        sa.Column('tag_category', sa.String(50), nullable=True, comment='标签分类：sport/equipment/skill'),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0', comment='排序，数字越小越靠前'),
        sa.Column('status', mysql.TINYINT(unsigned=True), nullable=False, server_default='1', comment='状态：0-禁用，1-启用'),
        sa.Column('extra', sa.Text(), nullable=True, comment='扩展字段'),
        sa.Column('create_time', sa.BigInteger(), nullable=False, comment='创建时间'),
        sa.Column('update_time', sa.BigInteger(), nullable=False, comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        comment='标签表',
    )
    op.create_index('idx_tag_sort_order', 'tags', ['sort_order'])

    # ==================== user_tags ====================
    op.create_table(
        'user_tags',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='自增主键'),
        sa.Column('user_id', sa.String(20), nullable=False, comment='用户ID，关联users.user_id'),
        sa.Column('tag_id', sa.BigInteger(), nullable=False, comment='标签ID，关联tags.id'),
        sa.Column('level', sa.String(20), nullable=True, comment='等级：beginner/intermediate/advanced/professional'),
        sa.Column('priority', mysql.TINYINT(unsigned=True), server_default='0', comment='优先级/偏好程度，数字越大越优先'),
        sa.Column('status', mysql.TINYINT(unsigned=True), nullable=False, server_default='1', comment='状态：0-删除，1-正常'),
        sa.Column('extra', sa.Text(), nullable=True, comment='扩展字段'),
        sa.Column('create_time', sa.BigInteger(), nullable=False, comment='创建时间'),
        sa.Column('update_time', sa.BigInteger(), nullable=False, comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        comment='用户标签关联表',
    )
    op.create_index('uk_user_tag', 'user_tags', ['user_id', 'tag_id'], unique=True)

    # ==================== multimedia ====================
    op.create_table(
        'multimedia',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='自增主键'),
        sa.Column('file_id', sa.String(20), nullable=False, comment='文件ID（雪花算法）'),
        sa.Column('user_id', sa.String(20), nullable=False, comment='上传用户ID'),
        sa.Column('file_type', mysql.TINYINT(unsigned=True), nullable=False, comment='文件类型：1=视频,2=图片,3=文档,4=音频,5=其他'),
        sa.Column('file_name', sa.String(255), nullable=False, comment='原始文件名'),
        sa.Column('file_ext', sa.String(20), nullable=False, server_default='', comment='文件扩展名'),
        sa.Column('mime_type', sa.String(100), nullable=False, server_default='', comment='MIME类型'),
        sa.Column('file_size', sa.BigInteger(), nullable=False, server_default='0', comment='文件大小（字节）'),
        sa.Column('storage_type', mysql.TINYINT(unsigned=True), nullable=False, server_default='2', comment='存储类型：1=本地,2=OSS,3=S3,4=COS'),
        sa.Column('original_uri', sa.String(500), nullable=False, server_default='', comment='原始存储路径（OSS key）'),
        sa.Column('width', sa.Integer(), nullable=False, server_default='0', comment='宽度（图片/视频）'),
        sa.Column('height', sa.Integer(), nullable=False, server_default='0', comment='高度（图片/视频）'),
        sa.Column('duration', sa.Integer(), nullable=False, server_default='0', comment='时长秒数（视频/音频）'),
        sa.Column('multi_imgs', sa.Text(), nullable=True, comment='多尺寸图片（JSON格式）'),
        sa.Column('status', mysql.TINYINT(unsigned=True), nullable=False, server_default='0', comment='状态：0=上传中,1=成功,2=失败,3=已删除'),
        sa.Column('hash_md5', sa.String(32), nullable=False, server_default='', comment='文件MD5（用于去重）'),
        sa.Column('hash_sha256', sa.String(64), nullable=False, server_default='', comment='文件SHA256'),
        sa.Column('extra', sa.Text(), nullable=True, comment='扩展字段（JSON格式）'),
        sa.Column('create_time', sa.BigInteger(), nullable=False, comment='创建时间（毫秒时间戳）'),
        sa.Column('update_time', sa.BigInteger(), nullable=False, comment='更新时间（毫秒时间戳）'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('file_id'),
        comment='多媒体文件表',
    )
    op.create_index('idx_user_type', 'multimedia', ['user_id', 'file_type'])
    op.create_index('idx_mm_status', 'multimedia', ['status'])
    op.create_index('idx_hash_md5', 'multimedia', ['hash_md5'])
    op.create_index('idx_user_md5', 'multimedia', ['user_id', 'hash_md5'])


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table('multimedia')
    op.drop_table('user_tags')
    op.drop_table('tags')
    op.drop_table('guide_items')
    op.drop_table('user_feedbacks')
    op.drop_table('user_actions')
    op.drop_table('posts')
    op.drop_table('user_follows')
    op.drop_table('user_stats')
    op.drop_table('user_profiles')
    op.drop_table('user_sessions')
    op.drop_table('user_devices')
    op.drop_table('users')
