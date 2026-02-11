"""Account相关数据模型"""

from typing import Optional
from pydantic import BaseModel, Field
from app.core.error_codes import ErrorCode, ErrorMessage  # noqa: F401


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

