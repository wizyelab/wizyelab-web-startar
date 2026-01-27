"""Account相关数据模型"""

from typing import Optional
from pydantic import BaseModel, Field


# ========================= 公共模型 =========================


class DeviceInfo(BaseModel):
    """设备信息"""

    device_id: str = Field(default="", description="设备ID")


class UserInfo(BaseModel):
    """用户信息"""

    user_id: str = Field(default="", description="用户ID")
    user_name: str = Field(default="", description="用户名称")
    avatar: str = Field(default="", description="头像URL")


# ========================= 登录相关 =========================


class LoginRequest(BaseModel):
    """
    用户登录请求

    支持两种登录方式:
    1. 第三方登录（Google/Apple）- 使用 id_token
    2. 邮箱验证码登录 - 使用 email + verify_code
    """

    id_token: str = Field(default="", description="第三方登录Token（Google/Apple）")
    verify_code: str = Field(default="", description="邮箱验证码，6位数字")
    email: str = Field(default="", description="邮箱地址（邮箱登录时需要）")
    device_info: Optional[DeviceInfo] = Field(default=None, description="设备信息")


class LoginData(BaseModel):
    """登录响应数据"""

    custom_token: str = Field(default="", description="自定义Token，用于后续API调用的身份凭证")
    user_info: Optional[UserInfo] = Field(default=None, description="用户信息")
    is_first_login: bool = Field(default=False, description="是否首次登录")


# ========================= 发送验证码 =========================


class SendVerifyCodeRequest(BaseModel):
    """发送验证码请求"""

    email: str = Field(..., description="接收验证码的邮箱地址")
    device_info: Optional[DeviceInfo] = Field(default=None, description="设备信息")


# ========================= 登出相关 =========================


class LogoutRequest(BaseModel):
    """用户登出请求"""

    user_id: str = Field(..., description="用户ID")
    device_info: Optional[DeviceInfo] = Field(default=None, description="设备信息")


# ========================= 错误码定义 =========================


class ErrorCode:
    """Account模块错误码定义"""

    SUCCESS = 0
    GENERAL_ERROR = 1
    INVALID_PARAMS = 100
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404

    # 账户相关错误码 1000-1999
    INVALID_TOKEN = 1001
    TOKEN_EXPIRED = 1002
    INVALID_VERIFY_CODE = 1003
    VERIFY_CODE_EXPIRED = 1004
    EMAIL_SEND_FAILED = 1005
    USER_NOT_FOUND = 1006
    USER_DISABLED = 1007
    DEVICE_NOT_FOUND = 1008

    # Firebase相关错误码 2000-2999
    FIREBASE_AUTH_ERROR = 2001
    FIREBASE_TOKEN_INVALID = 2002
    FIREBASE_USER_NOT_FOUND = 2003


class ErrorMessage:
    """错误消息映射"""

    messages = {
        ErrorCode.SUCCESS: "成功",
        ErrorCode.GENERAL_ERROR: "系统错误",
        ErrorCode.INVALID_PARAMS: "参数错误",
        ErrorCode.UNAUTHORIZED: "未授权",
        ErrorCode.FORBIDDEN: "禁止访问",
        ErrorCode.NOT_FOUND: "资源不存在",
        ErrorCode.INVALID_TOKEN: "无效的Token",
        ErrorCode.TOKEN_EXPIRED: "Token已过期",
        ErrorCode.INVALID_VERIFY_CODE: "验证码错误",
        ErrorCode.VERIFY_CODE_EXPIRED: "验证码已过期",
        ErrorCode.EMAIL_SEND_FAILED: "邮件发送失败",
        ErrorCode.USER_NOT_FOUND: "用户不存在",
        ErrorCode.USER_DISABLED: "用户已禁用",
        ErrorCode.DEVICE_NOT_FOUND: "设备信息不存在",
        ErrorCode.FIREBASE_AUTH_ERROR: "Firebase认证错误",
        ErrorCode.FIREBASE_TOKEN_INVALID: "Firebase Token无效",
        ErrorCode.FIREBASE_USER_NOT_FOUND: "Firebase用户不存在",
    }

    @classmethod
    def get(cls, code: int) -> str:
        return cls.messages.get(code, "未知错误")
