"""详情页相关路由 - Joiiee API"""

from fastapi import APIRouter

from app.schemas.common import BaseResponse, Video, Author
from app.schemas.detail import (
    DetailInfoRequest,
    DetailData,
    DetailPost,
    CommentListRequest,
    CommentListData,
    Comment,
    CreateCommentRequest,
    CreateCommentData,
    DeleteCommentRequest,
    GetCommentByLevelRequest,
    ReplyListData,
)

router = APIRouter(prefix="/detail", tags=["detail"])


# ========================= Mock 数据 =========================


def get_mock_detail_data(post_id: str) -> DetailData:
    """获取 mock 详情数据"""
    post = DetailPost(
        id=post_id,
        post_type=1,
        title="",
        description="I'm so excited. Voulez-vous coucher avec moi, ce soir. I love Hot dog and Oyster, and I think my champaign is from England, should I call it English Sparkling instead?",
        content="I'm so excited. Voulez-vous coucher avec moi, ce soir. I love Hot dog and Oyster, and I think my champaign is from England, should I call it English Sparkling instead?",
        img_urls=[],
        video=Video(
            id="video_001",
            height=1920,
            width=1080,
            duration=60,
            cover_url="https://example.com/cover_001.png",
            main_url="https://example.com/videos/post_001.mp4",
            back_urls=[],
        ),
        author=Author(
            user_id="user_louis",
            user_name="Louis",
            avatar="https://example.com/avatar/louis.png",
            is_followed=False,
        ),
        like_count=161,
        comment_count=11,
        share_count=2,
        is_liked=False,
        is_collected=False,
        is_followed=False,
        create_time="2026-01-09T10:30:00Z",
        update_time="2026-01-09T10:30:00Z",
        display_time="09 Jan 2026",
    )

    related_posts = [
        DetailPost(
            id="post_002",
            post_type=1,
            title="Morning practice",
            description="Great session today",
            content="",
            img_urls=[],
            video=Video(
                id="video_002",
                height=1920,
                width=1080,
                duration=45,
                cover_url="https://example.com/cover_002.png",
                main_url="https://example.com/videos/post_002.mp4",
                back_urls=[],
            ),
            author=Author(
                user_id="user_002",
                user_name="Emma",
                avatar="https://example.com/avatar/emma.png",
                is_followed=False,
            ),
            like_count=89,
            comment_count=12,
            share_count=3,
            is_liked=False,
            is_collected=False,
            is_followed=False,
            create_time="2026-01-20T08:00:00Z",
            update_time="2026-01-20T08:00:00Z",
            display_time="20 Jan 2026",
        )
    ]

    return DetailData(post=post, related_posts=related_posts)


def get_mock_comment_list_data(
    post_id: str, page: int = 1, page_size: int = 20
) -> CommentListData:
    """获取 mock 评论列表数据"""
    comments = [
        Comment(
            comment_id="comment_001",
            post_id=post_id,
            user=Author(
                user_id="user_sean",
                user_name="Sean Clark",
                avatar="https://example.com/avatar/sean.png",
                is_followed=False,
            ),
            text="I have no clue what this is...",
            level=0,
            like_count=12,
            reply_count=1,
            is_liked=False,
            parent_id="",
            reply_to_user=None,
            replies=[
                Comment(
                    comment_id="comment_002",
                    post_id=post_id,
                    user=Author(
                        user_id="user_david",
                        user_name="Daivd Cho",
                        avatar="https://example.com/avatar/david.png",
                        is_followed=False,
                    ),
                    text="Oi agreed",
                    level=1,
                    like_count=3,
                    reply_count=0,
                    is_liked=False,
                    parent_id="comment_001",
                    reply_to_user=Author(
                        user_id="user_sean",
                        user_name="Sean Clark",
                        avatar="https://example.com/avatar/sean.png",
                        is_followed=False,
                    ),
                    replies=[],
                    create_time="2026-01-21T10:27:00Z",
                    display_time="3 minutes ago",
                    update_time="2026-01-21T10:27:00Z",
                )
            ],
            create_time="2026-01-21T10:00:00Z",
            display_time="30 minutes ago",
            update_time="2026-01-21T10:00:00Z",
        ),
        Comment(
            comment_id="comment_003",
            post_id=post_id,
            user=Author(
                user_id="user_alessandro",
                user_name="Alessandro Massimo",
                avatar="https://example.com/avatar/alessandro.png",
                is_followed=False,
            ),
            text="Hell yes",
            level=0,
            like_count=8,
            reply_count=0,
            is_liked=False,
            parent_id="",
            reply_to_user=None,
            replies=[],
            create_time="2026-01-19T10:30:00Z",
            display_time="2 days ago",
            update_time="2026-01-19T10:30:00Z",
        ),
        Comment(
            comment_id="comment_004",
            post_id=post_id,
            user=Author(
                user_id="user_adrian",
                user_name="Adrian Lee",
                avatar="https://example.com/avatar/adrian.png",
                is_followed=False,
            ),
            text="?What?",
            level=0,
            like_count=2,
            reply_count=0,
            is_liked=False,
            parent_id="",
            reply_to_user=None,
            replies=[],
            create_time="2026-01-21T07:30:00Z",
            display_time="3 hours ago",
            update_time="2026-01-21T07:30:00Z",
        ),
        Comment(
            comment_id="comment_005",
            post_id=post_id,
            user=Author(
                user_id="user_aidan",
                user_name="Aidan Parry",
                avatar="https://example.com/avatar/aidan.png",
                is_followed=False,
            ),
            text="Oh...Absolutely relatable, I remember when I was in Paris, I ran into this beautiful bakery, I wen in side, and guess what? They don't sell any bakery, Alcohol only!",
            level=0,
            like_count=25,
            reply_count=0,
            is_liked=False,
            parent_id="",
            reply_to_user=None,
            replies=[],
            create_time="2026-01-21T10:00:00Z",
            display_time="30 minutes ago",
            update_time="2026-01-21T10:00:00Z",
        ),
    ]

    return CommentListData(
        comments=comments,
        total=11,
        page=page,
        page_size=page_size,
        has_more=False,
    )


