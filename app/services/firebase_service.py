"""
Firebase Admin SDK 集成模块

支持：
1. Google 第三方登录验证
2. Apple 第三方登录验证
3. 自定义Token生成
4. Token撤销（用于安全登出）
5. 用户管理（查询、创建）

参考: firebase-admin-python SDK
- auth.revoke_refresh_tokens(): 撤销用户所有Refresh Token
- auth.verify_id_token(check_revoked=True): 验证时检查Token是否已撤销
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

    从配置文件读取凭证路径，支持：
    1. FIREBASE_CREDENTIALS_PATH 环境变量指向服务账号密钥文件
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
                "Set FIREBASE_CREDENTIALS_PATH in environment variables."
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
            # 初始化 Firebase
            init_firebase()
        return cls._instance

    async def verify_id_token(
        self,
        id_token: str,
        check_revoked: bool = False
    ) -> Tuple[Optional[Dict[str, Any]], str]:
        """
        验证 Firebase ID Token（来自Google/Apple第三方登录）

        参考 firebase-admin-python/_auth_client.py:95-140

        Args:
            id_token: Firebase ID Token
            check_revoked: 是否检查Token是否已被撤销（登出后的Token会被撤销）

        Returns:
            (decoded_token, error_type)
            - 成功: (decoded_token, "")
            - 失败: (None, error_type) 其中 error_type 可以是:
              - "invalid": 无效Token
              - "expired": Token已过期
              - "revoked": Token已被撤销（用户已登出）
              - "disabled": 用户已被禁用
              - "error": 其他错误
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
            # Token已被撤销（用户执行了登出操作）
            logger.warning(f"ID Token已被撤销: {e}")
            return None, "revoked"

        except _auth.UserDisabledError as e:
            # 用户账户已被禁用
            logger.warning(f"用户已被禁用: {e}")
            return None, "disabled"

        except Exception as e:
            logger.error(f"Token验证异常: {e}")
            return None, "error"

    async def get_user_by_uid(self, uid: str) -> Optional[Any]:
        """
        根据UID获取Firebase用户信息

        Args:
            uid: Firebase用户UID

        Returns:
            用户记录，不存在返回None
        """
        if _auth is None:
            logger.warning("Firebase not initialized")
            return None

        try:
            user = _auth.get_user(uid)
            return user
        except _auth.UserNotFoundError:
            logger.warning(f"用户不存在: {uid}")
            return None
        except Exception as e:
            logger.error(f"获取用户信息异常: {e}")
            return None

    async def get_user_by_email(self, email: str) -> Optional[Any]:
        """
        根据邮箱获取Firebase用户信息

        Args:
            email: 用户邮箱

        Returns:
            用户记录，不存在返回None
        """
        if _auth is None:
            logger.warning("Firebase not initialized")
            return None

        try:
            user = _auth.get_user_by_email(email)
            return user
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
        """
        在Firebase中创建用户

        Args:
            email: 用户邮箱
            display_name: 显示名称

        Returns:
            创建的用户记录
        """
        if _auth is None:
            logger.warning("Firebase not initialized")
            return None

        try:
            user_args = {
                "email": email,
                "email_verified": True,  # 邮箱验证通过才创建
            }
            if display_name:
                user_args["display_name"] = display_name

            user = _auth.create_user(**user_args)
            logger.info(f"Firebase用户创建成功: {user.uid}")
            return user

        except _auth.EmailAlreadyExistsError:
            logger.warning(f"邮箱已存在: {email}")
            # 如果用户已存在，返回已存在的用户
            return await self.get_user_by_email(email)

        except Exception as e:
            logger.error(f"创建用户异常: {e}")
            return None

    async def create_custom_token(
        self,
        uid: str,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        创建自定义Token

        Args:
            uid: 用户UID（将作为Firebase的uid）
            additional_claims: 附加声明

        Returns:
            自定义Token字符串
        """
        if _auth is None:
            logger.warning("Firebase not initialized")
            return None

        try:
            custom_token = _auth.create_custom_token(uid, additional_claims)
            # custom_token是bytes类型，需要解码
            if isinstance(custom_token, bytes):
                custom_token = custom_token.decode('utf-8')
            logger.info(f"自定义Token创建成功: {uid}")
            return custom_token

        except Exception as e:
            logger.error(f"创建自定义Token异常: {e}")
            return None

    async def revoke_refresh_tokens(self, uid: str) -> bool:
        """
        撤销用户的所有Refresh Token

        参考 firebase-admin-python/_auth_client.py:142-161

        此方法会更新用户的 tokens_valid_after_timestamp 到当前UTC时间。
        调用后：
        - 所有现有会话将被终止
        - 新的ID Token将无法从现有会话中获取
        - 现有ID Token在自然过期（1小时）前仍然有效
        - 使用 verify_id_token(check_revoked=True) 可以立即检测已撤销的Token

        Args:
            uid: Firebase用户UID

        Returns:
            是否成功撤销
        """
        if _auth is None:
            logger.warning("Firebase not initialized")
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
