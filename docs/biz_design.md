# Joiiee 业务架构分析文档

## 一、项目概述

### 1.1 业务方向和定位

#### 目标人群
**Persona**: 湾区20-40岁中高产elites
- 良好的教育背景
- 丰富的兴趣爱好
- 有钱有闲支持自己的兴趣消费

#### 使用场景
1. 兴趣的购买决策
2. 兴趣的进阶提升
3. 基于兴趣的身份认同与归属感满足

#### 产品定位
- **切口(for用户)**: 网球系消费决策与成长 Agent — 帮你买对装备，快速进阶，找到同好
- **GTM一句话心智**: 装备攻略joiiee做，成长路径joiiee拆，兴趣同好joiiee找
- **终局定位**: AI 时代的泛兴趣"消费、成长、连接"社区

#### 投资人视角
> 从网球系这一趋势运动，高意图场景切入：用"可解释的装备决策引擎 + 视频模态为主驱动的成长反馈闭环"占住用户关键时刻（买/练/晒）。过程中用户的配置、视频与成长轨迹可结构化为兴趣图谱并沉淀为社区的UGC资产，形成决策—内容—社区—交易飞轮；终局扩展为跨兴趣的消费成长与社区网络

#### 愿景
让每个人更轻松地投入热爱：少踩坑、少花冤枉钱、有成长，在真实世界里找到兴趣同好

---

## 二、系统架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    客户端层 (Flutter iOS)                        │
├─────────────────────────────────────────────────────────────────┤
│                    API网关层 (Python FastAPI)                    │
├─────────────────────────────────────────────────────────────────┤
│                         业务服务层                               │
│  ┌───────────┬───────────┬───────────┬───────────┬───────────┐ │
│  │ 用户服务    │ 内容服务   │ 社交服务   │ AI对话服务  │ 推荐服务    │ │
│  └───────────┴───────────┴───────────┴───────────┴───────────┘ │
├─────────────────────────────────────────────────────────────────┤
│                          数据层                                  │
│  ┌───────────┬───────────┬───────────┬───────────┐             │
│  │ PostgreSQL│   Redis   │ 向量数据库  │ 对象存储   │             │
│  └───────────┴───────────┴───────────┴───────────┘             │
├─────────────────────────────────────────────────────────────────┤
│                        AI能力层                                  │
│  ┌───────────┬───────────┬───────────┬───────────┐             │
│  │ 推荐引擎   │ 视频理解    │ 骨架识别    │ 内容生成   │             │
│  └───────────┴───────────┴───────────┴───────────┘             │
├─────────────────────────────────────────────────────────────────┤
│                      数据采集层 (爬虫系统)                        │
│  ┌───────────┬───────────┬───────────┐                         │
│  │  YouTube  │  Amazon   │  Reddit   │                         │
│  └───────────┴───────────┴───────────┘                         │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 技术栈

| 层级 | 技术选型 |
|------|----------|
| 后端框架 | Python 3.10+, FastAPI |
| 数据库 | PostgreSQL + SQLAlchemy |
| 缓存 | Redis |
| 认证 | Firebase Auth (Google/Apple登录) |
| 邮件服务 | SMTP (aiosmtplib) |
| 客户端 | Flutter 3.x, Dart |
| AI/ML | PyTorch, MediaPipe, FAISS |
| 爬虫 | Scrapy, Selenium, PRAW |

---

## 三、核心业务流程

### 3.1 登录注册流程时序图

