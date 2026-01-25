"""聊天相关路由 - Joiiee API"""

from fastapi import APIRouter

from app.schemas.common import BaseResponse, Video, Author
from app.schemas.chat import (
    CreateSessionRequest,
    SessionData,
    SessionListRequest,
    SessionListData,
    SessionItem,
    UpdateSessionRequest,
    DeleteSessionRequest,
    SendMessageRequest,
    MessageResponseData,
    MessageItem,
    MessageListRequest,
    MessageListData,
    StopWordRequest,
    Attachment,
    Card,
    Equipment,
    Component,
    MediaReference,
    Thinking,
    ThinkingStep,
    SuggestedPrompt,
)

router = APIRouter(prefix="/chat", tags=["chat"])


# ========================= Mock 数据 =========================


def get_mock_thinking() -> Thinking:
    """生成 mock 思考过程"""
    return Thinking(
        thinking_id="think_001",
        message_id="msg_004",
        summary="Analyzed your needs and matched products",
        steps=[
            ThinkingStep(
                step_id="step_001",
                step_order=1,
                title="Analyzing requirements",
                content="Identified your skill level and preference for control",
                step_type=0,
                duration_ms=120,
                status=3,
                video=None,
                img_urls=[],
            ),
            ThinkingStep(
                step_id="step_002",
                step_order=2,
                title="Searching products",
                content="Filtered 12 rackets from 856 products for intermediate players",
                step_type=1,
                duration_ms=350,
                status=3,
                video=None,
                img_urls=[],
            ),
            ThinkingStep(
                step_id="step_003",
                step_order=3,
                title="Generating recommendations",
                content="Selected top 3 based on reviews and value",
                step_type=2,
                duration_ms=180,
                status=3,
                video=None,
                img_urls=[],
            ),
        ],
        total_duration_ms=650,
        is_expanded=False,
    )


def get_mock_suggested_prompts() -> list[SuggestedPrompt]:
    """生成 mock 推荐提示词"""
    return [
        SuggestedPrompt(id="sp_001", text="Compare with others", prompt_type=2, icon="compare"),
        SuggestedPrompt(id="sp_002", text="Show user reviews", prompt_type=2, icon="review"),
        SuggestedPrompt(id="sp_003", text="Any cheaper options?", prompt_type=1, icon="price"),
        SuggestedPrompt(id="sp_004", text="Recommend shoes too", prompt_type=3, icon="shoe"),
    ]


# ========================= 路由 =========================


@router.post("/create_session", response_model=BaseResponse[SessionData])
async def create_session(request: CreateSessionRequest):
    """
    创建新的AI对话会话

    支持不同类型的会话场景
    """
    data = SessionData(
        user_id="user_001",
        session_id="session_001",
        title=request.title,
        create_time="2026-01-21T10:30:00Z",
    )
    return BaseResponse(code=0, message="正确", data=data)


@router.post("/session_list", response_model=BaseResponse[SessionListData])
async def get_session_list(request: SessionListRequest):
    """
    获取用户的会话列表
    """
    items = [
        SessionItem(
            session_id="session_001",
            session_type=1,
            title="Equipment Chat",
            message_count=15,
            is_pinned=False,
            last_message_at="2026-01-21T10:30:00Z",
            last_message_preview="I can buy myself flower, write my name in the sand.",
            create_time="2026-01-20T08:00:00Z",
        ),
        SessionItem(
            session_id="session_002",
            session_type=3,
            title="Video Analysis",
            message_count=8,
            is_pinned=True,
            last_message_at="2026-01-21T09:00:00Z",
            last_message_preview="Your backhand stroke mostly come from...",
            create_time="2026-01-19T14:00:00Z",
        ),
    ]

    data = SessionListData(
        items=items,
        user_id="user_001",
        total=10,
        page=request.page,
        page_size=request.page_size,
        has_more=False,
    )
    return BaseResponse(code=0, message="正确", data=data)


@router.post("/update_session", response_model=BaseResponse)
async def update_session(request: UpdateSessionRequest):
    """
    更新会话信息

    如标题、置顶状态等
    """
    return BaseResponse(code=0, message="正确", data=None)


@router.post("/delete_session", response_model=BaseResponse)
async def delete_session(request: DeleteSessionRequest):
    """
    删除对话会话
    """
    return BaseResponse(code=0, message="正确", data=None)


@router.post("/send_message", response_model=BaseResponse[MessageResponseData])
async def send_message(request: SendMessageRequest):
    """
    发送消息并获取AI回复

    支持文本、图片、语音等多种消息类型
    """
    # 用户消息
    user_message = MessageItem(
        message_id="msg_001",
        session_id=request.session_id or "session_001",
        role=1,
        content=request.content,
        message_type=request.message_type,
        message_style=0,
        attachments=request.attachments,
        cards=[],
        generation_status=3,
        create_time="2026-01-21T10:30:00Z",
        display_time="2026-01-21T10:30:00Z",
        media_reference=[],
        summary="",
        component=None,
        thinking=None,
        suggested_prompts=[],
    )

    # AI 回复消息
    ai_message = MessageItem(
        message_id="msg_002",
        session_id=request.session_id or "session_001",
        role=2,
        content="I can take myself dancing, and I can hold my own hand.",
        message_type=3,
        message_style=0,
        attachments=[],
        cards=[],
        generation_status=3,
        create_time="2026-01-21T10:30:01Z",
        display_time="2026-01-21T10:30:01Z",
        media_reference=[],
        summary="",
        component=None,
        thinking=get_mock_thinking(),
        suggested_prompts=get_mock_suggested_prompts(),
    )

    data = MessageResponseData(
        user_message=user_message,
        ai_message=ai_message,
        session_updated=False,
    )
    return BaseResponse(code=0, message="正确", data=data)


@router.post("/message_list", response_model=BaseResponse[MessageListData])
async def get_message_list(request: MessageListRequest):
    """
    获取会话的消息列表

    支持向前加载更多历史消息
    """
    items = [
        MessageItem(
            message_id="msg_001",
            session_id=request.session_id,
            role=1,
            content="I can buy myself flower, write my name in the sand.",
            message_type=3,
            message_style=0,
            attachments=[],
            cards=[],
            generation_status=3,
            create_time="2026-01-21T10:30:00Z",
            display_time="2026-01-21T10:30:00Z",
            media_reference=[],
            summary="",
            component=None,
            thinking=None,
            suggested_prompts=[],
        ),
        MessageItem(
            message_id="msg_002",
            session_id=request.session_id,
            role=2,
            content="I can take myself dancing, and I can hold my own hand.",
            message_type=3,
            message_style=0,
            attachments=[],
            cards=[],
            generation_status=3,
            create_time="2026-01-21T10:30:01Z",
            display_time="2026-01-21T10:30:01Z",
            media_reference=[],
            summary="",
            component=None,
            thinking=get_mock_thinking(),
            suggested_prompts=get_mock_suggested_prompts(),
        ),
    ]

    data = MessageListData(items=items, has_more=False)
    return BaseResponse(code=0, message="正确", data=data)


@router.post("/stop_word", response_model=BaseResponse)
async def stop_word(request: StopWordRequest):
    """
    停止AI消息生成
    """
    return BaseResponse(code=0, message="正确", data=None)
