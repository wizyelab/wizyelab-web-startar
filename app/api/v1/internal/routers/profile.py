"""Profile相关路由 - Joiiee API"""

from fastapi import APIRouter

from app.schemas.common import BaseResponse, Video, Author
from app.schemas.profile import (
    ProfileInfoRequest,
    ProfileData,
    GuideData,
    GuideItem,
    OptionItem,
    ProfileUpdateRequest,
    ProfilePostsRequest,
    ProfilePostsData,
    ProfilePost,
    CreatePostRequest,
    CreatePostData,
    DeletePostRequest,
    FollowRequest,
    FollowData,
    FollowersRequest,
    FollowListData,
    UserItem,
    FeedbackRequest,
)

router = APIRouter(prefix="/profile", tags=["profile"])


# ========================= Mock 数据 =========================


def get_mock_profile_data(user_id: str) -> ProfileData:
    """获取 mock Profile 数据"""
    return ProfileData(
        user_id=user_id,
        user_name="Joan",
        avatar="https://example.com/avatar/joan.png",
        bio="Paddle enthusiast | 3.5 level player",
        gender=2,
        location="San Francisco, CA",
        interest_tags=[1, 2],
        follower_count=128,
        following_count=56,
        post_count=24,
        is_followed=False,
        is_self=True,
    )


def get_mock_guide_data() -> GuideData:
    """获取 mock 引导列表数据"""
    items = [
        GuideItem(
            id="interests",
            style=2,
            guide_words="What sports are you interested in?",
            profile_key="interest_tags",
            sort=1,
            options=[
                OptionItem(
                    content="Padel",
                    description="",
                    icon_url="https://example.com/icons/padel.png",
                ),
                OptionItem(
                    content="Tennis",
                    description="",
                    icon_url="https://example.com/icons/tennis.png",
                ),
                OptionItem(
                    content="Pickleball",
                    description="",
                    icon_url="https://example.com/icons/pickleball.png",
                ),
            ],
            is_required=True,
        ),
        GuideItem(
            id="skill_level",
            style=1,
            guide_words="What's your skill level?",
            profile_key="skill_level",
            sort=2,
            options=[
                OptionItem(
                    content="Beginner",
                    description="Just getting started",
                    icon_url="",
                ),
                OptionItem(
                    content="Intermediate",
                    description="Have some experience",
                    icon_url="",
                ),
                OptionItem(
                    content="Advanced",
                    description="Skilled player",
                    icon_url="",
                ),
                OptionItem(
                    content="Professional",
                    description="Pro level",
                    icon_url="",
                ),
            ],
            is_required=True,
        ),
        GuideItem(
            id="equipment",
            style=0,
            guide_words="Tell me about your equipment",
            profile_key="equipment_config",
            sort=3,
            options=[],
            is_required=False,
        ),
    ]

    return GuideData(items=items, total_steps=3)


def get_mock_posts_data(
    user_id: str, page: int = 1, page_size: int = 20
) -> ProfilePostsData:
    """获取 mock 用户帖子列表数据"""
    items = [
        ProfilePost(
            id="post_001",
            post_type=1,
            title="I'm so excited",
            description="Voulez-vous couch...",
            content="",
            thumbnail_url="https://example.com/thumb_001.png",
            img_urls=[],
            video=Video(
                id="video_001",
                height=1920,
                width=1080,
                duration=30,
                cover_url="https://example.com/thumb_001.png",
                main_url="https://example.com/videos/post_001.mp4",
                back_urls=[],
            ),
            author=Author(
                user_id=user_id,
                user_name="Joan",
                avatar="https://example.com/avatar/joan.png",
                is_followed=False,
            ),
            like_count=128,
            comment_count=32,
            share_count=8,
            is_liked=False,
            is_collected=False,
            create_time="2026-01-20T10:30:00Z",
            update_time="2026-01-20T10:30:00Z",
            display_time="20 Jan 2026",
        ),
        ProfilePost(
            id="post_002",
            post_type=2,
            title="I'm so excited",
            description="Voulez-vous couch...",
            content="",
            thumbnail_url="https://example.com/thumb_002.png",
            img_urls=["https://example.com/images/post_002.png"],
            video=None,
            author=Author(
                user_id=user_id,
                user_name="Joan",
                avatar="https://example.com/avatar/joan.png",
                is_followed=False,
            ),
            like_count=64,
            comment_count=16,
            share_count=4,
            is_liked=True,
            is_collected=False,
            create_time="2026-01-19T15:20:00Z",
            update_time="2026-01-19T15:20:00Z",
            display_time="19 Jan 2026",
        ),
    ]

    return ProfilePostsData(
        items=items,
        total=24,
        page=page,
        page_size=page_size,
        has_more=True,
    )