```
┌────┐          ┌────┐            ┌──────────┐       ┌───────────┐      ┌─────────────┐
│User│          │App │            │Web Server│       │Firebase   │      │Third Server │
└──┬─┘          └──┬─┘            └────┬─────┘       └─────┬─────┘      └──────┬──────┘
   │  选择登录方式   │                   │                   │                   │
   │───────────────>│                  │                   │                   │
   │                │                  │                   │                   │
   │ 显示登录方式     │                  │                   │                   │
   │<───────────────│                  │                   │                   │
   │                │                  │                   │                   │
   ├────────────────┴──────────────────┴───────────────────┴───────────────────┤
   │ [Opt] 第三方登录 (Google/Apple)                                             │
   ├───────────────────────────────────────────────────────────────────────────┤
   │                │ 请求授权URL       │                   │                   │
   │                │─────────────────────────────────────────────────────────>│
   │                │                  │                   │    登录并授权       │
   │                │                  │                   │<──────────────────│
   │                │     返回idToken  │                   │                    │
   │                │<─────────────────────────────────────────────────────────│
   │                │                  │                   │                   │
   │                │ 携带idToken进行auth认证               │                    │
   │                │─────────────────>│                   │                   │
   │                │                  │ 验证idToken       │                    │
   │                │                  │──────────────────>│                   │
   │                │                  │ 解析用户信息       │                    │
   │                │                  │<──────────────────│                   │
   ├────────────────┴──────────────────┴───────────────────┴───────────────────┤
   │ [Opt] 邮箱登录                                                            │
   ├───────────────────────────────────────────────────────────────────────────┤
   │                │    邮箱登录       │                   │                   │
   │                │─────────────────>│                   │                   │
   │  发送验证码    │                  │                   │                   │
   │<───────────────│                  │                   │                   │
   │                │                  │                   │                   │
   │  填写验证码    │                  │                   │                   │
   │───────────────>│                  │                   │                   │
   │                │  验证码验证       │                   │                   │
   │                │─────────────────>│                   │                   │
   │                │                  │       校验        │                   │
   │                │                  │────┐              │                   │
   │                │                  │<───┘              │                   │
   ├────────────────┴──────────────────┴───────────────────┴───────────────────┤
   │ 通用流程                                                                  │
   ├───────────────────────────────────────────────────────────────────────────┤
   │                │                  │  查询并创建user    │                   │
   │                │                  │──────────────────>│                   │
   │                │                  │    user信息       │                   │
   │                │                  │<──────────────────│                   │
   │                │                  │                   │                   │
   │                │                  ├───────────────────┤                   │
   │                │                  │ [Opt] 创建自定义token                 │
   │                │                  │──────────────────>│                   │
   │                │                  │      token        │                   │
   │                │                  │<──────────────────│                   │
   │                │                  ├───────────────────┤                   │
   │                │                  │                   │                   │
   │                │ 返回token或用户信息                   │                   │
   │                │<─────────────────│                   │                   │
   │                │                  │                   │                   │
   │ 验证是否登录成功│                  │                   │                   │
   │────┐           │                  │                   │                   │
   │<───┘           │                  │                   │                   │
└──┴─┘          └──┴─┘          └────┴─────┘       └─────┴─────┘      └──────┴──────┘
```

---

## 四、后端接口设计

### 4.1 登录注册模块 (2天)

#### 4.1.1 账户验证接口

**URI**: `POST /joiiee/v1/api/account/verify`

**功能描述**: 
- 支持第三方登录（Google/Apple）验证
- 支持邮箱验证码登录

**请求参数**:

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| id_token | string | 第三方登录token | "" | Google/Apple登录时使用 |
| verify_code | string | 消息验证码 | "" | 6位数字 |
| email | string | 邮箱地址 | "" | 邮箱登录时需要 |
| device_info | Device | 设备信息 | None | |

**Device结构**:

| 字段 | 类型 | 含义 | 默认值 |
|------|------|------|--------|
| device_id | string | 设备ID | "" |

**请求示例**:
```json
{
    "id_token": "wHvurNFEQTZEyUtixTGFwOr1OGh1",
    "verify_code": "016782",
    "email": "user@example.com",
    "device_info": {
        "device_id": "00008150-000E54160C01401C"
    }
}
```

**响应参数**:

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| code | int | 状态码 | 0 | 0:正常, 其他:异常 |
| message | string | 返回信息 | "成功" | |
| data | Data | 数据 | None | |

**Data结构**:

| 字段 | 类型 | 含义 | 默认值 |
|------|------|------|--------|
| custom_token | string | 自定义token | "" |
| user_info | UserInfo | 用户信息 | None |

