"""账户相关数据模型"""

from typing import Optional
from pydantic import BaseModel, Field


# ========================= 登录相关 =========================


class LoginRequest(BaseModel):
    """登录请求"""

    login_type: str = Field(..., description="登录类型: email/google/apple")
    email: Optional[str] = Field(default=None, description="邮箱（邮箱验证码登录时必填）")
    verify_code: Optional[str] = Field(default=None, description="验证码（邮箱验证码登录时必填）")
    id_token: Optional[str] = Field(default=None, description="Firebase ID Token（第三方登录时必填）")
    device_id: str = Field(default="", description="设备ID")
    device_type: str = Field(default="", description="设备类型: ios/android/web")


class LoginResponse(BaseModel):
    """登录响应数据"""

    user_id: str = Field(..., description="用户ID")
    session_id: str = Field(..., description="会话ID")
    is_new_user: bool = Field(default=False, description="是否新用户")


# ========================= 验证码相关 =========================


class SendVerifyCodeRequest(BaseModel):
    """发送验证码请求"""

    email: str = Field(..., description="邮箱地址")


class SendVerifyCodeResponse(BaseModel):
    """发送验证码响应"""

    success: bool = Field(default=True, description="是否成功")
    message: str = Field(default="验证码已发送", description="提示信息")


# ========================= 登出相关 =========================


class LogoutRequest(BaseModel):
    """登出请求"""

    device_id: Optional[str] = Field(default=None, description="设备ID（不传则登出当前设备）")
    all_devices: bool = Field(default=False, description="是否登出所有设备")


class LogoutResponse(BaseModel):
    """登出响应"""

    success: bool = Field(default=True, description="是否成功")


# ========================= 用户信息相关 =========================


class UserInfo(BaseModel):
    """用户基本信息"""

    user_id: str = Field(..., description="用户ID")
    email: str = Field(default="", description="邮箱")
    username: str = Field(default="", description="用户名")
    avatar: str = Field(default="", description="头像URL")
    bio: str = Field(default="", description="个人简介")
    gender: str = Field(default="", description="性别: male/female/other")
    location: str = Field(default="", description="位置")
    login_provider: str = Field(default="", description="登录方式: email/google/apple")