def get_mock_followers_data(
    user_id: str, page: int = 1, page_size: int = 20
) -> FollowListData:
    """获取 mock 粉丝列表数据"""
    items = [
        UserItem(
            user_id="user_001",
            user_name="Louis Hendrix",
            avatar="https://example.com/avatar_001.png",
            bio="Tennis lover",
            is_following=True,
        ),
        UserItem(
            user_id="user_002",
            user_name="Emma Wilson",
            avatar="https://example.com/avatar_002.png",
            bio="Paddle beginner",
            is_following=False,
        ),
    ]

    return FollowListData(
        items=items,
        total=128,
        has_more=True,
    )


# ========================= 路由 =========================


@router.post("/info", response_model=BaseResponse[ProfileData])
async def get_profile_info(request: ProfileInfoRequest):
    """
    获取用户的详细资料信息

    包括基本信息、统计数据、是否关注等
    """
    data = get_mock_profile_data(request.user_id)
    return BaseResponse(code=0, message="正确", data=data)


@router.post("/collect/guide_list", response_model=BaseResponse[GuideData])
async def get_guide_list():
    """
    获取Profile收集的引导问题列表

    用于新用户注册后的引导流程
    """
    data = get_mock_guide_data()
    return BaseResponse(code=0, message="正确", data=data)


@router.post("/update", response_model=BaseResponse)
async def update_profile(request: ProfileUpdateRequest):
    """
    更新个人profile页
    """
    return BaseResponse(code=0, message="正确", data=None)


@router.post("/posts", response_model=BaseResponse[ProfilePostsData])
async def get_user_posts(request: ProfilePostsRequest):
    """
    获取用户发布的帖子列表

    用于Profile页展示
    """
    data = get_mock_posts_data(request.user_id, request.page, request.page_size)
    return BaseResponse(code=0, message="正确", data=data)


@router.post("/post/create", response_model=BaseResponse[CreatePostData])
async def create_post(request: CreatePostRequest):
    """
    发布新帖子

    支持图片、视频、纯文本类型
    """
    data = CreatePostData(post_id="post_new_001")
    return BaseResponse(code=0, message="正确", data=data)


@router.post("/post/delete", response_model=BaseResponse)
async def delete_post(request: DeletePostRequest):
    """
    删除自己发布的帖子
    """
    return BaseResponse(code=0, message="正确", data=None)


@router.post("/follow", response_model=BaseResponse[FollowData])
async def follow_user(request: FollowRequest):
    """
    关注和取关目标用户
    """
    data = FollowData(
        is_followed=request.is_follow,
        follower_count=129 if request.is_follow else 128,
    )
    return BaseResponse(code=0, message="正确", data=data)


@router.post("/followers", response_model=BaseResponse[FollowListData])
async def get_followers(request: FollowersRequest):
    """
    获取用户的粉丝列表
    """
    data = get_mock_followers_data(request.user_id, request.page, request.page_size)
    return BaseResponse(code=0, message="正确", data=data)


@router.post("/feedback", response_model=BaseResponse)
async def submit_feedback(request: FeedbackRequest):
    """
    提交用户反馈

    包括不喜欢、举报等
    """
    return BaseResponse(code=0, message="正确", data=None)