**UserInfo结构**:

| 字段 | 类型 | 含义 | 默认值 |
|------|------|------|--------|
| user_id | string | 用户ID | "" |
| user_name | string | 用户名称 | "" |
| avatar | string | 头像URL | "" |

**响应示例**:
```json
{
    "code": 0,
    "message": "成功",
    "data": {
        "custom_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
        "user_info": {
            "user_id": "550e8400-e29b-41d4-a716-446655440000",
            "user_name": "joy",
            "avatar": "https://gips1.baidu.com/avatar.png"
        }
    }
}
```

---

#### 4.1.2 发送验证码接口

**URI**: `POST /joiiee/v1/api/account/send_verify_code`

**功能描述**: 发送邮箱验证码

**请求参数**:

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| mail_url | string | 邮箱地址 | "" | 必填 |
| device_info | Device | 设备信息 | None | |

**请求示例**:
```json
{
    "mail_url": "koydance@126.com",
    "device_info": {
        "device_id": "00008150-000E54160C01401C"
    }
}
```

**响应参数**:

| 字段 | 类型 | 含义 | 默认值 |
|------|------|------|--------|
| code | int | 状态码 | 0 |
| message | string | 返回信息 | "成功" |
| data | Data | 数据 | None |

**响应示例**:
```json
{
    "code": 0,
    "message": "成功"
}
```

---

#### 4.1.3 用户登出接口

**URI**: `POST /joiiee/v1/api/account/logout`

**功能描述**: 用户登出，使Token失效

**请求参数**:

| 字段 | 类型 | 含义 | 默认值 |
|------|------|------|--------|
| user_id | string | 用户ID | "" |
| device_info | Device | 设备信息 | None |

**请求示例**:
```json
{
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "device_info": {
        "device_id": "00008150-000E54160C01401C"
    }
}
```

**响应示例**:
```json
{
    "code": 0,
    "message": "成功"
}
```

---

### 4.2 Profile模块 (2天)

#### 4.2.1 更新Profile

**URI**: `PUT /joiiee/v1/api/profile/update`

**请求参数**:

| 字段 | 类型 | 含义 |
|------|------|------|
| name | string | 用户名称 |
| avatar | string | 头像URL |
| interest_tags | array | 兴趣标签 |
| skill_level | string | 技能等级 |

---

#### 4.2.2 获取引导列表

**URI**: `GET /joiiee/v1/api/collect_profile/guide_list`

**功能**: 返回Profile收集引导页的固定内容

---

#### 4.2.3 上传Profile信息

**URI**: `POST /joiiee/v1/api/collect_profile/upload`

**功能**: 上传用户Profile信息（兴趣标签、技能等级等）

---

#### 4.2.4 用户Feed流

**URI**: `GET /joiiee/v1/api/profile/feeds`

**功能**: 获取用户的内容Feed

---

### 4.3 首页模块 (2天)

#### 4.3.1 标签内容列表

**URI**: `GET /joiiee/v1/api/home/tag_content_list`

**请求参数**:

| 字段 | 类型 | 含义 |
|------|------|------|
| tag_id | string | 标签ID |
| page | int | 页码 |
| page_size | int | 每页数量 |

---

#### 4.3.2 广场Feed

**URI**: `GET /joiiee/v1/api/home/square_feed`

**请求参数**:

| 字段 | 类型 | 含义 |
|------|------|------|
| page | int | 页码 |
| page_size | int | 每页数量 |

**返回**: 个性化Feed流，包含推荐理由（证据链）

---

### 4.4 Chat对话模块 (4天)

#### 4.4.1 创建消息

**URI**: `POST /joiiee/v1/api/chat/create_message`

**请求参数**:

| 字段 | 类型 | 含义 |
|------|------|------|
| session_id | string | 会话ID |
| message | string | 消息内容 |
| message_type | string | 消息类型 |

---

#### 4.4.2 更新消息

