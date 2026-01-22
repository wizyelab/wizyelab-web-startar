"""首页相关路由 - Joiiee API"""

from fastapi import APIRouter

from app.schemas.common import BaseResponse, Video, Author
from app.schemas.home import (
    TagContentListRequest,
    TagContentListData,
    Tag,
    Content,
    Item,
    FeedRequest,
    FeedData,
    Post,
    UserActionRequest,
    ActionData,
    GenerateShareLinkRequest,
    ShareData,
)

router = APIRouter(prefix="/home", tags=["home"])


# ========================= Mock 数据 =========================


def get_mock_tag_content_list_data(tag_id: int = 0) -> TagContentListData:
    """获取 mock 标签内容列表数据"""
    # 装备推荐内容
    equipment_content = Content(
        content_id="content_001",
        logo="https://example.com/ai_logo.png",
        title="These rackets fit where you are right now.",
        sub_title="",
        content_type=1,
        video=None,
        cover_image="",
        action_type=1,
        action_url="/equipment/list",
        button_desc="",
        item_list=[
            Item(
                item_id="item_001",
                logo="https://example.com/decathlon_pr500.png",
                title="Decathlon PR 500",
                sub_title="$50 - $80",
                video=None,
                desc="Minimal vibration feedback...",
                rating="4.7",
            ),
            Item(
                item_id="item_002",
                logo="https://example.com/wilson_optix.png",
                title="Wilson Optix V1",
                sub_title="$50 - $80",
                video=None,
                desc="The sweet spot feels big or...",
                rating="4.5",
            ),
        ],
    )

    # AI分析内容
    ai_analysis_content = Content(
        content_id="content_002",
        logo="https://example.com/ai_analysis_logo.png",
        title="Upload a 10s video, and get your feedback.",
        sub_title="Real plays. Real moments.",
        content_type=2,
        video=Video(
            id="video_001",
            height=1080,
            width=1920,
            duration=15,
            cover_url="https://example.com/video_cover.png",
            main_url="https://example.com/videos/ai_demo.mp4",
            back_urls=["https://cdn1.example.com/videos/ai_demo.mp4"],
        ),
        cover_image="https://example.com/ai_analysis_cover.png",
        action_type=3,
        action_url="/upload/video",
        button_desc="Upload New Video",
        item_list=[],
    )

    # 高光时刻
    highlight_content = Content(
        content_id="content_003",
        logo="https://example.com/highlight_logo.png",
        title="This week's highlights",
        sub_title="",
        content_type=3,
        video=Video(
            id="video_002",
            height=1080,
            width=1920,
            duration=60,
            cover_url="https://example.com/highlight_cover.png",
            main_url="https://example.com/videos/highlight.mp4",
            back_urls=[],
        ),
        cover_image="https://example.com/highlight_cover.png",
        action_type=1,
        action_url="/highlight/detail/content_003",
        button_desc="Post",
        item_list=[],
    )

    # 推荐媒体
    media_content = Content(
        content_id="content_004",
        logo="https://example.com/media_logo.png",
        title="Trending on YouTube",
        sub_title="",
        content_type=4,
        video=Video(
            id="video_003",
            height=720,
            width=1280,
            duration=120,
            cover_url="https://example.com/youtube_cover.png",
            main_url="https://example.com/videos/trending.mp4",
            back_urls=[],
        ),
        cover_image="https://example.com/trending_cover.png",
        action_type=2,
        action_url="https://youtube.com/watch?v=xxx",
        button_desc="",
        item_list=[],
    )

    tag_list = [
        Tag(
            tag_id=1,
            tag_name="Padel",
            tag_icon="https://example.com/icons/padel.png",
            is_selected=tag_id == 0 or tag_id == 1,
            content_list=[
                equipment_content,
                ai_analysis_content,
                highlight_content,
                media_content,
            ]
            if tag_id == 0 or tag_id == 1
            else [],
        ),
        Tag(
            tag_id=2,
            tag_name="Pickleball",
            tag_icon="https://example.com/icons/pickleball.png",
            is_selected=tag_id == 2,
            content_list=[equipment_content, ai_analysis_content] if tag_id == 2 else [],
        ),
        Tag(
            tag_id=3,
            tag_name="Tennis",
            tag_icon="https://example.com/icons/tennis.png",
            is_selected=tag_id == 3,
            content_list=[highlight_content, media_content] if tag_id == 3 else [],
        ),
    ]

    return TagContentListData(tag_list=tag_list, first_login=False)


