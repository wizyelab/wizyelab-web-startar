# 基础设施组件文档

## 概述

本文档详细说明 Wizyelab Web Start 项目的基础设施层组件，这些组件为应用提供核心的基础服务支持。

## 组件列表

### 1. 数据库连接 (`app/infrastructure/database/`)

#### 特性

- **双模式支持**: 同步和异步数据库操作
- **SQLAlchemy 2.0**: 完整的异步支持，使用 aiomysql 驱动
- **延迟初始化**: 异步引擎在事件循环启动后初始化，避免事件循环绑定问题
- **NullPool 策略**: 异步引擎使用 NullPool，解决多 worker 模式下的事件循环不匹配问题
- **连接池管理**: 同步引擎使用 QueuePool，支持连接健康检查 (pool_pre_ping)
- **依赖注入**: 支持 FastAPI 依赖注入和上下文管理器两种使用方式
- **事件监听**: 连接生命周期事件监听（connect, checkout, checkin）

#### 为什么需要延迟初始化？

在多 worker 模式下（如 `uvicorn --workers 4`），每个 worker 进程有自己的事件循环。如果在模块加载时创建异步引擎，它会绑定到主进程的事件循环，导致 worker 进程中使用时出现 "attached to a different loop" 错误。

**解决方案**: 在 FastAPI lifespan 中调用 `init_async_engine()`，确保每个 worker 进程在自己的事件循环中创建引擎。

#### 为什么使用 NullPool？

NullPool 禁用连接池，每次操作创建新连接。虽然性能略低，但避免了连接跨事件循环复用的问题，确保多 worker 模式下的稳定性。

**权衡**: 稳定性 > 性能。对于大多数应用，数据库操作不是瓶颈。

#### 使用示例

**FastAPI 依赖注入**:
```python
from app.infrastructure.database.connection import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

@app.get("/users")
async def get_users(db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(User))
    return result.scalars().all()
```

**上下文管理器**:
```python
from app.infrastructure.database.connection import get_async_db_context

async with get_async_db_context() as db:
    result = await db.execute(select(User))
    users = result.scalars().all()
    # 自动 commit
```

**初始化**:
```python
# 在 main.py lifespan 中
from app.infrastructure.database.connection import init_async_engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 必须在事件循环运行后调用
    await init_async_engine()
    yield
    await close_db()
```

---

### 2. Redis 客户端 (`app/infrastructure/cache/`)

#### 特性

- **自动重连机制**: 连接失败时自动重试，带锁防止并发重连
- **连接健康监控**: `health_check_interval=30`，自动检测并重建断开的连接
- **重试配置**: `retry_on_timeout=True`，超时自动重试
- **全面的操作支持**:
  - **基本操作**: get, set, delete, exists, expire, ttl
  - **JSON 操作**: get_json, set_json (自动序列化/反序列化)
  - **缓存操作**: cache_get, cache_set, cache_delete, cache_clear_pattern (带前缀)
  - **Hash 操作**: hget, hset, hgetall, hdel
  - **List 操作**: lpush, rpush, lpop, rpop, lrange, llen
  - **Set 操作**: sadd, srem, smembers, sismember
  - **计数器**: incr, decr
  - **发布订阅**: publish, subscribe
- **分布式锁**: 上下文管理器支持，自动获取和释放锁
- **线程安全**: 使用 `asyncio.Lock` 确保重连过程的线程安全

#### 自动重连机制

**工作原理**:
1. 检测连接错误（"closed", "connection", "handler" 关键词）
2. 使用 `asyncio.Lock` 防止并发重连
3. 检查连接是否已恢复（其他协程可能已重连）
4. 优雅关闭旧连接（带超时）
5. 等待 0.1 秒确保连接完全关闭
6. 重新初始化连接池
7. 最多重试 2 次

**收益**:
- ✅ 网络抖动自动恢复
- ✅ Redis 重启无需重启服务
- ✅ 防止雷鸣群效应（并发重连）

#### 使用示例

**基本操作**:
```python
from app.infrastructure.cache.redis_client import redis_client

# 设置值（带过期时间）
await redis_client.set("key", "value", ex=3600)

# 获取值（自动重连）
value = await redis_client.get("key")

# 删除键
await redis_client.delete("key1", "key2")
```