**URI**: `PUT /joiiee/v1/api/chat/update_message`

---

#### 4.4.3 创建会话

**URI**: `POST /joiiee/v1/api/chat/create_session`

---

#### 4.4.4 更新会话

**URI**: `PUT /joiiee/v1/api/chat/update_session`

---

#### 4.4.5 停止消息生成

**URI**: `POST /joiiee/v1/api/chat/stop_message`

---

### 4.5 用户行为模块 (0.5天)

#### 4.5.1 用户反馈

**URI**: `POST /joiiee/v1/api/feedback/action`

**请求参数**:

| 字段 | 类型 | 含义 |
|------|------|------|
| content_id | string | 内容ID |
| feedback_type | string | 反馈类型(dislike等) |
| reason | string | 原因 |

---

#### 4.5.2 用户分享

**功能**: 生成H5分享链接

---

### 4.6 广场/Profile模块 (1天)

#### 4.6.1 发布内容

**URI**: `POST /joiiee/v1/api/post/`

---

#### 4.6.2 删除内容

**URI**: `POST /joiiee/v1/api/post/{post_id}`

---

### 4.7 详情页模块 (3天)

#### 4.7.1 内容详情

**URI**: `GET /joiiee/v1/api/detail_page/{post_id}`

**返回**: 图片/视频/文本内容，点赞/评论/分享计数

---

#### 4.7.2 评论列表

**URI**: `GET /joiiee/v1/api/comment_list/{post_id}`

---

#### 4.7.3 发表评论

**URI**: `POST /joiiee/v1/api/create_comment`

---

#### 4.7.4 删除评论

**URI**: `DELETE /joiiee/v1/api/delete_comment/{comment_id}`

---

#### 4.7.5 用户操作

**URI**: `POST /joiiee/v1/api/user/action`

**请求参数**:

| 字段 | 类型 | 含义 |
|------|------|------|
| content_id | string | 内容ID |
| action_type | string | 操作类型(like/share/unlike) |

---

## 五、数据库设计

### 5.1 用户相关表

```sql
-- 用户表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    firebase_uid VARCHAR(128) UNIQUE,        -- Firebase UID
    email VARCHAR(255) UNIQUE,               -- 邮箱
    user_name VARCHAR(50),                   -- 用户名
    avatar VARCHAR(500),                     -- 头像URL
    login_provider VARCHAR(20),              -- 登录方式: google/apple/email
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_users_firebase_uid ON users(firebase_uid);
CREATE INDEX idx_users_email ON users(email);

-- 用户设备表
CREATE TABLE user_devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    device_id VARCHAR(100) NOT NULL,
    device_type VARCHAR(20),                 -- ios/android
    device_name VARCHAR(100),
    push_token VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_active_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_user_devices_user_id ON user_devices(user_id);
CREATE INDEX idx_user_devices_device_id ON user_devices(device_id);

-- 用户会话表
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    device_id VARCHAR(100) NOT NULL,
    custom_token TEXT,
    is_valid BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_device_id ON user_sessions(device_id);

-- 用户Profile表
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    interest_tags JSONB,                     -- 兴趣标签
    skill_level VARCHAR(20),                 -- 技能等级
    equipment_config JSONB,                  -- 装备配置
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_user_profiles_user_id ON user_profiles(user_id);
```

### 5.2 内容相关表

