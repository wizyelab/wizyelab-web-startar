"""
Firebase Admin SDK 集成模块

支持：
1. Google 第三方登录验证
2. Apple 第三方登录验证
3. 自定义Token生成
4. Token撤销（用于安全登出）
5. 用户管理（查询、创建）
"""

from typing import Optional, Tuple, Dict, Any

from app.core.logging import setup_logger
from app.core.config import settings

logger = setup_logger(__name__)

# Firebase Admin SDK
_firebase_app = None
_auth = None
_initialized = False


def init_firebase():
    """
    初始化 Firebase Admin SDK

    从配置文件读取凭证路径
    """
    global _firebase_app, _auth, _initialized

    if _initialized:
        return _firebase_app is not None

    _initialized = True

    try:
        import firebase_admin
        from firebase_admin import credentials, auth

        cred_path = settings.firebase.credentials_path
        project_id = settings.firebase.project_id

        if not cred_path:
            logger.warning(
                "Firebase credentials path not configured. "
                "Set firebase.credentials_path in config."
            )
            return False

        import os
        if not os.path.exists(cred_path):
            logger.warning(
                f"Firebase credentials file not found: {cred_path}. "
                "Firebase features will be disabled."
            )
            return False

        cred = credentials.Certificate(cred_path)
        options = {}
        if project_id:
            options['projectId'] = project_id

        _firebase_app = firebase_admin.initialize_app(cred, options)
        _auth = auth
        logger.info("Firebase Admin SDK initialized successfully")
        return True

    except ImportError:
        logger.warning(
            "firebase-admin package not installed. "
            "Run: pip install firebase-admin"
        )
        return False
    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {e}")
        return False


class FirebaseService:
    """Firebase 服务类 - 单例模式"""

    _instance: Optional['FirebaseService'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            init_firebase()
        return cls._instance

    async def verify_id_token(
        self,
        id_token: str,
        check_revoked: bool = False
    ) -> Tuple[Optional[Dict[str, Any]], str]:
        """
        验证 Firebase ID Token（来自Google/Apple第三方登录）

        Args:
            id_token: Firebase ID Token
            check_revoked: 是否检查Token是否已被撤销

        Returns:
            (decoded_token, error_type)
            - 成功: (decoded_token, "")
            - 失败: (None, error_type)
        """
        if _auth is None:
            logger.warning("Firebase not initialized")
            return None, "error"

        try:
            decoded_token = _auth.verify_id_token(id_token, check_revoked=check_revoked)
            logger.info(f"Token验证成功，用户UID: {decoded_token.get('uid')}")
            return decoded_token, ""

        except _auth.InvalidIdTokenError as e:
            logger.warning(f"无效的ID Token: {e}")
            return None, "invalid"

        except _auth.ExpiredIdTokenError as e:
            logger.warning(f"ID Token已过期: {e}")
            return None, "expired"

        except _auth.RevokedIdTokenError as e:
            logger.warning(f"ID Token已被撤销: {e}")
            return None, "revoked"

        except _auth.UserDisabledError as e:
            logger.warning(f"用户已被禁用: {e}")
            return None, "disabled"

        except Exception as e:
            logger.error(f"Token验证异常: {e}")
            return None, "error"

    async def get_user_by_uid(self, uid: str) -> Optional[Any]:
        """根据UID获取Firebase用户信息"""
        if _auth is None:
            return None

        try:
            return _auth.get_user(uid)
        except _auth.UserNotFoundError:
            logger.warning(f"用户不存在: {uid}")
            return None
        except Exception as e:
            logger.error(f"获取用户信息异常: {e}")
            return None

    async def get_user_by_email(self, email: str) -> Optional[Any]:
        """根据邮箱获取Firebase用户信息"""
        if _auth is None:
            return None

        try:
            return _auth.get_user_by_email(email)
        except _auth.UserNotFoundError:
            logger.info(f"邮箱用户不存在: {email}")
            return None
        except Exception as e:
            logger.error(f"获取用户信息异常: {e}")
            return None

    async def create_user(
        self,
        email: str,
        display_name: Optional[str] = None
    ) -> Optional[Any]:
        """在Firebase中创建用户"""
        if _auth is None:
            return None

        try:
            user_args = {
                "email": email,
                "email_verified": True,
            }
            if display_name:
                user_args["display_name"] = display_name

            user = _auth.create_user(**user_args)
            logger.info(f"Firebase用户创建成功: {user.uid}")
            return user

        except _auth.EmailAlreadyExistsError:
            logger.warning(f"邮箱已存在: {email}")
            return await self.get_user_by_email(email)

        except Exception as e:
            logger.error(f"创建用户异常: {e}")
            return None

    async def create_custom_token(
        self,
        uid: str,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """创建自定义Token"""
        if _auth is None:
            return None

        try:
            custom_token = _auth.create_custom_token(uid, additional_claims)
            if isinstance(custom_token, bytes):
                custom_token = custom_token.decode('utf-8')
            logger.info(f"自定义Token创建成功: {uid}")
            return custom_token

        except Exception as e:
            logger.error(f"创建自定义Token异常: {e}")
            return None

    async def revoke_refresh_tokens(self, uid: str) -> bool:
        """撤销用户的所有Refresh Token"""
        if _auth is None:
            return False

        try:
            _auth.revoke_refresh_tokens(uid)
            logger.info(f"用户Refresh Token已撤销: {uid}")
            return True

        except _auth.UserNotFoundError:
            logger.warning(f"撤销Token失败 - 用户不存在: {uid}")
            return False

        except Exception as e:
            logger.error(f"撤销Refresh Token异常: {e}")
            return False


# 全局 Firebase 服务实例
firebase_service = FirebaseService()
