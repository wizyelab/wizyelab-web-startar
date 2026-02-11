# Wizyelab Web Start

基于 FastAPI + LangChain 的智能运动助手后端服务

## 项目结构

```
.
├── .github/                          # GitHub 配置
│   └── workflows/                    # GitHub Actions 工作流
│       ├── ci.yml                    # CI 工作流（测试、代码检查）
│       └── cd.yml                    # CD 工作流（构建、部署）
├── app/                              # 应用主目录
│   ├── api/                          # API 路由
│   │   ├── v1/                       # API v1 版本
│   │   │   ├── public/               # 对外公开 API
│   │   │   │   ├── __init__.py       # 公开 API 路由
│   │   │   │   └── files.py          # 文件存储 API
│   │   │   ├── internal/             # 内部 API
│   │   │   └── __init__.py           # v1 路由聚合
│   │   └── router.py                 # 路由主聚合器
│   ├── core/                         # 核心模块
│   │   ├── config.py                 # 配置管理（多环境支持）
│   │   └── logging.py                # 日志配置
│   ├── infrastructure/               # 基础设施层
│   │   ├── database/                 # 数据库模块
│   │   │   ├── connection.py         # SQLAlchemy 连接池
│   │   │   └── models.py             # 数据库模型基类
│   │   ├── cache/                    # Redis 缓存模块
│   │   │   └── redis_client.py       # Redis 异步客户端
│   │   ├── storage/                  # 对象存储模块
│   │   │   └── oss_client.py         # 阿里云 OSS 客户端
│   │   └── monitoring/               # 监控模块
│   │       ├── health.py             # 健康检查
│   │       └── metrics.py            # Prometheus 指标
│   ├── services/                     # 业务服务层
│   │   ├── llm/                      # LLM 服务
│   │   │   ├── agent.py              # Wizyelab Agent
│   │   │   ├── chains.py             # LangChain Chains
│   │   │   ├── tools.py              # Agent 工具
│   │   │   ├── memory.py             # 对话记忆
│   │   │   └── llm_client.py         # LLM 客户端
│   │   └── storage/                  # 存储服务
│   │       └── oss_service.py        # OSS 业务服务
│   ├── middleware/                   # HTTP 中间件
│   │   ├── cors.py                   # CORS 配置
│   │   ├── rate_limit.py             # 限流中间件
│   │   └── request_logging.py        # 请求日志记录
│   └── schemas/                      # Pydantic 数据模型
├── configs/                          # 配置文件目录
│   ├── base.yaml                     # 基础配置（所有环境共享）
│   ├── dev.yaml                      # 开发环境配置
│   ├── staging.yaml                  # 预上线环境配置
│   └── prod.yaml                     # 生产环境配置
├── tests/                            # 测试文件
│   └── test_api.py                   # API 测试
├── .dockerignore                     # Docker 忽略文件
├── .env.example                      # 环境变量示例
├── docker-compose.cloud.yml          # Docker Compose（云部署：staging/prod）
├── .env.staging                      # Staging 环境部署配置
├── .env.prod                         # Production 环境部署配置
├── Dockerfile                        # Docker 镜像构建文件
├── main.py                           # 应用入口
├── pyproject.toml                    # Poetry 配置
└── README.md                         # 项目说明
```

## 技术栈

| 类别 | 技术 |
|------|------|
| **Web 框架** | FastAPI + Uvicorn |
| **包管理** | Poetry |
| **数据库** | PolarDB (MySQL 兼容) + SQLAlchemy 2.0 (异步) |
| **缓存** | Redis (Tair) + aioredis |
| **对象存储** | 阿里云 OSS |
| **LLM 框架** | LangChain 1.0 + OpenAI |
| **监控** | Prometheus + OpenTelemetry |
| **日志** | structlog (结构化 JSON 日志) |

## 环境要求

- Python >= 3.9
- Poetry (包管理工具)

## 安装

1. 安装 Poetry（如果尚未安装）:
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

2. 安装项目依赖:
```bash
poetry install
```

