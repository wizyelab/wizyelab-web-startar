"""
认证服务模块

提供 session 验证、用户身份获取等功能
"""

from typing import Optional, Dict, Any, Tuple

from app.core.logging import setup_logger
from app.core.snowflake import generate_id_str
from app.core.config import settings
from app.infrastructure.cache.redis_client import redis_client

logger = setup_logger(__name__)

# Session 配置
SESSION_TTL = settings.session.ttl_days * 24 * 3600  # 从配置读取
SESSION_PREFIX = "auth:session:"  # session:{session_id} -> session_data


class AuthService:
    """
    认证服务

    职责：
    1. 创建和管理 session
    2. 验证 session 有效性
    3. 根据 session 获取用户信息
    """

    @staticmethod
    def generate_session_id() -> str:
        """生成 session_id（雪花算法）"""
        return generate_id_str()

    @staticmethod
    async def create_session(
        session_id: str,
        user_id: str,
        device_id: str,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        创建 session 并存入 Redis

        Args:
            session_id: 会话ID
            user_id: 用户ID
            device_id: 设备ID
            extra_data: 额外数据

        Returns:
            是否成功
        """
        try:
            session_key = f"{SESSION_PREFIX}{session_id}"
            session_data = {
                "session_id": session_id,
                "user_id": user_id,
                "device_id": device_id,
                **(extra_data or {}),
            }
            await redis_client.set_json(session_key, session_data, ex=SESSION_TTL)

            # 同时存储用户维度的索引，用于登出时清理
            user_session_key = f"auth:user_session:{user_id}:{device_id}"
            await redis_client.set(user_session_key, session_id, ex=SESSION_TTL)

            logger.info(f"Session 创建成功: session_id={session_id}, user_id={user_id}")
            return True

        except Exception as e:
            logger.error(f"创建 session 失败: {e}")
            return False

    @staticmethod
    async def get_session(session_id: str) -> Optional[Dict[str, Any]]:
        """
        根据 session_id 获取 session 数据

        Args:
            session_id: 会话ID

        Returns:
            session 数据，不存在或已过期返回 None
        """
        if not session_id:
            return None

        try:
            session_key = f"{SESSION_PREFIX}{session_id}"
            session_data = await redis_client.get_json(session_key)
            return session_data

        except Exception as e:
            logger.error(f"获取 session 失败: {e}")
            return None

    @staticmethod
    async def get_user_id_by_session(session_id: str) -> Optional[str]:
        """
        根据 session_id 获取 user_id

        Args:
            session_id: 会话ID

        Returns:
            user_id，不存在返回 None
        """
        session_data = await AuthService.get_session(session_id)
        if session_data:
            return session_data.get("user_id")
        return None

    @staticmethod
    async def validate_session(session_id: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        验证 session 有效性

        Args:
            session_id: 会话ID

        Returns:
            (is_valid, user_id, error_message)
        """
        if not session_id:
            return False, None, "session_id 不能为空"

        session_data = await AuthService.get_session(session_id)

        if not session_data:
            return False, None, "session 不存在或已过期"

        user_id = session_data.get("user_id")
        if not user_id:
            return False, None, "session 数据异常"

        return True, user_id, None

    @staticmethod
    async def delete_session(session_id: str) -> bool:
        """
        删除 session

        Args:
            session_id: 会话ID

        Returns:
            是否成功
        """
        try:
            # 先获取 session 数据，用于删除用户维度的索引
            session_data = await AuthService.get_session(session_id)

            # 删除 session
            session_key = f"{SESSION_PREFIX}{session_id}"
            await redis_client.delete(session_key)

            # 删除用户维度的索引
            if session_data:
                user_id = session_data.get("user_id")
                device_id = session_data.get("device_id")
                if user_id and device_id:
                    user_session_key = f"auth:user_session:{user_id}:{device_id}"
                    await redis_client.delete(user_session_key)

            logger.info(f"Session 删除成功: session_id={session_id}")
            return True

        except Exception as e:
            logger.error(f"删除 session 失败: {e}")
            return False

    @staticmethod
    async def delete_user_sessions(user_id: str, device_id: Optional[str] = None) -> bool:
        """
        删除用户的 session（用于登出）

        Args:
            user_id: 用户ID
            device_id: 设备ID（如果指定，只删除该设备的 session）

        Returns:
            是否成功
        """
        try:
            if device_id:
                # 删除指定设备的 session
                user_session_key = f"auth:user_session:{user_id}:{device_id}"
                session_id = await redis_client.get(user_session_key)
                if session_id:
                    await AuthService.delete_session(session_id)
            else:
                # 删除用户所有 session（需要遍历，生产环境建议用 scan）
                pattern = f"auth:user_session:{user_id}:*"
                async for key in redis_client.client.scan_iter(match=pattern):
                    session_id = await redis_client.get(key)
                    if session_id:
                        await AuthService.delete_session(session_id)

            return True

        except Exception as e:
            logger.error(f"删除用户 session 失败: {e}")
            return False

    @staticmethod
    async def refresh_session(session_id: str) -> bool:
        """
        刷新 session 过期时间

        Args:
            session_id: 会话ID

        Returns:
            是否成功
        """
        try:
            session_key = f"{SESSION_PREFIX}{session_id}"
            # 刷新过期时间
            result = await redis_client.expire(session_key, SESSION_TTL)
            return result

        except Exception as e:
            logger.error(f"刷新 session 失败: {e}")
            return False


# 全局认证服务实例
auth_service = AuthService()