# ========================= 路由 =========================


@router.post("/info", response_model=BaseResponse[DetailData])
async def get_detail_info(request: DetailInfoRequest):
    """
    获取帖子/内容的详情信息

    包括内容、作者信息、互动数据等
    """
    data = get_mock_detail_data(request.post_id)
    return BaseResponse(code=0, message="正确", data=data)


@router.post("/comment_list", response_model=BaseResponse[CommentListData])
async def get_comment_list(request: CommentListRequest):
    """
    获取帖子的评论列表

    支持分页和嵌套回复
    """
    data = get_mock_comment_list_data(
        request.post_id, request.page, request.page_size
    )
    return BaseResponse(code=0, message="正确", data=data)


@router.post("/create_comment", response_model=BaseResponse[CreateCommentData])
async def create_comment(request: CreateCommentRequest):
    """
    对帖子发表评论或回复他人评论
    """
    new_comment = Comment(
        comment_id="comment_new_001",
        post_id=request.post_id,
        user=Author(
            user_id="current_user",
            user_name="CurrentUser",
            avatar="https://example.com/avatar/current.png",
            is_followed=False,
        ),
        text=request.text,
        level=request.level,
        like_count=0,
        reply_count=0,
        is_liked=False,
        parent_id=request.comment_id,
        reply_to_user=Author(
            user_id=request.reply_to_user_id,
            user_name="ReplyUser",
            avatar="https://example.com/avatar/reply.png",
            is_followed=False,
        )
        if request.reply_to_user_id
        else None,
        replies=[],
        create_time="2026-01-21T10:30:00Z",
        display_time="Just now",
        update_time="2026-01-21T10:30:00Z",
    )

    data = CreateCommentData(
        comment_id="comment_new_001",
        comment=new_comment,
    )
    return BaseResponse(code=0, message="正确", data=data)


@router.post("/delete_comment", response_model=BaseResponse)
async def delete_comment(request: DeleteCommentRequest):
    """
    删除自己发表的评论
    """
    return BaseResponse(code=0, message="正确", data=None)


@router.post("/get_comment_by_level", response_model=BaseResponse[ReplyListData])
async def get_comment_by_level(request: GetCommentByLevelRequest):
    """
    获取某条评论的回复列表

    用于"查看更多回复"场景
    """
    items = [
        Comment(
            comment_id="comment_002",
            post_id="post_001",
            user=Author(
                user_id="user_david",
                user_name="Daivd Cho",
                avatar="https://example.com/avatar/david.png",
                is_followed=False,
            ),
            text="Oi agreed",
            level=1,
            like_count=3,
            reply_count=0,
            is_liked=False,
            parent_id=request.comment_id,
            reply_to_user=Author(
                user_id="user_sean",
                user_name="Sean Clark",
                avatar="https://example.com/avatar/sean.png",
                is_followed=False,
            ),
            replies=[],
            create_time="2026-01-21T10:27:00Z",
            display_time="3 minutes ago",
            update_time="2026-01-21T10:27:00Z",
        )
    ]

    data = ReplyListData(
        items=items,
        total=1,
        has_more=False,
    )
    return BaseResponse(code=0, message="正确", data=data)