```sql
-- 内容表
CREATE TABLE contents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_type VARCHAR(20) NOT NULL,       -- video/image/text/product
    title VARCHAR(200),
    description TEXT,
    media_urls JSONB,
    tags JSONB,
    source VARCHAR(50),                      -- ugc/crawled
    source_platform VARCHAR(50),             -- YouTube/Amazon/Reddit
    crawled_metadata JSONB,
    like_count INT DEFAULT 0,
    comment_count INT DEFAULT 0,
    share_count INT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_contents_content_type ON contents(content_type);
CREATE INDEX idx_contents_created_at ON contents(created_at);

-- 评论表
CREATE TABLE comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_id UUID NOT NULL REFERENCES contents(id),
    user_id UUID NOT NULL REFERENCES users(id),
    parent_comment_id UUID REFERENCES comments(id),
    comment_text TEXT NOT NULL,
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_comments_content_id ON comments(content_id);
CREATE INDEX idx_comments_user_id ON comments(user_id);

-- 用户行为表
CREATE TABLE user_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    content_id UUID NOT NULL REFERENCES contents(id),
    action_type VARCHAR(20) NOT NULL,        -- like/share/collect/view
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_user_actions_user_content ON user_actions(user_id, content_id, action_type);
CREATE INDEX idx_user_actions_content_id ON user_actions(content_id);

-- 用户反馈表
CREATE TABLE user_feedbacks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    content_id UUID NOT NULL REFERENCES contents(id),
    feedback_type VARCHAR(20) NOT NULL,      -- dislike/report/not_interested
    reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 5.3 对话相关表

```sql
-- 对话会话表
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    session_type VARCHAR(50),                -- equipment/training/general
    context_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_chat_sessions_user_id ON chat_sessions(user_id);

-- 对话消息表
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id),
    user_id UUID NOT NULL REFERENCES users(id),
    role VARCHAR(20) NOT NULL,               -- user/assistant
    content TEXT NOT NULL,
    evidence_chain JSONB,                    -- 推荐证据链
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_chat_messages_session_id ON chat_messages(session_id);
```

---

## 六、数据采集爬虫系统

### 6.1 爬虫架构

```
┌────────────────────────────────────────────────┐
│           爬虫调度中心 (Celery)                 │
└────────────────────────────────────────────────┘
         │              │              │
    ┌────▼────┐   ┌────▼────┐   ┌────▼────┐
    │ YouTube │   │ Amazon  │   │ Reddit  │
    │ Spider  │   │ Spider  │   │ Spider  │
    └────┬────┘   └────┬────┘   └────┬────┘
         │              │              │
         └──────────────┼──────────────┘
                        │
                   ┌────▼────┐
                   │数据清洗  │
                   │与入库    │
                   └────┬────┘
                        │
                   ┌────▼────┐
                   │离线模型  │
                   │处理      │
                   └─────────┘
```

### 6.2 数据源

| 平台 | 目标数据 | 技术方案 |
|------|----------|----------|
| YouTube | 网球/Paddle/皮克球视频、评论 | YouTube Data API v3 |
| Amazon | 运动装备商品、描述、图片、评论 | Scrapy + Selenium |
| Reddit | r/tennis, r/padel, r/pickleball帖子、评论 | Reddit API (PRAW) |

### 6.3 爬虫数据表

```sql
-- 爬虫任务表
CREATE TABLE crawl_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_type VARCHAR(20) NOT NULL,          -- youtube/amazon/reddit
    task_config JSONB,
    status VARCHAR(20) NOT NULL,             -- pending/running/success/failed
    next_run_time TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 原始爬取数据表
CREATE TABLE crawled_raw_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES crawl_tasks(id),
    platform VARCHAR(50) NOT NULL,
    data_type VARCHAR(50),                   -- video/product/post/comment
    raw_data JSONB,
    is_processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

---

## 七、AI算法能力

### 7.1 在线能力

#### Feed推荐引擎
- **召回层**: 协同过滤、内容标签、向量相似度、热度召回
- **排序层**: LightGBM/DeepFM排序模型
- **证据链**: 生成可解释的推荐理由

#### 运动骨架分析
- **骨架提取**: MediaPipe/OpenPose提取关键点
- **动作对比**: DTW算法计算相似度
- **纠正建议**: 分析差异点，生成建议

### 7.2 离线能力

#### 内容理解模型
- 视频内容理解与分类
- 关键帧提取
- 时间戳标注
- 自动标签生成

#### 数据处理Pipeline
```
原始数据 → 内容清洗 → 模型理解 → 标签生成 → 质量评分 → 入库
```

### 7.3 AI相关表

