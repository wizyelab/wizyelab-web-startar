# 架构改进记录

## 2026-01-27 — 认证体系与基础架构完善

参照 `joiiee-server-startar` 项目，对项目架构进行全面升级。

### 新增文件

| 文件 | 说明 |
|------|------|
| `app/schemas/common.py` | 通用响应模型（`BaseResponse[T]`、分页模型、媒体模型） |
| `app/schemas/account.py` | 账户相关数据模型（登录、验证码、登出、用户信息） |
| `app/core/deps.py` | FastAPI 依赖注入模块（`get_current_user_id`、`get_current_session_id`、`get_optional_user_id`） |
| `app/services/auth_service.py` | 认证服务（Session 的创建、查询、验证、删除、刷新） |
| `app/api/v1/internal/routers/account.py` | 账户路由（登录、登出、发送验证码、获取当前用户） |

### 增强文件

| 文件 | 变更内容 |
|------|---------|
| `app/core/config.py` | 新增 `SessionConfig`、`AuthConfig`、`FirebaseConfig`、`SMTPConfig`、`VerifyCodeConfig`、`SnowflakeConfig` 配置类；`CORSConfig` 增加 `expose_headers`；`OSSConfig` 增加 `file_host`；`Settings` 类注册所有新配置并补充 `_build_config_dict` 解析逻辑 |
| `app/middleware/request_context.py` | `RequestContext` 增加 `session_id`、`_new_session_id` 字段；新增 `get_session_id()`、`set_session_id_for_response()` 全局函数；`RequestContextMiddleware` 增加 Session 解析（Header + Cookie）、路由认证校验、401 响应、登录成功后自动设置响应 Cookie/Header |
| `configs/base.yaml` | 新增 `session`、`auth`、`firebase`、`smtp`、`verify_code`、`snowflake` 配置段；`cors` 增加 `expose_headers`；`oss` 增加 `file_host` |

### 架构要点

- **Session 认证**：基于 Redis 的 Session 管理，支持 Header（`X-Session-ID`，移动端）和 Cookie（Web 端）双通道
- **路由保护**：中间件层统一拦截，通过 `auth.public_path_prefixes` 和 `auth.public_exact_paths` 配置白名单
- **依赖注入**：路由通过 `Depends(get_current_user_id)` 获取已认证用户，未登录自动返回 401
- **统一响应**：所有接口使用 `BaseResponse[T]` 泛型模型，包含 `code`、`message`、`data`
- **配置管理**：新增配置均支持 YAML 定义 + `WIZYELAB_*` 环境变量覆盖

### 待完善

- [x] 用户数据库模型（User、UserDevice、UserSession 表）
- [x] Firebase 第三方登录验证逻辑
- [x] 邮箱验证码发送与校验逻辑
- [x] 用户资料（Profile）服务与路由
- [x] 邮件发送服务（EmailService）

---

## 2026-01-27 — 业务服务完善（Phase 2）

延续 Phase 1 架构基础，补全所有待完善模块。

### 新增文件

| 文件 | 说明 |
|------|------|
| `app/models/user.py` | 用户数据库模型（`User`、`UserDevice`、`UserSession`），雪花算法ID，毫秒级时间戳 |
| `app/models/profile.py` | Profile 模块数据库模型（`UserProfile`、`UserStats`、`UserFollow`、`Post`、`UserAction`、`UserFeedback`、`GuideItemModel`、`Tag`），含枚举定义 |
| `app/services/firebase_service.py` | Firebase Admin SDK 集成（Token 验证、用户管理、自定义 Token 生成、Token 撤销） |
| `app/services/email_service.py` | 邮件服务（验证码生成、验证码邮件发送、通用邮件发送），支持 HTML + 纯文本 |
| `app/services/account_service.py` | 账户业务服务（第三方登录、邮箱验证码登录、发送验证码、登出），完整业务流程 |
| `app/services/profile_service.py` | Profile 业务服务（用户资料、引导列表、帖子 CRUD、关注/取关、粉丝列表、用户反馈） |
| `app/schemas/profile.py` | Profile 数据模型（ProfileData、GuideData、ProfilePost、FollowData 等） |
| `app/api/v1/internal/routers/profile.py` | Profile 路由（info、update、posts、create/delete post、follow、followers、feedback） |

### 增强文件

| 文件 | 变更内容 |
|------|---------|
| `app/schemas/account.py` | 重构为 joiiee 模式：新增 `DeviceInfo`、`UserInfo`、`LoginData`、`ErrorCode`、`ErrorMessage`；`LoginRequest` 改为 `id_token` + `email` + `verify_code` + `device_info` 模式 |
| `app/api/v1/internal/routers/account.py` | 从 TODO 占位实现替换为完整的 `AccountService(db)` 调用，支持第三方登录和邮箱验证码登录 |
| `app/api/v1/internal/routers/__init__.py` | 注册 `account` 和 `profile` 路由模块 |
| `main.py` | 在 lifespan 中添加 Firebase Admin SDK 初始化 |

### 架构要点

- **AccountService**：封装登录/注册/登出完整业务流程，支持 Firebase 第三方登录 + 邮箱验证码登录
- **ProfileService**：封装用户资料、帖子、关注、反馈等社交功能
- **Firebase 集成**：单例模式，支持 Token 验证（Google/Apple）、用户管理、自定义 Token 生成、Refresh Token 撤销
- **邮件服务**：异步 SMTP 发送，支持 HTML + 纯文本模板，开发模式下 mock 发送
- **验证码机制**：Redis 存储，按 `email + device_id` 维度隔离，可配置有效期和长度
- **错误码体系**：`ErrorCode` 类定义分层错误码（通用 0-499、账户 1000-1999、Firebase 2000-2999）
- **数据模型**：完整的用户表（User/UserDevice/UserSession）和 Profile 表（UserProfile/UserStats/UserFollow/Post/UserAction/UserFeedback/GuideItemModel/Tag）
