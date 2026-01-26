"""账户相关路由"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.logging import setup_logger
from app.core.deps import get_current_user_id, get_current_session_id
from app.schemas.common import BaseResponse
from app.schemas.account import (
    LoginRequest,
    LoginResponse,
    SendVerifyCodeRequest,
    SendVerifyCodeResponse,
    LogoutRequest,
    LogoutResponse,
    UserInfo,
)
from app.services.auth_service import auth_service
from app.middleware.request_context import (
    set_session_id_for_response,
    get_request_context,
)

logger = setup_logger(__name__)

router = APIRouter(prefix="/account", tags=["account"])


@router.post("/login", response_model=BaseResponse[LoginResponse])
async def login(request: LoginRequest):
    """
    用户登录

    支持的登录方式:
    - email: 邮箱验证码登录
    - google: Google 第三方登录
    - apple: Apple 第三方登录
    """
    try:
        # TODO: 根据 login_type 实现具体的登录逻辑
        # 1. email 登录：验证邮箱和验证码
        # 2. google/apple 登录：验证 Firebase ID Token

        # 这里是示例实现，实际需要根据业务逻辑完善
        if request.login_type == "email":
            if not request.email or not request.verify_code:
                return BaseResponse(
                    code=400,
                    message="邮箱和验证码不能为空",
                    data=None
                )
            # TODO: 验证邮箱验证码
            # TODO: 查找或创建用户

        elif request.login_type in ["google", "apple"]:
            if not request.id_token:
                return BaseResponse(
                    code=400,
                    message="ID Token 不能为空",
                    data=None
                )
            # TODO: 验证 Firebase ID Token
            # TODO: 查找或创建用户

        else:
            return BaseResponse(
                code=400,
                message=f"不支持的登录类型: {request.login_type}",
                data=None
            )

        # 示例：假设用户已验证通过
        # 实际应该从数据库获取或创建用户
        from app.core.snowflake import generate_id_str
        user_id = generate_id_str()  # 实际应该是从数据库获取的 user_id
        is_new_user = True  # 实际应该根据查询结果判断

        # 创建 session
        session_id = auth_service.generate_session_id()
        device_id = request.device_id or "unknown"

        success = await auth_service.create_session(
            session_id=session_id,
            user_id=user_id,
            device_id=device_id,
            extra_data={
                "login_type": request.login_type,
                "device_type": request.device_type,
            }
        )

        if not success:
            return BaseResponse(
                code=500,
                message="创建会话失败",
                data=None
            )

        # 设置响应中的 session_id
        set_session_id_for_response(session_id)

        logger.info(f"用户登录成功: user_id={user_id}, login_type={request.login_type}")

        return BaseResponse(
            code=0,
            message="登录成功",
            data=LoginResponse(
                user_id=user_id,
                session_id=session_id,
                is_new_user=is_new_user
            )
        )

    except Exception as e:
        logger.error(f"登录失败: {e}")
        return BaseResponse(
            code=500,
            message="登录失败，请稍后重试",
            data=None
        )


@router.post("/send_verify_code", response_model=BaseResponse[SendVerifyCodeResponse])
async def send_verify_code(request: SendVerifyCodeRequest):
    """
    发送邮箱验证码

    用于邮箱登录前发送验证码
    """
    try:
        # TODO: 实现发送验证码逻辑
        # 1. 生成验证码
        # 2. 存储到 Redis（设置过期时间）
        # 3. 发送邮件

        logger.info(f"发送验证码: email={request.email}")

        return BaseResponse(
            code=0,
            message="验证码已发送",
            data=SendVerifyCodeResponse(
                success=True,
                message="验证码已发送到您的邮箱"
            )
        )

    except Exception as e:
        logger.error(f"发送验证码失败: {e}")
        return BaseResponse(
            code=500,
            message="发送验证码失败",
            data=None
        )


@router.post("/logout", response_model=BaseResponse[LogoutResponse])
async def logout(
    request: LogoutRequest,
    session_id: str = Depends(get_current_session_id),
    user_id: str = Depends(get_current_user_id)
):
    """
    用户登出

    可选择登出当前设备或所有设备
    """
    try:
        if request.all_devices:
            # 登出所有设备
            await auth_service.delete_user_sessions(user_id)
            logger.info(f"用户登出所有设备: user_id={user_id}")
        else:
            # 登出当前设备
            await auth_service.delete_session(session_id)
            logger.info(f"用户登出: user_id={user_id}, session_id={session_id}")

        return BaseResponse(
            code=0,
            message="登出成功",
            data=LogoutResponse(success=True)
        )

    except Exception as e:
        logger.error(f"登出失败: {e}")
        return BaseResponse(
            code=500,
            message="登出失败",
            data=None
        )


@router.get("/me", response_model=BaseResponse[UserInfo])
async def get_current_user(user_id: str = Depends(get_current_user_id)):
    """
    获取当前登录用户信息
    """
    try:
        # TODO: 从数据库获取用户信息
        # 这里是示例实现

        return BaseResponse(
            code=0,
            message="获取成功",
            data=UserInfo(
                user_id=user_id,
                email="",
                username="",
                avatar="",
                bio="",
                gender="",
                location="",
                login_provider=""
            )
        )

    except Exception as e:
        logger.error(f"获取用户信息失败: {e}")
        return BaseResponse(
            code=500,
            message="获取用户信息失败",
            data=None
        )
