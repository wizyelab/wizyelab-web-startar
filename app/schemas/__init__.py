"""api层数据模型模块"""

# 可以在这里定义请求和响应的 Pydantic 模型
from .common import BaseResponse, Video, Author, PaginationRequest, PaginationData
from .account import (
    DeviceInfo,
    UserInfo,
    LoginRequest,
    LoginData,
    SendVerifyCodeRequest,
    LogoutRequest,
    ErrorCode,
    ErrorMessage,
)