3. 激活虚拟环境:
```bash
poetry shell
```

4. 配置环境变量:
```bash
cp .env.xxx .env
# 编辑 .env 文件，填入实际配置
```

## 配置

### 多环境配置

项目支持多环境配置，配置文件位于 `configs/` 目录：

| 文件 | 说明 |
|------|------|
| `base.yaml` | 基础配置，所有环境共享的默认值 |
| `dev.yaml` | 开发环境配置 |
| `staging.yaml` | 预上线环境配置 |
| `prod.yaml` | 生产环境配置 |

**配置加载顺序**:
1. `base.yaml` (基础配置)
2. `{env}.yaml` (环境特定配置，覆盖 base)
3. `${VAR_NAME}` 占位符替换为环境变量值
4. `WIZYELAB_*` 环境变量覆盖

**切换环境**:
```bash
# 通过环境变量设置
export WIZYELAB_ENV=dev      # 开发环境 (默认)
export WIZYELAB_ENV=staging  # 预上线环境
export WIZYELAB_ENV=prod     # 生产环境

# 或使用 ENV 变量
export ENV=prod
```

### 配置项

| 配置项 | 说明 |
|--------|------|
| `server` | 服务器配置（host, port, reload, workers, log_level）|
| `app` | 应用配置（name, version, debug, api_prefix）|
| `database` | PolarDB/MySQL 数据库配置 |
| `redis` | Redis/Tair 缓存配置 |
| `oss` | 阿里云 OSS 对象存储配置 |
| `llm` | LLM 配置（OpenAI API）|
| `agent` | Agent 配置 |
| `logging` | 日志配置 |
| `monitoring` | 监控配置（Prometheus, OpenTelemetry）|
| `rate_limit` | 限流配置 |
| `cache` | 缓存配置 |
| `cors` | CORS 配置 |

### 环境变量

配置可以通过环境变量覆盖，支持两种方式：

**1. 在配置文件中使用占位符**:
```yaml
database:
  password: "${WIZYELAB_DATABASE_PASSWORD}"  # 从环境变量读取
oss:
  access_key_id: "${WIZYELAB_OSS_ACCESS_KEY_ID}"
  access_key_secret: "${WIZYELAB_OSS_ACCESS_KEY_SECRET}"
```

**2. 使用 WIZYELAB_ 前缀覆盖配置**:
```bash
WIZYELAB_DATABASE_HOST=localhost
WIZYELAB_REDIS_HOST=localhost
WIZYELAB_LLM_API_KEY=your-api-key
WIZYELAB_OSS_ACCESS_KEY_ID=your-access-key-id
WIZYELAB_OSS_ACCESS_KEY_SECRET=your-access-key-secret
```

### OSS 配置

阿里云 OSS 对象存储配置：
```yaml
oss:
  access_key_id: "${WIZYELAB_OSS_ACCESS_KEY_ID}"
  access_key_secret: "${WIZYELAB_OSS_ACCESS_KEY_SECRET}"
  endpoint: "oss-cn-hangzhou.aliyuncs.com"
  bucket_name: "wizyelab-dev"
  internal_endpoint: ""  # 内网 endpoint（可选）
  use_https: true
  upload:
    multipart_threshold: 10485760  # 10MB，超过使用分片上传
    part_size: 10485760
    num_threads: 4
  download:
    multipart_threshold: 10485760
    part_size: 10485760
    num_threads: 4
  url_expire_seconds: 3600  # 签名 URL 过期时间
```

## 运行

### 开发模式

```bash
python main.py
```

或者使用 uvicorn 直接运行：

```bash
uvicorn main:app --reload
```

### 生产模式

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API 文档

启动服务后，访问以下地址查看 API 文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 路由

### 系统路由

| 路由 | 说明 |
|------|------|
| `/` | 根路径 |
| `/health` | 健康检查（详细） |
| `/livez` | 存活检查 |
| `/readyz` | 就绪检查 |
| `/metrics` | Prometheus 指标 |

### 业务 API

