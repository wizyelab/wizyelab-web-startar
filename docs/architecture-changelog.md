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

---

## 2026-02-07 — 框架能力增强（Phase 3）

从 `joiiee-server-startar` 项目提取核心框架能力，提升系统稳定性和生产就绪度。

### 增强文件

| 文件 | 变更内容 |
|------|---------|
| `app/infrastructure/cache/redis_client.py` | **Redis 自动重连机制**：新增 `_reconnect()` 方法，使用 `asyncio.Lock` 防止并发重连；`get()` 和 `set()` 方法增加重试逻辑（max_retries=2），检测连接错误（closed/connection/handler）时自动重连；连接池配置增加 `health_check_interval=30` 和 `retry_on_timeout=True` |
| `app/infrastructure/database/connection.py` | **数据库延迟初始化**：异步引擎改为延迟初始化模式，新增 `init_async_engine()` 函数在事件循环启动后调用；使用 `NullPool` 替代连接池，解决多 worker 模式下事件循环绑定问题；`get_async_db()`、`get_async_db_context()`、`async_init_db()` 增加初始化检查；`close_db()` 增加 `_async_engine_initialized` 重置和空值检查 |
| `main.py` | **lifespan 增强**：在 Redis 初始化前调用 `init_async_engine()`，确保异步引擎在事件循环运行后初始化 |
| `README.md` | **文档完善**：新增"框架能力"章节，详细说明数据库连接、Redis 客户端、对象存储、监控、配置管理、中间件、Snowflake ID 等核心能力；新增"生产就绪特性"章节，列举高可用性、可观测性、安全性、性能等特性 |
| `docs/architecture-changelog.md` | **变更记录**：新增 Phase 3 记录，说明框架增强内容和收益 |

### 新增文件

| 文件 | 说明 |
|------|------|
| `docs/infrastructure/README.md` | 基础设施组件文档，详细说明数据库、Redis、OSS、监控等组件的特性和使用方法 |

### 架构要点

#### Redis 自动重连机制
- **线程安全重连**：使用 `asyncio.Lock` 防止多个协程同时重连
- **连接健康检查**：重连前先 ping 检查，避免不必要的重连
- **优雅关闭旧连接**：使用 `asyncio.wait_for()` 设置超时，防止挂起
- **重试逻辑**：`get()` 和 `set()` 方法支持最多 2 次重试
- **错误检测**：识别 "closed"、"connection"、"handler" 等连接错误关键词

#### 数据库延迟初始化
- **事件循环绑定**：异步引擎在 FastAPI lifespan 中初始化，确保绑定到正确的事件循环
- **NullPool 策略**：禁用连接池，每次操作创建新连接，避免连接跨事件循环复用
- **多 worker 支持**：解决 uvicorn --workers N 模式下的事件循环不匹配问题
- **初始化检查**：所有异步数据库操作前检查引擎是否已初始化，未初始化抛出 RuntimeError

### 收益

#### 稳定性提升
- ✅ **Redis 连接失败自动恢复**：网络抖动、Redis 重启等场景下自动重连，无需重启服务
- ✅ **多 worker 模式稳定**：解决事件循环绑定问题，支持生产环境多 worker 部署
- ✅ **并发安全**：重连过程使用锁机制，防止雷鸣群效应

#### 生产就绪
- ✅ **高可用性**：自动故障恢复，减少人工介入
- ✅ **可扩展性**：支持多 worker 水平扩展
- ✅ **可维护性**：完善的文档和错误提示

#### 性能权衡
- ⚠️ **数据库性能**：NullPool 模式下每次操作创建新连接，性能略低于连接池模式，但换取了稳定性
- ✅ **Redis 性能**：自动重连不影响正常操作性能，仅在连接失败时触发