**JSON 缓存**:
```python
# 设置 JSON 对象
user_data = {"id": 123, "name": "Alice", "email": "alice@example.com"}
await redis_client.cache_set("user:123", user_data, ttl=3600)

# 获取 JSON 对象
user = await redis_client.cache_get("user:123")
print(user["name"])  # Alice

# 清除匹配模式的缓存
await redis_client.cache_clear_pattern("user:*")
```

**分布式锁**:
```python
# 使用上下文管理器
async with redis_client.lock("my_lock", timeout=10, blocking_timeout=5.0):
    # 执行需要加锁的操作
    # 锁会在退出时自动释放
    await do_critical_operation()
```

**Hash 操作**:
```python
# 设置 Hash 字段
await redis_client.hset("user:123", "name", "Alice")
await redis_client.hset("user:123", "age", "25")

# 获取 Hash 字段
name = await redis_client.hget("user:123", "name")

# 获取整个 Hash
user = await redis_client.hgetall("user:123")
```

**计数器**:
```python
# 增加计数
count = await redis_client.incr("page_views")

# 减少计数
count = await redis_client.decr("inventory:item_123")
```

---

### 3. 对象存储 (`app/infrastructure/storage/`)

#### 特性

- **阿里云 OSS 集成**: 完整的 OSS 操作支持
- **上传操作**:
  - 简单上传: `put_object`, `put_object_from_file`
  - 分片上传: `multipart_upload` (大文件)
  - 智能上传: `upload_file` (自动选择简单/分片)
  - 批量上传: 支持多文件上传
  - 签名 URL: 客户端直传
- **下载操作**:
  - 简单下载: `get_object`, `get_object_to_file`
  - 断点续传: `resumable_download`
  - 智能下载: `download_file` (自动选择)
- **对象管理**:
  - 元数据查询: `head_object`, `object_exists`
  - 删除: `delete_object`, `batch_delete_objects`
  - 复制: `copy_object`
  - 列举: `list_objects`, `list_objects_v2`
- **CORS 配置**: 支持跨域资源共享配置
- **线程池执行**: 异步操作使用线程池，不阻塞事件循环

#### 使用示例

**上传文件**:
```python
from app.services.storage import oss_service

# 上传文件（自动选择简单/分片上传）
result = await oss_service.upload_file(
    file=file,  # UploadFile 对象
    prefix="uploads/images"
)
print(result.url)  # 文件访问 URL
```

**下载文件**:
```python
# 下载文件内容
content = await oss_service.download_file("uploads/images/photo.jpg")

# 保存到本地
await oss_service.download_file_to_path(
    "uploads/images/photo.jpg",
    "/tmp/photo.jpg"
)
```

**签名 URL**:
```python
# 生成下载签名 URL（1小时有效）
download_url = oss_service.get_signed_url(
    "uploads/document.pdf",
    expires=3600
)

# 生成上传签名 URL（客户端直传）
upload_url = oss_service.get_upload_url(
    "uploads/photo.jpg",
    expires=300
)
```

---

### 4. 监控与可观测性 (`app/infrastructure/monitoring/`)

#### 特性

- **Prometheus 指标**: 自动收集应用指标
  - HTTP 指标: 请求总数、延迟、活跃请求、请求/响应大小
  - 应用指标: Agent 调用、LLM 使用、数据库连接、Redis 连接、缓存命中
- **健康检查**:
  - `/health`: 详细健康状态（包含数据库、Redis、LLM 组件状态）
  - `/livez`: 简单存活检查
  - `/readyz`: 就绪检查（503 如果不健康）
- **结构化日志**: JSON 格式日志，包含 trace_id 用于分布式追踪
- **请求追踪**: 基于 Snowflake 算法的 trace_id，支持跨服务追踪

#### Prometheus 指标列表

| 指标名称 | 类型 | 说明 |
|---------|------|------|
| `http_requests_total` | Counter | HTTP 请求总数（按 method, endpoint, status） |
| `http_request_duration_seconds` | Histogram | HTTP 请求延迟分布 |
| `http_requests_active` | Gauge | 当前活跃请求数 |
| `http_request_size_bytes` | Histogram | HTTP 请求大小 |
| `http_response_size_bytes` | Histogram | HTTP 响应大小 |
| `agent_calls_total` | Counter | Agent 调用次数 |
| `agent_call_duration_seconds` | Histogram | Agent 调用延迟 |
| `llm_calls_total` | Counter | LLM 调用次数 |
| `llm_tokens_total` | Counter | LLM Token 使用量 |
| `db_connections_active` | Gauge | 数据库活跃连接数 |
| `redis_connections_active` | Gauge | Redis 活跃连接数 |
| `cache_hits_total` | Counter | 缓存命中次数 |
| `cache_misses_total` | Counter | 缓存未命中次数 |

