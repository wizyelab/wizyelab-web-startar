"""Profile相关路由"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.connection import get_async_db
from app.middleware.request_context import get_user_id
from app.schemas.common import BaseResponse
from app.schemas.profile import (
    ProfileInfoRequest,
    ProfileData,
    GuideData,
    GuideListRequest,
    ProfileUpdateRequest,
    ProfilePostsRequest,
    ProfilePostsData,
    CreatePostRequest,
    CreatePostData,
    DeletePostRequest,
    FollowRequest,
    FollowData,
    FollowersRequest,
    FollowListData,
    FeedbackRequest,
)
from app.services.profile_service import ProfileService

router = APIRouter(prefix="/profile", tags=["profile"])


# ========================= 路由 =========================


@router.post("/info", response_model=BaseResponse[ProfileData])
async def get_profile_info(
    request: ProfileInfoRequest,
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取用户的详细资料信息

    包括基本信息、统计数据、是否关注等
    """
    current_user_id = get_user_id()
    service = ProfileService(db)
    code, message, data = await service.get_profile(request.user_id, current_user_id)
    return BaseResponse(code=code, message=message, data=data)


@router.post("/collect/guide_list", response_model=BaseResponse[GuideData])
async def get_guide_list(
    request: GuideListRequest,
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取Profile收集的引导问题列表

    用于新用户注册后的引导流程
    tag_id=0 返回全部，否则按标签过滤
    """
    service = ProfileService(db)
    code, message, data = await service.get_guide_list(tag_id=request.tag_id)
    return BaseResponse(code=code, message=message, data=data)


@router.post("/update", response_model=BaseResponse)
async def update_profile(
    request: ProfileUpdateRequest,
    db: AsyncSession = Depends(get_async_db),
):
    """
    更新个人profile页
    """
    user_id = get_user_id()
    service = ProfileService(db)

    data = request.model_dump(exclude_none=True)

    code, message = await service.update_profile(user_id, data)
    return BaseResponse(code=code, message=message, data=None)


@router.post("/posts", response_model=BaseResponse[ProfilePostsData])
async def get_user_posts(
    request: ProfilePostsRequest,
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取用户发布的帖子列表

    用于Profile页展示
    """
    current_user_id = get_user_id()
    service = ProfileService(db)
    code, message, data = await service.get_user_posts(
        request.user_id, current_user_id, request.page, request.page_size
    )
    return BaseResponse(code=code, message=message, data=data)


@router.post("/post/create", response_model=BaseResponse[CreatePostData])
async def create_post(
    request: CreatePostRequest,
    db: AsyncSession = Depends(get_async_db),
):
    """
    发布新帖子

    支持图片、视频、纯文本类型
    """
    user_id = get_user_id()
    service = ProfileService(db)
    code, message, data = await service.create_post(
        user_id=user_id,
        post_type=request.post_type,
        title=request.title,
        description=request.description,
        content=request.content,
        images=[img.model_dump() for img in request.images] if request.images else [],
        video=request.video.model_dump() if request.video else None,
        tags=request.tags,
    )
    return BaseResponse(code=code, message=message, data=data)


@router.post("/post/delete", response_model=BaseResponse)
async def delete_post(
    request: DeletePostRequest,
    db: AsyncSession = Depends(get_async_db),
):
    """
    删除自己发布的帖子
    """
    user_id = get_user_id()
    service = ProfileService(db)
    code, message = await service.delete_post(user_id, request.post_id)
    return BaseResponse(code=code, message=message, data=None)


@router.post("/follow", response_model=BaseResponse[FollowData])
async def follow_user(
    request: FollowRequest,
    db: AsyncSession = Depends(get_async_db),
):
    """
    关注和取关目标用户
    """
    user_id = get_user_id()
    service = ProfileService(db)
    code, message, data = await service.follow_user(
        user_id, request.target_user_id, request.is_follow
    )
    return BaseResponse(code=code, message=message, data=data)


@router.post("/followers", response_model=BaseResponse[FollowListData])
async def get_followers(
    request: FollowersRequest,
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取用户的粉丝列表
    """
    current_user_id = get_user_id()
    service = ProfileService(db)
    code, message, data = await service.get_followers(
        request.user_id, current_user_id, request.page, request.page_size
    )
    return BaseResponse(code=code, message=message, data=data)


@router.post("/feedback", response_model=BaseResponse)
async def submit_feedback(
    request: FeedbackRequest,
    db: AsyncSession = Depends(get_async_db),
):
    """
    提交用户反馈

    包括不喜欢、举报等
    """
    user_id = get_user_id()
    service = ProfileService(db)
    code, message = await service.submit_feedback(
        user_id=user_id,
        post_id=request.post_id,
        feedback_type=request.feedback_type,
        reason=request.reason,
        detail=request.detail,
    )
    return BaseResponse(code=code, message=message, data=None)
