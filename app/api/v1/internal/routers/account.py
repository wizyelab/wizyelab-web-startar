"""账户相关路由"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.common import BaseResponse
from app.schemas.account import (
    LoginRequest,
    LoginData,
    SendVerifyCodeRequest,
    LogoutRequest,
    ErrorCode,
)
from app.services.account_service import AccountService
from app.infrastructure.database.connection import get_async_db
from app.core.logging import setup_logger

logger = setup_logger(__name__)

router = APIRouter(prefix="/account", tags=["account"])


# ========================= 路由 =========================


@router.post("/login", response_model=BaseResponse[LoginData])
async def login(request: LoginRequest, db: AsyncSession = Depends(get_async_db)):
    """
    用户登录

    支持两种登录方式：
    1. 第三方登录（Google/Apple）- 提供 id_token
    2. 邮箱验证码登录 - 提供 email + verify_code

    **注意**: 必须提供 id_token 或 (email + verify_code) 其中一种方式
    """
    device_id = request.device_info.device_id if request.device_info else ""

    account_service = AccountService(db)

    if request.id_token:
        # 第三方登录
        code, message, data = await account_service.verify_third_party_login(
            id_token=request.id_token,
            device_id=device_id,
        )
    elif request.email and request.verify_code:
        # 邮箱验证码登录
        code, message, data = await account_service.verify_email_login(
            email=request.email,
            verify_code=request.verify_code,
            device_id=device_id,
        )
    else:
        return BaseResponse(
            code=ErrorCode.INVALID_PARAMS,
            message="请提供 id_token（第三方登录）或 email + verify_code（邮箱登录）",
            data=None,
        )

    return BaseResponse(code=code, message=message, data=data)


@router.post("/send_verify_code", response_model=BaseResponse)
async def send_verify_code(
    request: SendVerifyCodeRequest, db: AsyncSession = Depends(get_async_db)
):
    """
    发送验证码

    发送6位数字验证码到指定邮箱，用于邮箱登录验证。

    **业务说明**:
    1. 验证码生成: 生成6位数字验证码
    2. 存储: 验证码存储到Redis，有效期10分钟
    3. 发送限制: 同一邮箱+设备10分钟内只能发送一次
    4. 邮件发送: 通过SMTP发送验证码邮件
    """
    device_id = request.device_info.device_id if request.device_info else ""

    account_service = AccountService(db)
    code, message = await account_service.send_verify_code(
        email=request.email,
        device_id=device_id,
    )

    return BaseResponse(code=code, message=message, data=None)


@router.post("/logout", response_model=BaseResponse)
async def logout(request: LogoutRequest, db: AsyncSession = Depends(get_async_db)):
    """
    用户登出

    使当前会话Token失效。

    **登出流程**:
    1. 获取用户信息: 根据user_id获取用户的Firebase UID
    2. 撤销Firebase Token: 调用Firebase Admin SDK撤销用户的Refresh Token
    3. 删除Redis会话: 删除Redis中存储的会话缓存
    4. 数据库会话失效: 将数据库中该设备的会话标记为无效
    5. 更新设备状态: 将该设备标记为非活跃状态
    """
    device_id = request.device_info.device_id if request.device_info else ""

    account_service = AccountService(db)
    code, message = await account_service.logout(
        user_id=request.user_id,
        device_id=device_id,
    )

    return BaseResponse(code=code, message=message, data=None)