```sql
-- 用户视频分析表
CREATE TABLE user_video_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    video_url VARCHAR(500),
    skeleton_data JSONB,                     -- 骨架关键点
    action_type VARCHAR(50),                 -- forehand/backhand/serve
    score FLOAT,
    correction_advice JSONB,
    similar_standard_videos JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 标准动作库
CREATE TABLE standard_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    action_type VARCHAR(50),
    action_name VARCHAR(100),
    skeleton_template JSONB,
    video_url VARCHAR(500),
    difficulty_level VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 推荐记录表
CREATE TABLE recommendation_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    content_id UUID NOT NULL REFERENCES contents(id),
    scene VARCHAR(50),                       -- feed/search/related
    rank_score FLOAT,
    evidence_chain JSONB,
    is_clicked BOOLEAN DEFAULT FALSE,
    is_liked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

---

## 八、开发排期

### 8.1 后端开发 (14.5天)

| 模块        | 工期 | 说明 |
|-----------|------|------|
| 登录注册      | 2天 | Firebase集成、验证码邮件 |
| Profile管理 | 2天 | 用户信息、兴趣标签 |
| 首页Feed    | 2天 | 内容列表、广场Feed |
| AI对话      | 4天 | 会话管理、消息流 |
| 广场/Profile | 1天 | 内容发布 |
| 内容详情      | 3天 | 详情页、评论、互动 |
| 用户反馈      | 0.5天 | 反馈收集 |
| **系统设计文档** | **2天** | 架构设计、接口文档 |

### 8.2 其他模块 (估算)

| 模块 | 工期 |
|------|------|
| Flutter客户端 | 20天 |
| 爬虫系统 | 15天 |
| AI模型在线 | 10天 |
| AI模型离线 | 10天 |

---

## 九、项目目录结构

```
backend/
├── alembic/                    # 数据库迁移
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
├── alembic.ini
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI入口
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py       # 路由汇总
│   │       └── account.py      # 账户接口
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # 配置管理
│   │   ├── database.py         # 数据库连接
│   │   ├── redis.py            # Redis缓存
│   │   ├── firebase.py         # Firebase集成
│   │   └── email.py            # 邮件服务
│   ├── models/
│   │   ├── __init__.py
│   │   └── user.py             # 用户模型
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── account.py          # 账户Schema
│   │   └── response.py         # 响应Schema
│   └── services/
│       ├── __init__.py
│       └── account_service.py  # 账户业务逻辑
├── requirements.txt
├── env.example
└── README.md
```

---

## 十、环境配置

### 10.1 环境变量 (.env)

```bash
# 应用配置
APP_NAME=Joiiee
APP_VERSION=1.0.0
DEBUG=true

# Firebase配置
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_CREDENTIALS_PATH=firebase-credentials.json

# 数据库配置
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/joiiee

# Redis配置
REDIS_URL=redis://localhost:6379/0

# 邮件配置
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_FROM_NAME=Joiiee

# JWT配置
JWT_SECRET_KEY=your-super-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# 验证码配置
VERIFY_CODE_EXPIRE_MINUTES=10
VERIFY_CODE_LENGTH=6
```

### 10.2 依赖安装

```bash
pip install -r requirements.txt
```

### 10.3 启动服务

```bash
# 开发环境
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 生产环境
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 十一、错误码定义

| 错误码 | 含义 |
|--------|------|
| 0 | 成功 |
| 1 | 系统错误 |
| 100 | 参数错误 |
| 401 | 未授权 |
| 403 | 禁止访问 |
| 404 | 资源不存在 |
| 1001 | 无效的Token |
| 1002 | Token已过期 |
| 1003 | 验证码错误 |
| 1004 | 验证码已过期 |
| 1005 | 邮件发送失败 |
| 1006 | 用户不存在 |
| 1007 | 用户已禁用 |
| 2001 | Firebase认证错误 |
| 2002 | Firebase Token无效 |
| 2003 | Firebase用户不存在 |

---

**文档版本**: v1.0  
**更新日期**: 2026-01-16  
**编写人**: Joiiee Tech Team