| 路由 | 说明 |
|------|------|
| `/api/v1/public/*` | 对外公开 API |
| `/api/v1/internal/*` | 内部 API |

### 文件存储 API

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/public/files/upload` | POST | 上传单个文件 |
| `/api/v1/public/files/upload/batch` | POST | 批量上传文件 |
| `/api/v1/public/files/download/{key}` | GET | 下载文件 |
| `/api/v1/public/files/info/{key}` | GET | 获取文件信息 |
| `/api/v1/public/files/{key}` | DELETE | 删除文件 |
| `/api/v1/public/files/delete/batch` | POST | 批量删除文件 |
| `/api/v1/public/files/list` | GET | 列举文件 |
| `/api/v1/public/files/signed-url` | POST | 获取签名 URL |
| `/api/v1/public/files/upload-url` | POST | 获取直传 URL |
| `/api/v1/public/files/exists/{key}` | GET | 检查文件是否存在 |

**上传文件示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/public/files/upload" \
  -F "file=@/path/to/image.jpg" \
  -F "prefix=uploads"
```

**获取直传 URL（客户端直传）**:
```bash
curl -X POST "http://localhost:8000/api/v1/public/files/upload-url" \
  -H "Content-Type: application/json" \
  -d '{"filename": "photo.jpg", "prefix": "uploads"}'
```

## LLM Agent 使用

```python
from app.services.llm import create_agent, get_agent

# 创建 Agent
agent = create_agent(session_id="user_123")

# 对话
response = await agent.chat("推荐一款适合初学者的网球拍")
print(response)

# 流式对话
async for chunk in agent.chat_stream("分析我的网球挥拍动作"):
    print(chunk, end="")
```

## OSS 服务使用

```python
from app.services.storage import oss_service

# 上传文件
result = await oss_service.upload_file(file, prefix="uploads")
print(result.url)

# 下载文件
content = await oss_service.download_file("uploads/images/2024/01/15/abc123.jpg")

# 获取签名 URL
url = oss_service.get_signed_url("path/to/file.pdf", expires=3600)

# 生成直传 URL
upload_url = oss_service.get_upload_url("path/to/upload.jpg")
```

## 监控

### Prometheus 指标

访问 `/metrics` 端点获取 Prometheus 格式的指标：

| 指标 | 说明 |
|------|------|
| `http_requests_total` | HTTP 请求总数 |
| `http_request_duration_seconds` | HTTP 请求延迟 |
| `http_requests_active` | 活跃请求数 |
| `agent_calls_total` | Agent 调用次数 |
| `agent_call_duration_seconds` | Agent 调用延迟 |
| `llm_calls_total` | LLM 调用次数 |
| `llm_tokens_total` | LLM Token 使用量 |
| `cache_hits_total` | 缓存命中次数 |
| `cache_misses_total` | 缓存未命中次数 |

### 健康检查

| 端点 | 说明 |
|------|------|
| `/health` | 详细健康状态（包含各组件状态） |
| `/livez` | 简单存活检查 |
| `/readyz` | 就绪检查 |

## 测试

```bash
poetry run pytest
```

## 开发

### 代码格式化

```bash
poetry run black .
```

### 类型检查

```bash
poetry run mypy .
```

### 代码检查

```bash
poetry run flake8
```

## Docker 部署

### 本地开发

本地开发无需 Docker，直接使用 Poetry 运行：

```bash
# 安装依赖
poetry install

# 运行服务
python main.py
```

### 云部署

项目使用统一的 `docker-compose.cloud.yml` 配置文件，通过不同的环境变量文件区分 staging 和 production 环境。

**Staging 部署**:
```bash
# 使用 staging 环境配置
docker-compose -f docker-compose.cloud.yml --env-file .env.staging up -d
```

**Production 部署**:
```bash
# 使用 production 环境配置
docker-compose -f docker-compose.cloud.yml --env-file .env.prod up -d
```

**环境配置差异**:

| 配置项 | Staging | Production |
|--------|---------|------------|
| CPU 限制 | 2 核 | 4 核 |
| 内存限制 | 2G | 4G |
| 副本数 | 1 | 2 |
| 日志大小 | 100m x 3 | 200m x 5 |
| 重启策略 | unless-stopped | always |