#### 使用示例

**记录 Agent 调用**:
```python
from app.infrastructure.monitoring.metrics import record_agent_call

start_time = time.time()
try:
    result = await agent.chat(message)
    record_agent_call(
        agent_type="wizyelab",
        duration=time.time() - start_time,
        success=True
    )
except Exception as e:
    record_agent_call(
        agent_type="wizyelab",
        duration=time.time() - start_time,
        success=False
    )
    raise
```

**记录缓存访问**:
```python
from app.infrastructure.monitoring.metrics import record_cache_access

value = await redis_client.cache_get("key")
if value:
    record_cache_access(hit=True)
else:
    record_cache_access(hit=False)
```

**健康检查响应示例**:
```json
{
  "status": "healthy",
  "timestamp": "2026-02-07T10:30:00Z",
  "components": {
    "database": {
      "status": "healthy",
      "latency_ms": 5.2
    },
    "redis": {
      "status": "healthy",
      "latency_ms": 1.8
    },
    "llm": {
      "status": "healthy"
    }
  }
}
```

---

### 5. 配置管理 (`app/core/config.py`)

#### 特性

- **多环境支持**: dev, staging, prod
- **分层配置**:
  1. `base.yaml` - 共享默认值
  2. `{env}.yaml` - 环境特定配置
  3. 环境变量替换 (`${VAR_NAME}`)
  4. `WIZYELAB_*` 前缀覆盖
- **类型安全**: 基于 Pydantic 的配置验证
- **深度合并**: 环境配置自动覆盖基础配置
- **自动类型转换**: 字符串自动转换为 bool/int/float

#### 配置加载顺序

```
base.yaml
    ↓
{env}.yaml (覆盖)
    ↓
${VAR_NAME} 替换
    ↓
WIZYELAB_* 环境变量覆盖
    ↓
最终配置
```

#### 使用示例

**访问配置**:
```python
from app.core.config import settings

# 数据库配置
db_url = settings.database_url
pool_size = settings.database.pool_size

# Redis 配置
redis_host = settings.redis.host
redis_port = settings.redis.port

# 应用配置
app_name = settings.app.name
debug_mode = settings.app.debug
```

**环境变量覆盖**:
```bash
# 方式 1: 在配置文件中使用占位符
# configs/prod.yaml
database:
  password: "${WIZYELAB_DATABASE_PASSWORD}"

# 方式 2: 直接覆盖
export WIZYELAB_DATABASE_HOST=prod-db.example.com
export WIZYELAB_REDIS_HOST=prod-redis.example.com
```

---

### 6. 中间件系统 (`app/middleware/`)

#### 特性

- **请求上下文**: 全局请求上下文（ContextVar），包含 trace_id、user_id、session_id 等
- **会话管理**: 双通道支持（Header + Cookie），适配移动端和 Web 端
- **认证执行**: 可配置的公开路径白名单，自动 401 响应
- **限流**: 基于 Redis 的分布式限流，支持滑动窗口算法
- **请求日志**: 自动记录请求/响应，包含性能指标
- **CORS**: 跨域资源共享配置

#### 请求上下文

**可用字段**:
- `request_id`: 请求唯一 ID
- `trace_id`: 分布式追踪 ID（Snowflake）
- `span_id`: Span ID
- `user_id`: 当前用户 ID
- `device_id`: 设备 ID
- `session_id`: 会话 ID
- `client_ip`: 客户端 IP
- `user_agent`: User-Agent
- `platform`: 平台（iOS/Android/Web）
- `app_version`: 应用版本

**使用示例**:
```python
from app.middleware.request_context import get_request_context, get_user_id

# 获取完整上下文
ctx = get_request_context()
print(ctx.trace_id)
print(ctx.user_id)

# 获取当前用户 ID
user_id = get_user_id()  # 返回 Optional[int]
```

---

### 7. Snowflake ID 生成器 (`app/core/snowflake.py`)

