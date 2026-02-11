"""
Profile 服务模块

处理用户资料、帖子、反馈等业务逻辑
"""
import json
from datetime import datetime
from typing import Optional, Tuple, List, Dict, Any

from sqlalchemy import select, update, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import setup_logger
from app.core.error_codes import ErrorCode
from app.models.user import User
from app.models.profile import (
    UserStats, UserFollow, Post, UserAction,
    UserFeedback, GuideItemModel, PostStatus, ActionType,
    current_timestamp_ms
)
from app.schemas.common import Video, Image, Author
from app.schemas.profile import (
    ProfileData, GuideData, GuideItem, OptionItem,
    ProfilePost, ProfilePostsData, CreatePostData,
    FollowData, FollowListData, UserItem
)

logger = setup_logger(__name__)


class ProfileService:
    """Profile 服务类"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ==================== Profile 相关 ====================

    async def get_profile(
        self, target_user_id: str, current_user_id: Optional[str]
    ) -> Tuple[int, str, Optional[ProfileData]]:
        """
        获取用户 Profile

        查询流程：
        1. 查询 users 表获取基本信息和 onboarding 数据
        2. 查询 user_stats 表获取统计数据
        3. 查询 user_follows 表判断是否已关注
        """
        try:
            # 1. 查询用户基本信息（包含 onboarding）
            stmt = select(User).where(User.user_id == target_user_id, User.status == 1)
            result = await self.db.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                return ErrorCode.USER_NOT_FOUND, "用户不存在", None

            # 2. 解析 onboarding 中的 interest_tags
            interest_tags = []
            if user.onboarding:
                try:
                    onboarding_data = json.loads(user.onboarding) if isinstance(user.onboarding, str) else user.onboarding
                    interest_tags = onboarding_data.get("interest_tags", [])
                except (json.JSONDecodeError, TypeError):
                    pass

            # 3. 查询用户统计
            stmt = select(UserStats).where(UserStats.user_id == target_user_id)
            result = await self.db.execute(stmt)
            stats = result.scalar_one_or_none()

            # 4. 查询关注状态
            is_followed = False
            if current_user_id and current_user_id != target_user_id:
                is_followed = await self._check_follow_status(current_user_id, target_user_id)

            # 5. 构建响应
            return ErrorCode.SUCCESS, "成功", ProfileData(
                user_id=user.user_id,
                user_name=user.user_name or "",
                avatar=user.avatar or "",
                bio=user.bio or "",
                gender=user.gender or 0,
                location=user.location or "",
                interest_tags=interest_tags,
                follower_count=stats.follower_count if stats else 0,
                following_count=stats.following_count if stats else 0,
                post_count=stats.post_count if stats else 0,
                is_followed=is_followed,
                is_self=(current_user_id == target_user_id),
            )
        except Exception as e:
            logger.error(f"获取用户Profile失败: {e}")
            return ErrorCode.GENERAL_ERROR, "系统错误", None

    async def update_profile(
        self, user_id: str, data: Dict[str, Any]
    ) -> Tuple[int, str]:
        """
        更新 Profile

        更新流程：
        1. 分离基本信息字段和 onboarding 字段
        2. 更新 users 表（name, avatar, bio, gender, location）
        3. 更新 users.onboarding 字段（原 user_profiles.profile_data）
        """
        try:
            # 1. 分离字段
            user_fields = {"name", "avatar", "bio", "gender", "location", "onboarding"}
            profile_fields = {"interest_tags", "skill_level", "equipment_config", "extra"}

            user_data = {}
            extra = {}

            for key, value in data.items():
                if value is None:
                    continue
                if isinstance(value, dict):
                    value = json.dumps(value)
                if key in user_fields:
                    # name -> user_name
                    db_key = "user_name" if key == "name" else key
                    user_data[db_key] = value
                else:
                    extra[key] = value

            # 2. 查询现有用户
            stmt = select(User).where(User.user_id == user_id)
            result = await self.db.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                return ErrorCode.USER_NOT_FOUND, "用户不存在"

            # 3. 更新 users 表基本字段
            if extra:
                user_data['extra'] = json.dumps(extra)
            if user_data:
                user_data["update_time"] = current_timestamp_ms()
                stmt = (
                    update(User)
                    .where(User.user_id == user_id)
                    .values(**user_data)
                )
                await self.db.execute(stmt)
            await self.db.commit()
            return ErrorCode.SUCCESS, "成功"

        except Exception as e:
            logger.error(f"更新Profile失败: {e}")
            await self.db.rollback()
            return ErrorCode.GENERAL_ERROR, "系统错误"

    # ==================== 引导相关 ====================

    async def get_guide_list(self, tag_id: int = 0) -> Tuple[int, str, Optional[GuideData]]:
        """
        获取引导列表

        查询 guide_items 表，按 sort_order 排序
        tag_id=0 返回全部，否则按 tag_id 过滤
        """
        try:
            stmt = (
                select(GuideItemModel)
                .where(GuideItemModel.status == 1)
            )
            if tag_id > 0:
                stmt = stmt.where(GuideItemModel.tag_id == tag_id)
            stmt = stmt.order_by(GuideItemModel.sort_order)
            result = await self.db.execute(stmt)
            guide_items = result.scalars().all()

            items = []
            for item in guide_items:
                options = []
                if item.options:
                    for opt in item.options:
                        options.append(OptionItem(
                            content=opt.get("content", ""),
                            description=opt.get("description", ""),
                            icon_url=opt.get("icon_url", ""),
                        ))

                # 构建 head_img
                head_img = None
                if item.head_img:
                    head_img = Image(
                        id=item.head_img.get("id", ""),
                        height=item.head_img.get("height", 0),
                        width=item.head_img.get("width", 0),
                        format=item.head_img.get("format", ""),
                        size=item.head_img.get("size", 0),
                        main_url=item.head_img.get("main_url", ""),
                        back_urls=item.head_img.get("back_urls", []),
                    )

                # 构建 body_img
                body_img = None
                if item.body_img:
                    body_img = Image(
                        id=item.body_img.get("id", ""),
                        height=item.body_img.get("height", 0),
                        width=item.body_img.get("width", 0),
                        format=item.body_img.get("format", ""),
                        size=item.body_img.get("size", 0),
                        main_url=item.body_img.get("main_url", ""),
                        back_urls=item.body_img.get("back_urls", []),
                    )

                items.append(GuideItem(
                    id=item.id,
                    tag_id=item.tag_id,
                    style=item.style,
                    guide_words=item.guide_words or "",
                    profile_key=item.profile_key or "",
                    sort=item.sort_order,
                    options=options,
                    head_img=head_img,
                    body_img=body_img,
                ))

            return ErrorCode.SUCCESS, "成功", GuideData(
                items=items,
                total_steps=len(items),
            )
        except Exception as e:
            logger.error(f"获取引导列表失败: {e}")
            return ErrorCode.GENERAL_ERROR, "系统错误", None

    # ==================== 帖子相关 ====================

    async def get_user_posts(
        self, target_user_id: str, current_user_id: Optional[str],
        page: int, page_size: int
    ) -> Tuple[int, str, Optional[ProfilePostsData]]:
        """
        获取用户帖子列表

        查询流程：
        1. 查询作者信息
        2. 查询总数
        3. 分页查询帖子
        4. 批量查询用户行为状态
        5. 构建响应
        """
        try:
            # 1. 查询作者信息
            stmt = select(User).where(User.user_id == target_user_id)
            result = await self.db.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                return ErrorCode.USER_NOT_FOUND, "用户不存在", None

            # 2. 查询总数
            count_stmt = (
                select(func.count())
                .select_from(Post)
                .where(
                    Post.user_id == target_user_id,
                    Post.status == PostStatus.NORMAL
                )
            )
            count_result = await self.db.execute(count_stmt)
            total = count_result.scalar() or 0

            # 3. 分页查询帖子
            offset = (page - 1) * page_size
            stmt = (
                select(Post)
                .where(
                    Post.user_id == target_user_id,
                    Post.status == PostStatus.NORMAL
                )
                .order_by(Post.create_time.desc())
                .offset(offset)
                .limit(page_size)
            )
            result = await self.db.execute(stmt)
            posts = result.scalars().all()

            # 4. 批量查询用户行为状态
            post_ids = [p.post_id for p in posts]
            action_status = {}
            if current_user_id and post_ids:
                action_status = await self._batch_check_actions(
                    current_user_id, "post", post_ids
                )

            # 5. 查询关注状态
            is_followed = False
            if current_user_id and current_user_id != target_user_id:
                is_followed = await self._check_follow_status(current_user_id, target_user_id)

            # 6. 构建响应
            items = []
            for post in posts:
                post_action = action_status.get(post.post_id, {})

                video_data = None
                if post.video:
                    video_data = Video(
                        id=post.video.get("id", ""),
                        height=post.video.get("height", 0),
                        width=post.video.get("width", 0),
                        duration=post.video.get("duration", 0),
                        cover=post.video.get("cover"),
                        main_url=post.video.get("main_url", ""),
                        back_urls=post.video.get("back_urls", []),
                    )

                items.append(ProfilePost(
                    id=post.post_id,
                    post_type=post.post_type,
                    title=post.title or "",
                    description=post.description or "",
                    content=post.content or "",
                    images=json.loads(post.images) if post.images else [],
                    video=video_data,
                    author=Author(
                        user_id=user.user_id,
                        user_name=user.user_name or "",
                        avatar=user.avatar or "",
                        is_followed=is_followed,
                    ),
                    like_count=post.like_count,
                    comment_count=post.comment_count,
                    share_count=post.share_count,
                    is_liked=post_action.get(ActionType.LIKE, False),
                    is_collected=post_action.get(ActionType.COLLECT, False),
                    create_time=self._format_timestamp(post.create_time),
                    update_time=self._format_timestamp(post.update_time),
                    display_time=self._format_display_time(post.create_time),
                ))

            has_more = (page * page_size) < total

            return ErrorCode.SUCCESS, "成功", ProfilePostsData(
                items=items,
                total=total,
                page=page,
                page_size=page_size,
                has_more=has_more,
            )
        except Exception as e:
            logger.error(f"获取用户帖子列表失败: {e}")
            return ErrorCode.GENERAL_ERROR, "系统错误", None

    async def create_post(
        self, user_id: str, post_type: int, title: str,
        description: str, content: str, images: List[Dict],
        video: Optional[Dict], tags: List[int]
    ) -> Tuple[int, str, Optional[CreatePostData]]:
        """
        创建帖子

        流程：
        1. 插入 posts 表
        2. 更新 user_stats.post_count
        """
        try:
            post = Post(
                user_id=user_id,
                post_type=post_type,
                title=title,
                description=description,
                content=content,
                images=json.dumps(images) if images else None,
                video=video,
                status=PostStatus.NORMAL,
            )
            self.db.add(post)
            await self.db.flush()

            # 更新用户统计
            stats = await self._get_or_create_user_stats(user_id)
            stats.post_count += 1

            await self.db.commit()

            return ErrorCode.SUCCESS, "成功", CreatePostData(post_id=post.post_id)
        except Exception as e:
            logger.error(f"创建帖子失败: {e}")
            await self.db.rollback()
            return ErrorCode.GENERAL_ERROR, "系统错误", None

    async def delete_post(
        self, user_id: str, post_id: str
    ) -> Tuple[int, str]:
        """
        删除帖子（软删除）

        流程：
        1. 校验帖子归属
        2. 软删除
        3. 更新 user_stats.post_count
        """
        try:
            stmt = select(Post).where(Post.post_id == post_id)
            result = await self.db.execute(stmt)
            post = result.scalar_one_or_none()

            if not post:
                return ErrorCode.POST_NOT_FOUND, "帖子不存在"

            if post.user_id != user_id:
                return ErrorCode.POST_NO_PERMISSION, "无权操作此帖子"

            if post.status == PostStatus.DELETED:
                return ErrorCode.POST_DELETED, "帖子已删除"

            post.status = PostStatus.DELETED
            post.update_time = current_timestamp_ms()

            stats = await self._get_or_create_user_stats(user_id)
            if stats.post_count > 0:
                stats.post_count -= 1

            await self.db.commit()
            return ErrorCode.SUCCESS, "成功"
        except Exception as e:
            logger.error(f"删除帖子失败: {e}")
            await self.db.rollback()
            return ErrorCode.GENERAL_ERROR, "系统错误"

    # ==================== 关注相关 ====================

    async def follow_user(
        self, user_id: str, target_user_id: str, is_follow: bool
    ) -> Tuple[int, str, Optional[FollowData]]:
        """关注/取关用户"""
        try:
            if user_id == target_user_id:
                return ErrorCode.CANNOT_FOLLOW_SELF, "不能关注自己", None

            stmt = select(User).where(User.user_id == target_user_id, User.status == 1)
            result = await self.db.execute(stmt)
            target_user = result.scalar_one_or_none()

            if not target_user:
                return ErrorCode.USER_NOT_FOUND, "用户不存在", None

            stmt = select(UserFollow).where(
                UserFollow.follower_id == user_id,
                UserFollow.following_id == target_user_id
            )
            result = await self.db.execute(stmt)
            follow = result.scalar_one_or_none()

            if is_follow:
                if follow and follow.status == 1:
                    return ErrorCode.ALREADY_FOLLOWED, "已经关注该用户", None

                if follow:
                    follow.status = 1
                    follow.update_time = current_timestamp_ms()
                else:
                    follow = UserFollow(
                        follower_id=user_id,
                        following_id=target_user_id,
                        status=1,
                    )
                    self.db.add(follow)

                my_stats = await self._get_or_create_user_stats(user_id)
                target_stats = await self._get_or_create_user_stats(target_user_id)
                my_stats.following_count += 1
                target_stats.follower_count += 1
            else:
                if not follow or follow.status == 0:
                    return ErrorCode.NOT_FOLLOWED, "未关注该用户", None

                follow.status = 0
                follow.update_time = current_timestamp_ms()

                my_stats = await self._get_or_create_user_stats(user_id)
                target_stats = await self._get_or_create_user_stats(target_user_id)
                if my_stats.following_count > 0:
                    my_stats.following_count -= 1
                if target_stats.follower_count > 0:
                    target_stats.follower_count -= 1

            await self.db.commit()

            return ErrorCode.SUCCESS, "成功", FollowData(
                is_followed=is_follow,
                follower_count=target_stats.follower_count,
            )
        except Exception as e:
            logger.error(f"关注/取关失败: {e}")
            await self.db.rollback()
            return ErrorCode.GENERAL_ERROR, "系统错误", None

    async def get_followers(
        self, user_id: str, current_user_id: Optional[str],
        page: int, page_size: int
    ) -> Tuple[int, str, Optional[FollowListData]]:
        """获取粉丝列表"""
        try:
            count_stmt = (
                select(func.count())
                .select_from(UserFollow)
                .where(
                    UserFollow.following_id == user_id,
                    UserFollow.status == 1
                )
            )
            count_result = await self.db.execute(count_stmt)
            total = count_result.scalar() or 0

            offset = (page - 1) * page_size
            stmt = (
                select(UserFollow)
                .where(
                    UserFollow.following_id == user_id,
                    UserFollow.status == 1
                )
                .order_by(UserFollow.create_time.desc())
                .offset(offset)
                .limit(page_size)
            )
            result = await self.db.execute(stmt)
            follows = result.scalars().all()

            follower_ids = [f.follower_id for f in follows]
            users_map = {}
            if follower_ids:
                stmt = select(User).where(User.user_id.in_(follower_ids))
                result = await self.db.execute(stmt)
                users = result.scalars().all()
                users_map = {u.user_id: u for u in users}

            following_status = {}
            if current_user_id and follower_ids:
                stmt = select(UserFollow).where(
                    UserFollow.follower_id == current_user_id,
                    UserFollow.following_id.in_(follower_ids),
                    UserFollow.status == 1
                )
                result = await self.db.execute(stmt)
                my_follows = result.scalars().all()
                following_status = {f.following_id: True for f in my_follows}

            items = []
            for follow in follows:
                user = users_map.get(follow.follower_id)
                if user:
                    items.append(UserItem(
                        user_id=user.user_id,
                        user_name=user.user_name or "",
                        avatar=user.avatar or "",
                        bio=user.bio or "",
                        is_following=following_status.get(user.user_id, False),
                    ))

            has_more = (page * page_size) < total

            return ErrorCode.SUCCESS, "成功", FollowListData(
                items=items,
                total=total,
                has_more=has_more,
            )
        except Exception as e:
            logger.error(f"获取粉丝列表失败: {e}")
            return ErrorCode.GENERAL_ERROR, "系统错误", None

    # ==================== 反馈相关 ====================

    async def submit_feedback(
        self, user_id: str, post_id: Optional[str],
        feedback_type: int, reason: Optional[str], detail: Optional[str]
    ) -> Tuple[int, str]:
        """提交反馈"""
        try:
            feedback = UserFeedback(
                user_id=user_id,
                post_id=post_id,
                feedback_type=feedback_type,
                reason=reason,
                detail=detail,
                status=0,
            )
            self.db.add(feedback)
            await self.db.commit()

            logger.info(f"用户反馈已提交: user_id={user_id}, type={feedback_type}")
            return ErrorCode.SUCCESS, "成功"
        except Exception as e:
            logger.error(f"提交反馈失败: {e}")
            await self.db.rollback()
            return ErrorCode.FEEDBACK_FAILED, "反馈提交失败"

    # ==================== 私有方法 ====================

    async def _get_or_create_user_stats(self, user_id: str) -> UserStats:
        """获取或创建用户统计记录"""
        stmt = select(UserStats).where(UserStats.user_id == user_id)
        result = await self.db.execute(stmt)
        stats = result.scalar_one_or_none()

        if not stats:
            stats = UserStats(user_id=user_id)
            self.db.add(stats)
            await self.db.flush()

        return stats

    async def _check_follow_status(
        self, follower_id: str, following_id: str
    ) -> bool:
        """检查关注状态"""
        stmt = select(UserFollow).where(
            UserFollow.follower_id == follower_id,
            UserFollow.following_id == following_id,
            UserFollow.status == 1
        )
        result = await self.db.execute(stmt)
        follow = result.scalar_one_or_none()
        return follow is not None

    async def _batch_check_actions(
        self, user_id: str, target_type: str, target_ids: List[str]
    ) -> Dict[str, Dict[int, bool]]:
        """批量检查用户行为状态（点赞/收藏）"""
        result_map: Dict[str, Dict[int, bool]] = {}

        if not target_ids:
            return result_map

        stmt = select(UserAction).where(
            UserAction.user_id == user_id,
            UserAction.target_type == target_type,
            UserAction.target_id.in_(target_ids),
            UserAction.status == 1
        )
        result = await self.db.execute(stmt)
        actions = result.scalars().all()

        for action in actions:
            if action.target_id not in result_map:
                result_map[action.target_id] = {}
            result_map[action.target_id][action.action_type] = True

        return result_map

    def _format_timestamp(self, ts: int) -> str:
        """格式化时间戳为 ISO8601 格式"""
        if not ts:
            return ""
        dt = datetime.fromtimestamp(ts / 1000)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    def _format_display_time(self, ts: int) -> str:
        """格式化时间戳为展示格式"""
        if not ts:
            return ""
        dt = datetime.fromtimestamp(ts / 1000)
        return dt.strftime("%d %b %Y")
