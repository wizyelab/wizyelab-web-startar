"""
统一错误码定义

所有模块的错误码集中管理，避免冲突和散落。

编码规则:
  0       - 成功
  1       - 通用错误
  100-199 - 参数校验错误
  1xxx    - 认证/账户 (Auth & Account)
  2xxx    - Firebase
  3xxx    - 聊天/消息 (Chat & Message)
  4xxx    - 内容/帖子/评论 (Content & Social)
  5xxx    - 文件/上传 (File & Upload)
  6xxx    - 任务 (Task)
"""


class ErrorCode:
    """全局错误码"""

    # ==================== 通用 (0-199) ====================
    SUCCESS = 0
    GENERAL_ERROR = 1
    INVALID_PARAMS = 100

    # ==================== 认证/账户 (1000-1999) ====================
    INVALID_TOKEN = 1001
    TOKEN_EXPIRED = 1002
    INVALID_VERIFY_CODE = 1003
    VERIFY_CODE_EXPIRED = 1004
    EMAIL_SEND_FAILED = 1005
    USER_NOT_FOUND = 1006
    USER_DISABLED = 1007
    DEVICE_NOT_FOUND = 1008

    # ==================== Firebase (2000-2999) ====================
    FIREBASE_AUTH_ERROR = 2001
    FIREBASE_TOKEN_INVALID = 2002
    FIREBASE_USER_NOT_FOUND = 2003

    # ==================== 内容/社交 (4000-4999) ====================
    # 帖子
    POST_NOT_FOUND = 4001
    POST_NO_PERMISSION = 4002
    POST_DELETED = 4003
    # 评论
    COMMENT_NOT_FOUND = 4011
    COMMENT_NO_PERMISSION = 4012
    COMMENT_DELETED = 4013
    PARENT_COMMENT_NOT_FOUND = 4014
    # 关注
    CANNOT_FOLLOW_SELF = 4021
    ALREADY_FOLLOWED = 4022
    NOT_FOLLOWED = 4023
    # 互动
    TARGET_ID_REQUIRED = 4031
    FEEDBACK_FAILED = 4032

    # ==================== 文件/上传 (5000-5999) ====================
    FILE_NOT_FOUND = 5001
    UPLOAD_FAILED = 5002
    INVALID_FILE_CATEGORY = 5003
    FILE_RECORD_SAVE_FAILED = 5004


class ErrorMessage:
    """错误码 → 默认消息映射"""

    _messages = {
        # 通用
        ErrorCode.SUCCESS: "成功",
        ErrorCode.GENERAL_ERROR: "系统错误",
        ErrorCode.INVALID_PARAMS: "参数错误",
        # 认证/账户
        ErrorCode.INVALID_TOKEN: "无效的Token",
        ErrorCode.TOKEN_EXPIRED: "Token已过期",
        ErrorCode.INVALID_VERIFY_CODE: "验证码错误",
        ErrorCode.VERIFY_CODE_EXPIRED: "验证码已过期",
        ErrorCode.EMAIL_SEND_FAILED: "邮件发送失败",
        ErrorCode.USER_NOT_FOUND: "用户不存在",
        ErrorCode.USER_DISABLED: "用户已禁用",
        ErrorCode.DEVICE_NOT_FOUND: "设备信息不存在",
        # Firebase
        ErrorCode.FIREBASE_AUTH_ERROR: "Firebase认证错误",
        ErrorCode.FIREBASE_TOKEN_INVALID: "Firebase Token无效",
        ErrorCode.FIREBASE_USER_NOT_FOUND: "Firebase用户不存在",
        # 内容/社交
        ErrorCode.POST_NOT_FOUND: "帖子不存在",
        ErrorCode.POST_NO_PERMISSION: "无权操作此帖子",
        ErrorCode.POST_DELETED: "帖子已删除",
        ErrorCode.COMMENT_NOT_FOUND: "评论不存在",
        ErrorCode.COMMENT_NO_PERMISSION: "无权删除此评论",
        ErrorCode.COMMENT_DELETED: "评论已删除",
        ErrorCode.PARENT_COMMENT_NOT_FOUND: "父评论不存在",
        ErrorCode.CANNOT_FOLLOW_SELF: "不能关注自己",
        ErrorCode.ALREADY_FOLLOWED: "已经关注该用户",
        ErrorCode.NOT_FOLLOWED: "未关注该用户",
        ErrorCode.TARGET_ID_REQUIRED: "请指定目标ID",
        ErrorCode.FEEDBACK_FAILED: "反馈提交失败",
        # 文件/上传
        ErrorCode.FILE_NOT_FOUND: "文件不存在",
        ErrorCode.UPLOAD_FAILED: "上传失败",
        ErrorCode.INVALID_FILE_CATEGORY: "无效的文件分类",
        ErrorCode.FILE_RECORD_SAVE_FAILED: "文件记录保存失败",
    }

    @classmethod
    def get(cls, code: int, default: str = "未知错误") -> str:
        return cls._messages.get(code, default)
