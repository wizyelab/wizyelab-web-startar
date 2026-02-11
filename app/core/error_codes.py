"""统一错误码模块"""


class ErrorCode:
    """全局错误码定义"""

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

    # 文件相关错误码 3000-3999
    FILE_NOT_FOUND = 3001
    FILE_UPLOAD_FAILED = 3002
    FILE_DELETE_FAILED = 3003
    FILE_RECORD_SAVE_FAILED = 3004
    INVALID_FILE_CATEGORY = 3005
    FILE_TOO_LARGE = 3006


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
        ErrorCode.FILE_NOT_FOUND: "文件不存在",
        ErrorCode.FILE_UPLOAD_FAILED: "文件上传失败",
        ErrorCode.FILE_DELETE_FAILED: "文件删除失败",
        ErrorCode.FILE_RECORD_SAVE_FAILED: "文件记录保存失败",
        ErrorCode.INVALID_FILE_CATEGORY: "无效的文件分类",
        ErrorCode.FILE_TOO_LARGE: "文件过大",
    }

    @classmethod
    def get(cls, code: int) -> str:
        return cls.messages.get(code, "未知错误")