### 单独构建镜像

```bash
# 构建镜像
docker build -t wizyelab-web-start .

# 运行容器
docker run -d -p 8000:8000 \
  -e WIZYELAB_ENV=dev \
  -e WIZYELAB_REDIS_HOST=host.docker.internal \
  wizyelab-web-start
```

## CI/CD

项目使用 GitHub Actions 实现自动化 CI/CD。

### CI 工作流 (`.github/workflows/ci.yml`)

| 任务 | 说明 |
|------|------|
| **lint** | Black 格式检查 + Flake8 代码检查 |
| **type-check** | MyPy 类型检查 |
| **test** | Pytest 运行测试（含 Redis 服务） |
| **security** | Bandit 安全扫描 |

**触发条件**：push 到 main/develop 分支，或 Pull Request

### CD 工作流 (`.github/workflows/cd.yml`)

| 任务 | 说明 |
|------|------|
| **build** | 构建 Docker 镜像并推送到阿里云 ACR |
| **deploy-staging** | 部署到预上线环境 |
| **deploy-prod** | 部署到生产环境（需要 tag） |

**触发条件**：
- 推送到 main 分支 → 部署到 staging
- 推送 v* 标签 → 部署到 production
- 手动触发 → 选择部署环境

### 需要配置的 Secrets

| Secret | 说明 |
|--------|------|
| `ACR_USERNAME` | 阿里云 ACR 用户名 |
| `ACR_PASSWORD` | 阿里云 ACR 密码 |
| `STAGING_HOST` | Staging 服务器地址 |
| `STAGING_USER` | Staging SSH 用户 |
| `STAGING_SSH_KEY` | Staging SSH 私钥 |
| `PROD_HOST` | 生产服务器地址 |
| `PROD_USER` | 生产 SSH 用户 |
| `PROD_SSH_KEY` | 生产 SSH 私钥 |

### 部署流程

```
代码推送 → CI 检查 → 构建镜像 → 推送 ACR → SSH 部署 → 健康检查
```

## 架构特点

- **分层架构**: api → services → infrastructure，职责清晰
- **多环境支持**: 灵活的配置管理，支持 dev/staging/prod
- **异步优先**: 全异步支持（FastAPI + SQLAlchemy 2.0 + aioredis）
- **完整监控**: Prometheus 指标 + 健康检查 + 结构化日志
- **AI 集成**: LangChain Agent + 工具系统 + 对话记忆
- **对象存储**: 阿里云 OSS 集成，支持分片上传/下载

## 框架能力

### 1. 数据库连接 (`app/infrastructure/database/`)

**特性**:
- **双模式支持**: 同步和异步数据库操作
- **SQLAlchemy 2.0**: 完整的异步支持
- **延迟初始化**: 异步引擎在事件循环启动后初始化，避免事件循环绑定问题
- **NullPool**: 异步引擎使用 NullPool，解决多 worker 模式下的事件循环不匹配问题
- **连接池管理**: 同步引擎使用 QueuePool，支持连接健康检查 (pool_pre_ping)
- **依赖注入**: 支持 FastAPI 依赖注入和上下文管理器两种使用方式

**使用示例**:
```python
from app.infrastructure.database.connection import get_async_db
from fastapi import Depends

@app.get("/users")
async def get_users(db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(User))
    return result.scalars().all()
```

### 2. Redis 客户端 (`app/infrastructure/cache/`)

**特性**:
- **自动重连机制**: 连接失败时自动重试，带锁防止并发重连
- **连接健康监控**: health_check_interval=30，自动检测并重建断开的连接
- **全面的操作支持**:
  - 基本操作: get, set, delete, exists, expire, ttl
  - JSON 操作: get_json, set_json (自动序列化)
  - 缓存操作: cache_get, cache_set, cache_delete, cache_clear_pattern (带前缀)
  - Hash 操作: hget, hset, hgetall, hdel
  - List 操作: lpush, rpush, lpop, rpop, lrange, llen
  - Set 操作: sadd, srem, smembers, sismember
  - 计数器: incr, decr
  - 发布订阅: publish, subscribe