def get_mock_feed_data(page: int = 1, page_size: int = 20) -> FeedData:
    """获取 mock Feed 数据"""
    items = [
        Post(
            id="feed_001",
            post_type=1,
            title="I'm so excited",
            description="Great match today!",
            content="Had an amazing paddle session this morning...",
            thumbnail_url="https://example.com/thumb_001.png",
            img_urls=["https://example.com/videos/feed_001.mp4"],
            video=Video(
                id="video_feed_001",
                height=1920,
                width=1080,
                duration=30,
                cover_url="https://example.com/thumb_001.png",
                main_url="https://example.com/videos/feed_001.mp4",
                back_urls=[],
            ),
            author=Author(
                user_id="user_001",
                user_name="JohnDoe",
                avatar="https://example.com/avatar_001.png",
                is_followed=False,
            ),
            like_count=128,
            comment_count=32,
            share_count=8,
            is_liked=False,
            is_collected=False,
            create_time="2026-01-20T10:30:00Z",
            update_time="2026-01-20T10:30:00Z",
            display_time="3 days ago",
        ),
        Post(
            id="feed_002",
            post_type=2,
            title="New racket arrived!",
            description="Finally got my Wilson Optix V1",
            content="So happy with this purchase...",
            thumbnail_url="https://example.com/thumb_002.png",
            img_urls=[
                "https://example.com/images/feed_002_1.png",
                "https://example.com/images/feed_002_2.png",
            ],
            video=None,
            author=Author(
                user_id="user_002",
                user_name="JaneSmith",
                avatar="https://example.com/avatar_002.png",
                is_followed=True,
            ),
            like_count=256,
            comment_count=48,
            share_count=12,
            is_liked=True,
            is_collected=False,
            create_time="2026-01-19T15:20:00Z",
            update_time="2026-01-19T15:20:00Z",
            display_time="3 days ago",
        ),
        Post(
            id="feed_003",
            post_type=3,
            title="Tips for beginners",
            description="",
            content="Here are some tips I wish I knew when I started playing paddle...",
            thumbnail_url="",
            img_urls=[],
            video=None,
            author=Author(
                user_id="user_003",
                user_name="PaddlePro",
                avatar="https://example.com/avatar_003.png",
                is_followed=False,
            ),
            like_count=89,
            comment_count=15,
            share_count=5,
            is_liked=False,
            is_collected=True,
            create_time="2026-01-18T09:00:00Z",
            update_time="2026-01-18T09:00:00Z",
            display_time="3 days ago",
        ),
    ]

    return FeedData(
        items=items,
        total=100,
        page=page,
        page_size=page_size,
        has_more=page < 5,
    )


# ========================= 路由 =========================


@router.post("/tag_content_list", response_model=BaseResponse[TagContentListData])
async def get_tag_content_list(request: TagContentListRequest):
    """
    获取首页标签及对应的内容列表

    支持装备推荐、AI分析、高光时刻、推荐媒体等多种内容类型
    """
    data = get_mock_tag_content_list_data(request.tag_id)
    return BaseResponse(code=0, message="正确", data=data)


@router.post("/feed", response_model=BaseResponse[FeedData])
async def get_feed(request: FeedRequest):
    """
    获取广场的个性化Feed流

    包含用户发布的图片、视频、文本内容
    """
    data = get_mock_feed_data(request.page, request.page_size)
    return BaseResponse(code=0, message="正确", data=data)


@router.post("/user/action", response_model=BaseResponse[ActionData])
async def user_action(request: UserActionRequest):
    """
    用户点赞、收藏、分享等行为

    action_type: 0-view, 1-like, 2-unlike, 3-collect, 4-uncollect, 5-share
    """
    # Mock 响应
    is_active = request.action_type in [1, 3, 5]  # like, collect, share
    count = 129 if is_active else 128

    data = ActionData(
        action_type=request.action_type,
        is_active=is_active,
        count=count,
    )
    return BaseResponse(code=0, message="正确", data=data)


@router.post("/share/generate_link", response_model=BaseResponse[ShareData])
async def generate_share_link(request: GenerateShareLinkRequest):
    """
    生成内容的H5分享链接或DeepLink
    """
    data = ShareData(
        share_url=f"https://joiiee.com/share/{request.post_id}?t=abc123",
        share_text="I'm so excited - Great match today!",
        share_image="https://example.com/thumb_001.png",
    )
    return BaseResponse(code=0, message="正确", data=data)
