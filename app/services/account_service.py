"""
账户服务模块

处理用户登录、注册、验证等业务逻辑
"""

import time
from typing import Optional, Tuple

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import setup_logger
from app.core.config import settings
from app.models.user import User, UserDevice, UserSession, generate_uuid, generate_user_id, current_timestamp_ms
from app.services.firebase_service import firebase_service
from app.services.email_service import email_service
from app.services.auth_service import auth_service, SESSION_TTL
from app.middleware.request_context import set_session_id_for_response
from app.infrastructure.cache.redis_client import redis_client
from app.core.error_codes import ErrorCode
from app.schemas.account import LoginData, UserInfo

logger = setup_logger(__name__)


class AccountService:
    """账户服务类"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def verify_third_party_login(
        self, id_token: str, device_id: str
    ) -> Tuple[int, str, Optional[LoginData]]:
        """
        验证第三方登录（Google/Apple）

        流程：
        1. 验证 Firebase ID Token
        2. 查询或创建用户
        3. 更新设备信息
        4. 创建自定义 Token
        5. 创建会话
        6. 返回响应

        Args:
            id_token: Firebase ID Token
            device_id: 设备ID

        Returns:
            (错误码, 消息, 响应数据)
        """
        # 1. 验证 Firebase ID Token
        decoded_token, error_type = await firebase_service.verify_id_token(id_token)
        if not decoded_token:
            error_messages = {
                "invalid": "无效的登录凭证",
                "expired": "登录凭证已过期，请重新登录",
                "revoked": "登录会话已失效，请重新登录",
                "disabled": "账户已被禁用",
                "error": "登录验证失败",
            }
            return (
                ErrorCode.FIREBASE_TOKEN_INVALID,
                error_messages.get(error_type, "无效的登录凭证"),
                None,
            )

        firebase_uid = decoded_token.get("uid")
        email = decoded_token.get("email")
        name = decoded_token.get("name") or decoded_token.get("display_name")
        picture = decoded_token.get("picture")
        provider = decoded_token.get("firebase", {}).get("sign_in_provider", "unknown")

        logger.info(f"第三方登录验证成功: provider={provider}, email={email}")

        # 2. 查询或创建用户
        user = await self._get_or_create_user(
            firebase_uid=firebase_uid,
            email=email,
            user_name=name,
            avatar=picture,
            login_provider=provider,
        )

        if not user:
            return ErrorCode.GENERAL_ERROR, "创建用户失败", None

        # 3. 更新设备信息
        await self._update_device(user.user_id, device_id)

        # 4. 创建自定义 Token
        custom_token = await firebase_service.create_custom_token(
            user.user_id, additional_claims={"email": email, "provider": provider}
        )

        # 5. 创建会话
        await self._create_session(user.user_id, device_id, custom_token)

        # 6. 判断是否首次登录
        is_first_login = await self._is_first_login(user.user_id)

        # 7. 返回响应
        response_data = LoginData(
            custom_token=custom_token or "",
            user_info=UserInfo(
                user_id=user.user_id,
                user_name=user.user_name or "",
                avatar=user.avatar or "",
            ),
            is_first_login=is_first_login,
        )

        return ErrorCode.SUCCESS, "成功", response_data

    async def verify_email_login(
        self, email: str, verify_code: str, device_id: str
    ) -> Tuple[int, str, Optional[LoginData]]:
        """
        验证邮箱登录

        流程：
        1. 校验验证码
        2. 查询或创建 Firebase 用户
        3. 查询或创建本地用户
        4. 更新设备信息
        5. 创建自定义 Token
        6. 创建会话
        7. 返回响应

        Args:
            email: 邮箱地址
            verify_code: 验证码
            device_id: 设备ID

        Returns:
            (错误码, 消息, 响应数据)
        """
        # 1. 校验验证码
        stored_code = await self._get_verify_code(email, device_id)

        if not stored_code:
            return ErrorCode.VERIFY_CODE_EXPIRED, "验证码已过期，请重新获取", None

        if stored_code != verify_code:
            return ErrorCode.INVALID_VERIFY_CODE, "验证码错误", None

        # 2. 验证成功，删除验证码
        await self._delete_verify_code(email, device_id)

        # 3. 查询或创建 Firebase 用户
        firebase_user = await firebase_service.get_user_by_email(email)
        if not firebase_user:
            firebase_user = await firebase_service.create_user(email)
            if not firebase_user:
                return ErrorCode.GENERAL_ERROR, "创建用户失败", None

        # 4. 查询或创建本地用户
        user = await self._get_or_create_user(
            firebase_uid=firebase_user.uid,
            email=email,
            user_name=email.split("@")[0],
            login_provider="email",
        )

        if not user:
            return ErrorCode.GENERAL_ERROR, "创建用户失败", None

        # 5. 更新设备信息
        await self._update_device(user.user_id, device_id)

        # 6. 创建自定义 Token
        custom_token = await firebase_service.create_custom_token(
            user.user_id, additional_claims={"email": email, "provider": "email"}
        )

        # 7. 创建会话
        await self._create_session(user.user_id, device_id, custom_token)

        # 8. 判断是否首次登录
        is_first_login = await self._is_first_login(user.user_id)

        # 9. 返回响应
        response_data = LoginData(
            custom_token=custom_token or "",
            user_info=UserInfo(
                user_id=user.user_id,
                user_name=user.user_name or "",
                avatar=user.avatar or "",
            ),
            is_first_login=is_first_login,
        )

        return ErrorCode.SUCCESS, "成功", response_data

    async def send_verify_code(self, email: str, device_id: str) -> Tuple[int, str]:
        """
        发送验证码

        流程：
        1. 生成验证码
        2. 存储到 Redis
        3. 发送邮件

        Args:
            email: 邮箱地址
            device_id: 设备ID

        Returns:
            (错误码, 消息)
        """
        # 1. 生成验证码
        code = email_service.generate_verify_code()

        # 2. 存储验证码到 Redis
        stored = await self._set_verify_code(email, code, device_id)
        if not stored:
            return ErrorCode.GENERAL_ERROR, "系统错误，请稍后重试"

        # 3. 发送邮件
        sent = await email_service.send_verify_code(email, code)
        if not sent:
            await self._delete_verify_code(email, device_id)
            return ErrorCode.EMAIL_SEND_FAILED, "邮件发送失败，请检查邮箱地址或稍后重试"

        logger.info(f"验证码已发送: {email}")
        return ErrorCode.SUCCESS, "成功"

    async def logout(self, user_id: str, device_id: str) -> Tuple[int, str]:
        """
        用户登出

        流程：
        1. 获取用户的 Firebase UID
        2. 撤销 Firebase Refresh Token
        3. 删除 Redis 会话
        4. 使数据库中的会话失效
        5. 更新设备状态

        Args:
            user_id: 用户ID
            device_id: 设备ID

        Returns:
            (错误码, 消息)
        """
        try:
            # 1. 获取用户信息
            stmt = select(User).where(User.user_id == user_id)
            result = await self.db.execute(stmt)
            user = result.scalar_one_or_none()

            # 2. 撤销 Firebase Refresh Token
            if user and user.firebase_uid:
                revoked = await firebase_service.revoke_refresh_tokens(user.firebase_uid)
                if revoked:
                    logger.info(
                        f"Firebase Token已撤销: user_id={user_id}, firebase_uid={user.firebase_uid}"
                    )
                else:
                    logger.warning(f"Firebase Token撤销失败，继续执行本地登出: user_id={user_id}")

            # 3. 删除 Redis 会话
            await self._delete_session(user_id, device_id)

            # 4. 使数据库中的会话失效
            stmt = (
                update(UserSession)
                .where(
                    UserSession.user_id == user_id,
                    UserSession.device_id == device_id,
                    UserSession.is_valid == 1,
                )
                .values(is_valid=0, update_time=current_timestamp_ms())
            )
            await self.db.execute(stmt)

            # 5. 更新设备状态
            stmt = (
                update(UserDevice)
                .where(
                    UserDevice.user_id == user_id,
                    UserDevice.device_id == device_id,
                )
                .values(is_active=0, update_time=current_timestamp_ms())
            )
            await self.db.execute(stmt)

            await self.db.commit()

            logger.info(f"用户登出成功: user_id={user_id}, device_id={device_id}")
            return ErrorCode.SUCCESS, "成功"

        except Exception as e:
            logger.error(f"用户登出失败: {e}")
            await self.db.rollback()
            return ErrorCode.GENERAL_ERROR, "登出失败"

    # =========================================================================
    # 私有方法
    # =========================================================================

    async def _get_or_create_user(
        self,
        firebase_uid: str,
        email: Optional[str] = None,
        user_name: Optional[str] = None,
        avatar: Optional[str] = None,
        login_provider: Optional[str] = None,
    ) -> Optional[User]:
        """查询或创建用户"""
        try:
            # 先按 firebase_uid 查询
            stmt = select(User).where(User.firebase_uid == firebase_uid)
            result = await self.db.execute(stmt)
            user = result.scalar_one_or_none()

            if user:
                if user_name and not user.user_name:
                    user.user_name = user_name
                if avatar and not user.avatar:
                    user.avatar = avatar
                user.update_time = current_timestamp_ms()
                await self.db.commit()
                return user

            # 如果有邮箱，再按邮箱查询
            if email:
                stmt = select(User).where(User.email == email)
                result = await self.db.execute(stmt)
                user = result.scalar_one_or_none()

                if user:
                    user.firebase_uid = firebase_uid
                    if user_name and not user.user_name:
                        user.user_name = user_name
                    if avatar and not user.avatar:
                        user.avatar = avatar
                    user.update_time = current_timestamp_ms()
                    await self.db.commit()
                    return user

            # 创建新用户
            user = User(
                user_id=generate_user_id(),
                firebase_uid=firebase_uid,
                email=email,
                user_name=user_name,
                avatar=avatar,
                login_provider=login_provider,
                status=1,
            )
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)

            logger.info(f"新用户创建成功: {user.user_id}")
            return user

        except Exception as e:
            logger.error(f"查询/创建用户失败: {e}")
            await self.db.rollback()
            return None

    async def _update_device(self, user_id: str, device_id: str) -> Optional[UserDevice]:
        """更新设备信息"""
        try:
            stmt = select(UserDevice).where(
                UserDevice.user_id == user_id,
                UserDevice.device_id == device_id,
            )
            result = await self.db.execute(stmt)
            device = result.scalar_one_or_none()

            now = current_timestamp_ms()

            if device:
                device.last_active_at = now
                device.is_active = 1
                device.update_time = now
            else:
                device = UserDevice(
                    user_id=user_id,
                    device_id=device_id,
                    last_active_at=now,
                    is_active=1,
                )
                self.db.add(device)

            await self.db.commit()
            return device

        except Exception as e:
            logger.error(f"更新设备信息失败: {e}")
            await self.db.rollback()
            return None

    async def _create_session(
        self, user_id: str, device_id: str, custom_token: Optional[str]
    ) -> Optional[str]:
        """创建用户会话"""
        try:
            now = current_timestamp_ms()
            expires_at = now + (SESSION_TTL * 1000)

            # 1. 删除该用户+设备的旧 session（Redis）
            await auth_service.delete_user_sessions(user_id, device_id)

            # 2. 将数据库中旧 session 置为无效
            stmt = (
                update(UserSession)
                .where(
                    UserSession.user_id == user_id,
                    UserSession.device_id == device_id,
                    UserSession.is_valid == 1,
                )
                .values(is_valid=0, update_time=now)
            )
            await self.db.execute(stmt)

            # 3. 生成新的 session_id 并存储到 Redis
            session_id = auth_service.generate_session_id()
            extra_data = {
                "custom_token": custom_token or "",
                "created_at": now,
            }
            success = await auth_service.create_session(
                session_id=session_id,
                user_id=user_id,
                device_id=device_id,
                extra_data=extra_data,
            )

            if not success:
                logger.error("Redis session 创建失败")
                return None

            # 4. 创建新 session 记录到数据库
            session = UserSession(
                session_id=session_id,
                user_id=user_id,
                device_id=device_id,
                custom_token=custom_token,
                is_valid=1,
                expires_at=expires_at,
                last_used_at=now,
            )
            self.db.add(session)
            await self.db.commit()

            # 5. 设置 session_id 到响应
            set_session_id_for_response(session_id)

            logger.info(f"会话创建成功: session_id={session_id}, user_id={user_id}")
            return session_id

        except Exception as e:
            logger.error(f"创建会话失败: {e}")
            await self.db.rollback()
            return None

    async def _delete_session(self, user_id: str, device_id: str) -> bool:
        """删除 Redis 会话"""
        try:
            await auth_service.delete_user_sessions(user_id, device_id)
            return True
        except Exception as e:
            logger.error(f"删除会话失败: {e}")
            return False

    async def _set_verify_code(self, email: str, code: str, device_id: str) -> bool:
        """存储验证码到 Redis"""
        try:
            key = f"verify:{email}:{device_id}"
            ttl = settings.verify_code.expire_minutes * 60
            await redis_client.set(key, code, ex=ttl)
            return True
        except Exception as e:
            logger.error(f"存储验证码失败: {e}")
            return False

    async def _get_verify_code(self, email: str, device_id: str) -> Optional[str]:
        """从 Redis 获取验证码"""
        try:
            key = f"verify:{email}:{device_id}"
            return await redis_client.get(key)
        except Exception as e:
            logger.error(f"获取验证码失败: {e}")
            return None

    async def _delete_verify_code(self, email: str, device_id: str) -> bool:
        """删除 Redis 中的验证码"""
        try:
            key = f"verify:{email}:{device_id}"
            await redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"删除验证码失败: {e}")
            return False

    async def _is_first_login(self, user_id: str) -> bool:
        """
        判断是否首次登录

        通过 user_sessions 表中该用户的记录数判断，
        只有1条记录（当前会话）则为首次登录
        """
        try:
            stmt = select(func.count()).select_from(UserSession).where(
                UserSession.user_id == user_id
            )
            result = await self.db.execute(stmt)
            count = result.scalar() or 0
            return count <= 1
        except Exception as e:
            logger.error(f"查询首次登录状态失败: {e}")
            return False