#### 特性

- **分布式唯一 ID**: 64 位结构
  - 时间戳: 41 位（毫秒级，可用 69 年）
  - 数据中心 ID: 5 位（支持 32 个数据中心）
  - 工作节点 ID: 5 位（每个数据中心 32 个节点）
  - 序列号: 12 位（每毫秒 4096 个 ID）
- **线程安全**: 单例模式 + 锁机制
- **时钟偏移检测**: 防止时钟回拨导致 ID 重复
- **高吞吐**: 每毫秒 4096 个 ID，每秒 409 万个 ID
- **趋势递增**: 适合数据库索引，查询性能好

#### 使用示例

```python
from app.core.snowflake import generate_id, generate_id_str

# 生成 ID（整数）
user_id = generate_id()  # 1234567890123456789

# 生成 ID（字符串）
session_id = generate_id_str()  # "1234567890123456789"

# 解析 ID
from app.core.snowflake import snowflake_generator
timestamp, datacenter_id, worker_id, sequence = snowflake_generator.parse(user_id)
```

---

## 最佳实践

### 1. 数据库操作

**✅ 推荐**:
```python
# 使用依赖注入
@app.get("/users")
async def get_users(db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(User))
    return result.scalars().all()
```

**❌ 不推荐**:
```python
# 直接使用 AsyncSessionLocal（未初始化检查）
async with AsyncSessionLocal() as db:
    ...
```

### 2. Redis 操作

**✅ 推荐**:
```python
# 使用 cache_* 方法（自动添加前缀）
await redis_client.cache_set("user:123", user_data)
user = await redis_client.cache_get("user:123")
```

**❌ 不推荐**:
```python
# 手动管理前缀
await redis_client.set(f"{prefix}:user:123", json.dumps(user_data))
```

### 3. 错误处理

**✅ 推荐**:
```python
try:
    value = await redis_client.get("key")
except Exception as e:
    logger.error(f"Redis error: {e}")
    # 自动重连会处理连接错误
    # 其他错误需要处理
```

### 4. 监控指标

**✅ 推荐**:
```python
# 记录业务指标
from app.infrastructure.monitoring.metrics import record_agent_call

start = time.time()
try:
    result = await agent.chat(message)
    record_agent_call("wizyelab", time.time() - start, True)
except Exception:
    record_agent_call("wizyelab", time.time() - start, False)
    raise
```

---

## 故障排查

### 数据库连接错误

**错误**: `RuntimeError: Async database engine not initialized`

**原因**: 异步引擎未初始化

**解决**: 确保在 `main.py` lifespan 中调用 `init_async_engine()`

### Redis 连接失败

**错误**: `ConnectionError: Error while reading from socket`

**原因**: Redis 连接断开

**解决**: 自动重连机制会处理，无需手动干预。如果持续失败，检查 Redis 服务状态。

### 多 worker 模式错误

**错误**: `RuntimeError: Task attached to a different loop`

**原因**: 异步引擎绑定到错误的事件循环

**解决**: 使用延迟初始化 + NullPool（已实现）

---

## 性能优化建议

### 1. 数据库

- ✅ 使用索引优化查询
- ✅ 批量操作使用 `bulk_insert_mappings`
- ✅ 避免 N+1 查询，使用 `joinedload`
- ⚠️ NullPool 模式性能略低，但稳定性更好

### 2. Redis

- ✅ 使用 pipeline 批量操作
- ✅ 设置合理的 TTL，避免内存溢出
- ✅ 使用 Hash 存储结构化数据
- ✅ 缓存热点数据

### 3. OSS

- ✅ 大文件使用分片上传/下载
- ✅ 使用 CDN 加速访问
- ✅ 客户端直传减轻服务器压力
- ✅ 设置合理的 CORS 策略

---

## 总结

本项目的基础设施层提供了生产就绪的核心能力：

- ✅ **高可用性**: Redis 自动重连、数据库连接池健康检查
- ✅ **可扩展性**: 多 worker 支持、分布式 ID 生成
- ✅ **可观测性**: Prometheus 指标、健康检查、结构化日志
- ✅ **安全性**: 会话管理、认证中间件、限流保护
- ✅ **性能**: 全异步架构、连接池管理、缓存支持

这些能力确保了系统在生产环境中的稳定运行。