- **分布式锁**: 上下文管理器支持，自动获取和释放锁
- **线程安全**: 使用 asyncio.Lock 确保重连过程的线程安全

**使用示例**:
```python
from app.infrastructure.cache.redis_client import redis_client

# 基本操作
await redis_client.set("key", "value", ex=3600)
value = await redis_client.get("key")

# JSON 缓存
await redis_client.cache_set("user:123", {"name": "Alice"}, ttl=3600)
user = await redis_client.cache_get("user:123")

# 分布式锁
async with redis_client.lock("my_lock", timeout=10):
    # 执行需要加锁的操作
    pass
```

### 3. 对象存储 (`app/infrastructure/storage/`)

**特性**:
- **阿里云 OSS 集成**: 完整的 OSS 操作支持
- **上传操作**: 简单上传、分片上传、批量上传、签名 URL
- **下载操作**: 简单下载、断点续传、批量下载
- **对象管理**: 元数据查询、删除、复制、列举
- **CORS 配置**: 支持跨域资源共享配置
- **线程池执行**: 异步操作使用线程池，不阻塞事件循环

### 4. 监控与可观测性 (`app/infrastructure/monitoring/`)

**特性**:
- **Prometheus 指标**: 自动收集 HTTP 请求、Agent 调用、LLM 使用、缓存命中等指标
- **健康检查**:
  - `/health`: 详细健康状态（包含数据库、Redis、LLM 组件状态）
  - `/livez`: 简单存活检查
  - `/readyz`: 就绪检查（503 如果不健康）
- **结构化日志**: JSON 格式日志，包含 trace_id 用于分布式追踪
- **请求追踪**: 基于 Snowflake 算法的 trace_id，支持跨服务追踪

### 5. 配置管理 (`app/core/config.py`)

**特性**:
- **多环境支持**: dev, staging, prod
- **分层配置**:
  1. base.yaml (共享默认值)
  2. {env}.yaml (环境特定配置)
  3. 环境变量替换 (`${VAR_NAME}`)
  4. WIZYELAB_* 前缀覆盖
- **类型安全**: 基于 Pydantic 的配置验证
- **深度合并**: 环境配置自动覆盖基础配置

### 6. 中间件系统 (`app/middleware/`)

**特性**:
- **请求上下文**: 全局请求上下文（ContextVar），包含 trace_id、user_id、session_id 等
- **会话管理**: 双通道支持（Header + Cookie），适配移动端和 Web 端
- **认证执行**: 可配置的公开路径白名单，自动 401 响应
- **限流**: 基于 Redis 的分布式限流，支持滑动窗口算法
- **请求日志**: 自动记录请求/响应，包含性能指标

### 7. Snowflake ID 生成器 (`app/core/snowflake.py`)

**特性**:
- **分布式唯一 ID**: 64 位结构（时间戳 + 数据中心 ID + 工作节点 ID + 序列号）
- **线程安全**: 单例模式 + 锁机制
- **时钟偏移检测**: 防止时钟回拨导致 ID 重复
- **高吞吐**: 每毫秒 4096 个 ID
- **趋势递增**: 适合数据库索引

## 生产就绪特性

### 高可用性
- ✅ Redis 自动重连机制
- ✅ 数据库连接池健康检查
- ✅ 多 worker 模式支持（事件循环隔离）
- ✅ 优雅关闭（lifespan 管理）

### 可观测性
- ✅ Prometheus 指标收集
- ✅ 结构化 JSON 日志
- ✅ 分布式追踪（trace_id）
- ✅ 健康检查端点

### 安全性
- ✅ 会话管理（Redis 存储）
- ✅ 认证中间件
- ✅ 限流保护
- ✅ CORS 配置

### 性能
- ✅ 全异步架构
- ✅ 连接池管理
- ✅ 缓存支持
- ✅ 分布式锁

## 许可证

MIT
