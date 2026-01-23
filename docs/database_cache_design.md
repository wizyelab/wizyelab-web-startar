~~# Joiiee 数据库与缓存设计文档

## 一、设计概述

本文档基于 Joiiee 业务需求和接口设计，规划后端数据库表结构和 Redis 缓存结构。

### 1.1 技术选型

| 组件 | 技术选型 | 说明 |
|------|----------|------|
| 关系数据库 | 阿里云 PolarDB (MySQL兼容) | 主数据存储 |
| ORM | SQLAlchemy | 异步支持 |
| 缓存 | Redis | 会话/热点数据缓存 |
| 向量数据库 | FAISS/Milvus | 推荐向量存储 |
| 对象存储 | 阿里云 OSS | 媒体文件存储 |

### 1.2 命名规范

- 表名：小写下划线，复数形式（如 `users`, `chat_sessions`）
- 字段名：小写下划线（如 `user_id`, `create_time`）
- 索引名：`idx_{字段名}` 或 `idx_{字段1}_{字段2}`
- 唯一索引：`uk_{字段名}`

### 1.3 设计原则

- **不使用外键约束**：通过应用层保证数据一致性，提高写入性能和灵活性
- **软删除优先**：重要数据使用 `is_deleted` 或 `status` 字段标记删除
- **时间戳格式**：`create_time` 和 `update_time` 使用 `bigint` 存储毫秒级时间戳
- **适度冗余**：热点查询字段适当冗余，减少 JOIN 操作

### 1.4 通用字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | bigint(20) unsigned | 自增主键（物理主键） |
| `xxx_id` | varchar(36) | 业务ID（UUID格式，如 user_id、post_id） |
| `create_time` | bigint(20) unsigned | 创建时间戳（毫秒） |
| `update_time` | bigint(20) unsigned | 更新时间戳（毫秒） |
| `status` | tinyint(1) unsigned | 状态：0-不可用，1-可用 |
| `extra` | text | 扩展字段（JSON格式） |

### 1.5 主键设计说明

采用双ID方案：
- `id`：bigint 自增主键，用于数据库内部索引和分页优化
- `xxx_id`：varchar(36) UUID 字符串，用于业务层标识和对外暴露
- 关联表使用 UUID 字符串（如 `user_id`）进行关联
- 优点：对外不暴露自增序列，UUID 更安全且支持分布式生成

---

## 二、数据库表设计

### 2.1 用户模块

#### 2.1.1 users - 用户信息表

```sql
CREATE TABLE `users` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `user_id` varchar(36) NOT NULL COMMENT '用户ID（UUID）',
  `firebase_uid` varchar(128) DEFAULT NULL COMMENT 'Firebase UID',
  `phone` varchar(20) DEFAULT NULL COMMENT '手机号',
  `email` varchar(255) DEFAULT NULL COMMENT '邮箱',
  `user_name` varchar(50) DEFAULT NULL COMMENT '用户名',
  `avatar` varchar(500) DEFAULT NULL COMMENT '头像URL',
  `bio` varchar(500) DEFAULT NULL COMMENT '个人简介',
  `gender` tinyint(1) unsigned NOT NULL DEFAULT '0' COMMENT '性别：0-未知，1-男，2-女，3-其他',
  `location` varchar(100) DEFAULT NULL COMMENT '位置',
  `login_provider` varchar(20) DEFAULT NULL COMMENT '登录方式：google/apple/email/phone',
  `provider_token` text COMMENT '第三方登录Token',
  `status` tinyint(1) unsigned NOT NULL DEFAULT '1' COMMENT '状态：0-删除，1-正常',
  `extra` text COMMENT '扩展字段',
  `create_time` bigint(20) unsigned NOT NULL COMMENT '创建时间',
  `update_time` bigint(20) unsigned NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_id` (`user_id`),
  UNIQUE KEY `uk_firebase_uid` (`firebase_uid`),
  UNIQUE KEY `uk_phone` (`phone`),
  UNIQUE KEY `uk_email` (`email`),
  KEY `idx_create_time` (`create_time`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COMMENT='用户信息表';
```

#### 2.1.2 user_profiles - 用户画像表

```sql
CREATE TABLE `user_profiles` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `user_id` varchar(36) NOT NULL COMMENT '用户ID，关联users.user_id',
  `interest_tags` json DEFAULT NULL COMMENT '兴趣标签ID列表，如[1,2,3]',
  `skill_level` varchar(20) DEFAULT NULL COMMENT '技能等级：beginner/intermediate/advanced/professional',
  `equipment_config` json DEFAULT NULL COMMENT '装备配置',
  `profile_data` json DEFAULT NULL COMMENT '其他Profile数据（引导收集的数据）',
  `extra` text COMMENT '扩展字段',
  `create_time` bigint(20) unsigned NOT NULL COMMENT '创建时间',
  `update_time` bigint(20) unsigned NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_id` (`user_id`),
  KEY `idx_skill_level` (`skill_level`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COMMENT='用户画像表';
```

#### 2.1.3 user_devices - 用户设备表

```sql
CREATE TABLE `user_devices` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `user_id` varchar(36) NOT NULL COMMENT '用户ID，关联users.user_id',
  `device_id` varchar(100) NOT NULL COMMENT '设备ID',
  `device_type` varchar(20) DEFAULT NULL COMMENT '设备类型：ios/android',
  `device_name` varchar(100) DEFAULT NULL COMMENT '设备名称',
  `push_token` varchar(500) DEFAULT NULL COMMENT '推送Token',
  `app_version` varchar(20) DEFAULT NULL COMMENT 'App版本',
  `os_version` varchar(20) DEFAULT NULL COMMENT '系统版本',
  `is_active` tinyint(1) unsigned NOT NULL DEFAULT '1' COMMENT '是否激活：0-否，1-是',
  `last_active_at` bigint(20) unsigned DEFAULT NULL COMMENT '最后活跃时间',
  `extra` text COMMENT '扩展字段',
  `create_time` bigint(20) unsigned NOT NULL COMMENT '创建时间',
  `update_time` bigint(20) unsigned NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_device` (`user_id`, `device_id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_device_id` (`device_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COMMENT='用户设备表';
```

#### 2.1.4 user_sessions - 用户会话记录表

```sql
CREATE TABLE `user_sessions` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `session_id` varchar(36) NOT NULL COMMENT '会话ID（UUID）',
  `user_id` varchar(36) NOT NULL COMMENT '用户ID，关联users.user_id',
  `device_id` varchar(100) NOT NULL COMMENT '设备ID',
  `custom_token` text COMMENT '自定义Token',
  `refresh_token` text COMMENT '刷新Token',
  `login_ip` varchar(50) DEFAULT NULL COMMENT '登录IP',
  `login_location` varchar(100) DEFAULT NULL COMMENT '登录地点',
  `is_valid` tinyint(1) unsigned NOT NULL DEFAULT '1' COMMENT '是否有效：0-否，1-是',
  `expires_at` bigint(20) unsigned DEFAULT NULL COMMENT '过期时间',
  `last_used_at` bigint(20) unsigned DEFAULT NULL COMMENT '最后使用时间',
  `extra` text COMMENT '扩展字段',
  `create_time` bigint(20) unsigned NOT NULL COMMENT '创建时间（即登录时间）',
  `update_time` bigint(20) unsigned NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_session_id` (`session_id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_device_id` (`device_id`),
  KEY `idx_expires_at` (`expires_at`),
  KEY `idx_user_device` (`user_id`, `device_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COMMENT='用户会话记录表';
```

#### 2.1.5 user_follows - 用户关注关系表

```sql
CREATE TABLE `user_follows` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `follower_id` varchar(36) NOT NULL COMMENT '关注者ID，关联users.user_id',
  `following_id` varchar(36) NOT NULL COMMENT '被关注者ID，关联users.user_id',
  `status` tinyint(1) unsigned NOT NULL DEFAULT '1' COMMENT '状态：0-取消关注，1-关注中',
  `create_time` bigint(20) unsigned NOT NULL COMMENT '创建时间',
  `update_time` bigint(20) unsigned NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_follow_relation` (`follower_id`, `following_id`),
  KEY `idx_follower_id` (`follower_id`),
  KEY `idx_following_id` (`following_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COMMENT='用户关注关系表';
```

#### 2.1.6 user_stats - 用户统计表

```sql
CREATE TABLE `user_stats` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `user_id` varchar(36) NOT NULL COMMENT '用户ID，关联users.user_id',
  `follower_count` int(11) unsigned NOT NULL DEFAULT '0' COMMENT '粉丝数',
  `following_count` int(11) unsigned NOT NULL DEFAULT '0' COMMENT '关注数',
  `post_count` int(11) unsigned NOT NULL DEFAULT '0' COMMENT '帖子数',
  `like_count` int(11) unsigned NOT NULL DEFAULT '0' COMMENT '获赞数',
  `extra` text COMMENT '扩展字段',
  `create_time` bigint(20) unsigned NOT NULL COMMENT '创建时间',
  `update_time` bigint(20) unsigned NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_id` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COMMENT='用户统计表';
```

---

### 2.2 内容模块

#### 2.2.1 tags - 标签表

```sql
CREATE TABLE `tags` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `tag_id` varchar(36) NOT NULL COMMENT '标签ID（UUID）',
  `tag_name` varchar(50) NOT NULL COMMENT '标签名称：Padel/Tennis/Pickleball',
  `tag_icon` varchar(500) DEFAULT NULL COMMENT '标签图标URL',
  `tag_category` varchar(50) DEFAULT NULL COMMENT '标签分类：sport/equipment/skill',
  `parent_tag_id` varchar(36) DEFAULT NULL COMMENT '父标签ID，关联tags.tag_id',
  `sort_order` int(11) NOT NULL DEFAULT '0' COMMENT '排序，数字越小越靠前',
  `status` tinyint(1) unsigned NOT NULL DEFAULT '1' COMMENT '状态：0-禁用，1-启用',
  `extra` text COMMENT '扩展字段',
  `create_time` bigint(20) unsigned NOT NULL COMMENT '创建时间',
  `update_time` bigint(20) unsigned NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tag_id` (`tag_id`),
  UNIQUE KEY `uk_tag_name` (`tag_name`),
  KEY `idx_tag_category` (`tag_category`),
  KEY `idx_parent_tag_id` (`parent_tag_id`),
  KEY `idx_sort_order` (`sort_order`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COMMENT='标签表';
```

#### 2.2.2 posts - 帖子/内容表

```sql
CREATE TABLE `posts` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `post_id` varchar(36) NOT NULL COMMENT '帖子ID（UUID）',
  `user_id` varchar(36) NOT NULL COMMENT '用户ID，关联users.user_id',
  `post_type` tinyint(1) unsigned NOT NULL DEFAULT '3' COMMENT '帖子类型：1-视频，2-图片，3-文本',
  `title` varchar(200) DEFAULT NULL COMMENT '标题',
  `description` text COMMENT '描述',
  `content` text COMMENT '内容正文',
  `thumbnail_url` varchar(500) DEFAULT NULL COMMENT '缩略图URL',
  `img_urls` json DEFAULT NULL COMMENT '图片URL列表',
  `video_data` json DEFAULT NULL COMMENT '视频信息：{id,height,width,duration,cover_url,main_url,back_urls}',
  `like_count` int(11) unsigned NOT NULL DEFAULT '0' COMMENT '点赞数',
  `comment_count` int(11) unsigned NOT NULL DEFAULT '0' COMMENT '评论数',
  `share_count` int(11) unsigned NOT NULL DEFAULT '0' COMMENT '分享数',
  `view_count` int(11) unsigned NOT NULL DEFAULT '0' COMMENT '浏览数',
  `status` tinyint(1) unsigned NOT NULL DEFAULT '1' COMMENT '状态：0-草稿，1-正常，2-隐藏，3-删除',
  `source` varchar(50) NOT NULL DEFAULT 'ugc' COMMENT '来源：ugc/crawled',
  `source_platform` varchar(50) DEFAULT NULL COMMENT '来源平台：YouTube/Amazon/Reddit',
  `crawled_metadata` json DEFAULT NULL COMMENT '爬取元数据',
  `extra` text COMMENT '扩展字段',
  `create_time` bigint(20) unsigned NOT NULL COMMENT '创建时间',
  `update_time` bigint(20) unsigned NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_post_id` (`post_id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_post_type` (`post_type`),
  KEY `idx_status` (`status`),
  KEY `idx_create_time` (`create_time`),
  KEY `idx_source` (`source`),
  KEY `idx_user_status_time` (`user_id`, `status`, `create_time`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COMMENT='帖子/内容表';
```

#### 2.2.3 post_tags - 帖子标签关联表

```sql
CREATE TABLE `post_tags` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `post_id` varchar(36) NOT NULL COMMENT '帖子ID，关联posts.post_id',
  `tag_id` varchar(36) NOT NULL COMMENT '标签ID，关联tags.tag_id',
  `create_time` bigint(20) unsigned NOT NULL COMMENT '创建时间',
  `update_time` bigint(20) unsigned NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_post_tag` (`post_id`, `tag_id`),
  KEY `idx_post_id` (`post_id`),
  KEY `idx_tag_id` (`tag_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COMMENT='帖子标签关联表';
```

#### 2.2.4 comments - 评论表

```sql
CREATE TABLE `comments` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `comment_id` varchar(36) NOT NULL COMMENT '评论ID（UUID）',
  `post_id` varchar(36) NOT NULL COMMENT '帖子ID，关联posts.post_id',
  `user_id` varchar(36) NOT NULL COMMENT '用户ID，关联users.user_id',
  `parent_id` varchar(36) DEFAULT NULL COMMENT '父评论ID，关联comments.comment_id',
  `reply_to_user_id` varchar(36) DEFAULT NULL COMMENT '回复的用户ID，关联users.user_id',
  `text` text NOT NULL COMMENT '评论内容',
  `level` tinyint(1) unsigned NOT NULL DEFAULT '0' COMMENT '评论层级：0-一级，1-二级',
  `like_count` int(11) unsigned NOT NULL DEFAULT '0' COMMENT '点赞数',
  `reply_count` int(11) unsigned NOT NULL DEFAULT '0' COMMENT '回复数',
  `status` tinyint(1) unsigned NOT NULL DEFAULT '1' COMMENT '状态：0-删除，1-正常',
  `extra` text COMMENT '扩展字段',
  `create_time` bigint(20) unsigned NOT NULL COMMENT '创建时间',
  `update_time` bigint(20) unsigned NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_comment_id` (`comment_id`),
  KEY `idx_post_id` (`post_id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_parent_id` (`parent_id`),
  KEY `idx_create_time` (`create_time`),
  KEY `idx_post_status_time` (`post_id`, `status`, `create_time`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COMMENT='评论表';
```

#### 2.2.5 user_actions - 用户行为表

```sql
CREATE TABLE `user_actions` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `user_id` varchar(36) NOT NULL COMMENT '用户ID，关联users.user_id',
  `target_type` varchar(20) NOT NULL COMMENT '目标类型：post/comment',
  `target_id` varchar(36) NOT NULL COMMENT '目标ID（帖子或评论的UUID）',
  `action_type` tinyint(1) unsigned NOT NULL COMMENT '行为类型：0-浏览，1-点赞，2-收藏，3-分享',
  `is_active` tinyint(1) unsigned NOT NULL DEFAULT '1' COMMENT '是否有效（用于取消）：0-否，1-是',
  `extra` text COMMENT '扩展字段',
  `create_time` bigint(20) unsigned NOT NULL COMMENT '创建时间',
  `update_time` bigint(20) unsigned NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_action` (`user_id`, `target_type`, `target_id`, `action_type`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_target` (`target_type`, `target_id`),
  KEY `idx_action_type` (`action_type`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COMMENT='用户行为表（点赞/收藏/分享）';
```

#### 2.2.6 user_feedbacks - 用户反馈表

```sql
CREATE TABLE `user_feedbacks` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `user_id` varchar(36) NOT NULL COMMENT '用户ID，关联users.user_id',
  `post_id` varchar(36) DEFAULT NULL COMMENT '帖子ID，关联posts.post_id',
  `feedback_type` tinyint(1) unsigned NOT NULL COMMENT '反馈类型：1-不喜欢，2-不感兴趣，3-举报，4-垃圾内容',
  `reason` varchar(200) DEFAULT NULL COMMENT '反馈原因',
  `detail` text COMMENT '详细描述',
  `status` tinyint(1) unsigned NOT NULL DEFAULT '0' COMMENT '处理状态：0-待处理，1-已处理，2-已忽略',
  `processed_at` bigint(20) unsigned DEFAULT NULL COMMENT '处理时间',
  `extra` text COMMENT '扩展字段',
  `create_time` bigint(20) unsigned NOT NULL COMMENT '创建时间',
  `update_time` bigint(20) unsigned NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_post_id` (`post_id`),
  KEY `idx_status` (`status`),
  KEY `idx_feedback_type` (`feedback_type`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COMMENT='用户反馈表';
```

---

### 2.3 首页内容模块

#### 2.3.1 home_contents - 首页内容配置表

```sql
CREATE TABLE `home_contents` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `content_id` varchar(36) NOT NULL COMMENT '内容ID（UUID）',
  `tag_id` varchar(36) NOT NULL COMMENT '关联的标签ID，关联tags.tag_id',
  `content_type` tinyint(1) unsigned NOT NULL COMMENT '内容类型：0-默认，1-装备推荐，2-AI分析，3-高光时刻，4-推荐媒体',
  `logo` varchar(500) DEFAULT NULL COMMENT 'logo图片',
  `title` varchar(200) DEFAULT NULL COMMENT '标题',
  `sub_title` varchar(200) DEFAULT NULL COMMENT '副标题',
  `cover_image` varchar(500) DEFAULT NULL COMMENT '封面图',
  `button_desc` varchar(50) DEFAULT NULL COMMENT '按钮文案',
  `video_data` json DEFAULT NULL COMMENT '视频信息：{id,height,width,duration,cover_url,main_url,back_urls}',
  `action_type` tinyint(1) unsigned NOT NULL DEFAULT '0' COMMENT '点击动作：0-无，1-详情页，2-外链，3-视频上传',
  `action_url` varchar(500) DEFAULT NULL COMMENT '跳转链接',
  `item_list` json DEFAULT NULL COMMENT '装备/内容条目列表',
  `sort_order` int(11) NOT NULL DEFAULT '0' COMMENT '排序，数字越小越靠前',
  `status` tinyint(1) unsigned NOT NULL DEFAULT '1' COMMENT '状态：0-禁用，1-启用',
  `extra` text COMMENT '扩展字段',
  `create_time` bigint(20) unsigned NOT NULL COMMENT '创建时间',
  `update_time` bigint(20) unsigned NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_content_id` (`content_id`),
  KEY `idx_tag_id` (`tag_id`),
  KEY `idx_content_type` (`content_type`),
  KEY `idx_sort_order` (`sort_order`),
  KEY `idx_status` (`status`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COMMENT='首页内容配置表';
```

#### 2.3.2 equipments - 装备/商品表

```sql
CREATE TABLE `equipments` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `equipment_id` varchar(36) NOT NULL COMMENT '装备ID（UUID）',
  `name` varchar(200) NOT NULL COMMENT '装备名称',
  `brand` varchar(100) DEFAULT NULL COMMENT '品牌',
  `model` varchar(100) DEFAULT NULL COMMENT '型号',
  `category` varchar(50) DEFAULT NULL COMMENT '类别：racket/shoes/bag等',
  `img_urls` json DEFAULT NULL COMMENT '图片URL列表',
  `video_data` json DEFAULT NULL COMMENT '介绍视频',
  `price_min` decimal(10,2) DEFAULT NULL COMMENT '最低价',
  `price_max` decimal(10,2) DEFAULT NULL COMMENT '最高价',
  `price_display` varchar(50) DEFAULT NULL COMMENT '价格展示文本：$50-$80',
  `description` text COMMENT '描述',
  `rating` decimal(3,2) NOT NULL DEFAULT '0.00' COMMENT '评分',
  `review_count` int(11) unsigned NOT NULL DEFAULT '0' COMMENT '评论数',
  `tags` json DEFAULT NULL COMMENT '标签列表',
  `specifications` json DEFAULT NULL COMMENT '规格参数',
  `source_platform` varchar(50) DEFAULT NULL COMMENT '来源平台',
  `source_url` varchar(500) DEFAULT NULL COMMENT '来源链接',
  `source_id` varchar(100) DEFAULT NULL COMMENT '来源平台ID',
  `status` tinyint(1) unsigned NOT NULL DEFAULT '1' COMMENT '状态：0-下架，1-上架',
  `extra` text COMMENT '扩展字段',
  `create_time` bigint(20) unsigned NOT NULL COMMENT '创建时间',
  `update_time` bigint(20) unsigned NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_equipment_id` (`equipment_id`),
  KEY `idx_brand` (`brand`),
  KEY `idx_category` (`category`),
  KEY `idx_rating` (`rating`),
  KEY `idx_source` (`source_platform`, `source_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COMMENT='装备/商品表';
```

---

### 2.4 对话模块

#### 2.4.1 chat_sessions - 对话会话表

```sql
CREATE TABLE `chat_sessions` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `session_id` varchar(36) NOT NULL COMMENT '会话ID（UUID）',
  `user_id` varchar(36) NOT NULL COMMENT '用户ID，关联users.user_id',
  `session_type` tinyint(1) unsigned NOT NULL DEFAULT '1' COMMENT '会话类型：1-通用，2-装备推荐，3-视频分析，4-训练指导',
  `title` varchar(200) DEFAULT NULL COMMENT '会话标题',
  `source_type` tinyint(1) unsigned NOT NULL DEFAULT '0' COMMENT '来源类型：0-chat，1-装备推荐，2-AI分析，3-高光时刻，4-推荐媒体',
  `home_tag_id` varchar(36) DEFAULT NULL COMMENT '首页tag_id，关联tags.tag_id',
  `home_content_id` varchar(36) DEFAULT NULL COMMENT '首页content_id，关联home_contents.content_id',
  `context_data` json DEFAULT NULL COMMENT '会话上下文',
  `message_count` int(11) unsigned NOT NULL DEFAULT '0' COMMENT '消息数量',
  `is_pinned` tinyint(1) unsigned NOT NULL DEFAULT '0' COMMENT '是否置顶：0-否，1-是',
  `status` tinyint(1) unsigned NOT NULL DEFAULT '1' COMMENT '状态：0-删除，1-活跃，2-归档',
  `last_message_at` bigint(20) unsigned DEFAULT NULL COMMENT '最后消息时间',
  `last_message_preview` varchar(100) DEFAULT NULL COMMENT '最后消息预览',
  `extra` text COMMENT '扩展字段',
  `create_time` bigint(20) unsigned NOT NULL COMMENT '创建时间',
  `update_time` bigint(20) unsigned NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_session_id` (`session_id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_status` (`status`),
  KEY `idx_last_message_at` (`last_message_at`),
  KEY `idx_user_status_time` (`user_id`, `status`, `last_message_at`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COMMENT='对话会话表';
```

#### 2.4.2 chat_messages - 对话消息表

```sql
CREATE TABLE `chat_messages` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `message_id` varchar(36) NOT NULL COMMENT '消息ID（UUID）',
  `session_id` varchar(36) NOT NULL COMMENT '会话ID，关联chat_sessions.session_id',
  `user_id` varchar(36) NOT NULL COMMENT '用户ID，关联users.user_id',
  `role` tinyint(1) unsigned NOT NULL COMMENT '角色：1-用户，2-助手，3-系统',
  `content` text NOT NULL COMMENT '消息内容',
  `message_type` tinyint(1) unsigned NOT NULL DEFAULT '3' COMMENT '消息类型：1-视频，2-图片，3-文本，4-语音',
  `message_style` tinyint(1) unsigned NOT NULL DEFAULT '0' COMMENT '消息样式：0-chat，1-装备推荐，2-AI分析，3-高光，4-媒体',
  `attachments` json DEFAULT NULL COMMENT '附件列表：[{media_type,url,extra}]',
  `cards` json DEFAULT NULL COMMENT '卡片组件列表',
  `media_reference` json DEFAULT NULL COMMENT '参考媒体源：[{logo,desc}]',
  `summary` varchar(500) DEFAULT NULL COMMENT '总结',
  `component` json DEFAULT NULL COMMENT '组件：{text,button_left_desc,button_right_desc}',
  `evidence_chain` json DEFAULT NULL COMMENT '推荐证据链',
  `generation_status` tinyint(1) unsigned NOT NULL DEFAULT '3' COMMENT '生成状态：1-等待，2-生成中，3-完成，4-失败，5-停止',
  `extra` text COMMENT '扩展字段',
  `create_time` bigint(20) unsigned NOT NULL COMMENT '创建时间',
  `update_time` bigint(20) unsigned NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_message_id` (`message_id`),
  KEY `idx_session_id` (`session_id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_create_time` (`create_time`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COMMENT='对话消息表';
```

---

### 2.5 引导配置模块

#### 2.5.1 guide_items - 引导配置表

```sql
CREATE TABLE `guide_items` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `guide_id` varchar(50) NOT NULL COMMENT '引导项ID：interests/skill_level/equipment',
  `style` tinyint(1) unsigned NOT NULL DEFAULT '0' COMMENT '引导样式：0-对话式，1-选项条，2-选项卡',
  `guide_words` text COMMENT '引导话术',
  `profile_key` varchar(50) DEFAULT NULL COMMENT '对应profile字段名',
  `sort_order` int(11) NOT NULL DEFAULT '0' COMMENT '排序，数字越小越靠前',
  `is_required` tinyint(1) unsigned NOT NULL DEFAULT '0' COMMENT '是否必填：0-否，1-是',
  `options` json DEFAULT NULL COMMENT '选项列表：[{content,description,icon_url}]',
  `status` tinyint(1) unsigned NOT NULL DEFAULT '1' COMMENT '状态：0-禁用，1-启用',
  `extra` text COMMENT '扩展字段',
  `create_time` bigint(20) unsigned NOT NULL COMMENT '创建时间',
  `update_time` bigint(20) unsigned NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_guide_id` (`guide_id`),
  KEY `idx_sort_order` (`sort_order`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COMMENT='引导配置表';
```

---

### 2.6 爬虫数据模块

#### 2.6.1 crawl_tasks - 爬虫任务表

```sql
CREATE TABLE `crawl_tasks` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `task_id` varchar(36) NOT NULL COMMENT '任务ID（UUID）',
  `task_type` varchar(20) NOT NULL COMMENT '任务类型：youtube/amazon/reddit',
  `task_config` json DEFAULT NULL COMMENT '任务配置',
  `status` varchar(20) NOT NULL DEFAULT 'pending' COMMENT '状态：pending/running/success/failed',
  `error_message` text COMMENT '错误信息',
  `retry_count` int(11) unsigned NOT NULL DEFAULT '0' COMMENT '重试次数',
  `next_run_time` bigint(20) unsigned DEFAULT NULL COMMENT '下次运行时间',
  `started_at` bigint(20) unsigned DEFAULT NULL COMMENT '开始时间',
  `finished_at` bigint(20) unsigned DEFAULT NULL COMMENT '完成时间',
  `extra` text COMMENT '扩展字段',
  `create_time` bigint(20) unsigned NOT NULL COMMENT '创建时间',
  `update_time` bigint(20) unsigned NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_task_id` (`task_id`),
  KEY `idx_task_type` (`task_type`),
  KEY `idx_status` (`status`),
  KEY `idx_next_run_time` (`next_run_time`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COMMENT='爬虫任务表';
```

#### 2.6.2 crawled_raw_data - 爬取原始数据表

```sql
CREATE TABLE `crawled_raw_data` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `task_id` varchar(36) DEFAULT NULL COMMENT '任务ID，关联crawl_tasks.task_id',
  `platform` varchar(50) NOT NULL COMMENT '平台：youtube/amazon/reddit',
  `data_type` varchar(50) DEFAULT NULL COMMENT '数据类型：video/product/post/comment',
  `external_id` varchar(200) DEFAULT NULL COMMENT '外部平台ID',
  `raw_data` json NOT NULL COMMENT '原始数据',
  `is_processed` tinyint(1) unsigned NOT NULL DEFAULT '0' COMMENT '是否已处理：0-否，1-是',
  `processed_at` bigint(20) unsigned DEFAULT NULL COMMENT '处理时间',
  `extra` text COMMENT '扩展字段',
  `create_time` bigint(20) unsigned NOT NULL COMMENT '创建时间',
  `update_time` bigint(20) unsigned NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_platform_external` (`platform`, `external_id`),
  KEY `idx_platform` (`platform`),
  KEY `idx_is_processed` (`is_processed`),
  KEY `idx_task_id` (`task_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COMMENT='爬取原始数据表';
```

---

### 2.7 AI分析模块

#### 2.7.1 user_video_analysis - 用户视频分析表

```sql
CREATE TABLE `user_video_analysis` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `analysis_id` varchar(36) NOT NULL COMMENT '分析ID（UUID）',
  `user_id` varchar(36) NOT NULL COMMENT '用户ID，关联users.user_id',
  `video_url` varchar(500) NOT NULL COMMENT '视频URL',
  `video_data` json DEFAULT NULL COMMENT '视频信息',
  `action_type` varchar(50) DEFAULT NULL COMMENT '动作类型：forehand/backhand/serve/volley/footwork',
  `skeleton_data` json DEFAULT NULL COMMENT '骨架关键点数据',
  `score` decimal(5,2) DEFAULT NULL COMMENT '动作评分',
  `analysis_result` json DEFAULT NULL COMMENT '分析结果',
  `correction_advice` json DEFAULT NULL COMMENT '纠正建议',
  `similar_standard_videos` json DEFAULT NULL COMMENT '相似标准动作视频',
  `highlight_video` json DEFAULT NULL COMMENT '生成的高光视频',
  `status` varchar(20) NOT NULL DEFAULT 'pending' COMMENT '状态：pending/processing/completed/failed',
  `error_message` text COMMENT '错误信息',
  `completed_at` bigint(20) unsigned DEFAULT NULL COMMENT '完成时间',
  `extra` text COMMENT '扩展字段',
  `create_time` bigint(20) unsigned NOT NULL COMMENT '创建时间',
  `update_time` bigint(20) unsigned NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_analysis_id` (`analysis_id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_status` (`status`),
  KEY `idx_action_type` (`action_type`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COMMENT='用户视频分析表';
```

#### 2.7.2 standard_actions - 标准动作库表

```sql
CREATE TABLE `standard_actions` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `action_id` varchar(36) NOT NULL COMMENT '动作ID（UUID）',
  `action_type` varchar(50) NOT NULL COMMENT '动作类型',
  `action_name` varchar(100) NOT NULL COMMENT '动作名称',
  `skeleton_template` json DEFAULT NULL COMMENT '标准骨架模板',
  `video_url` varchar(500) DEFAULT NULL COMMENT '示例视频',
  `video_data` json DEFAULT NULL COMMENT '视频信息',
  `difficulty_level` varchar(20) DEFAULT NULL COMMENT '难度等级',
  `description` text COMMENT '描述',
  `tips` json DEFAULT NULL COMMENT '技巧提示',
  `status` tinyint(1) unsigned NOT NULL DEFAULT '1' COMMENT '状态：0-禁用，1-启用',
  `extra` text COMMENT '扩展字段',
  `create_time` bigint(20) unsigned NOT NULL COMMENT '创建时间',
  `update_time` bigint(20) unsigned NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_action_id` (`action_id`),
  KEY `idx_action_type` (`action_type`),
  KEY `idx_difficulty_level` (`difficulty_level`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COMMENT='标准动作库表';
```

#### 2.7.3 recommendation_logs - 推荐日志表

```sql
CREATE TABLE `recommendation_logs` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `user_id` varchar(36) NOT NULL COMMENT '用户ID，关联users.user_id',
  `target_type` varchar(20) NOT NULL COMMENT '目标类型：post/equipment',
  `target_id` varchar(36) NOT NULL COMMENT '目标ID（帖子或装备的UUID）',
  `scene` varchar(50) DEFAULT NULL COMMENT '场景：feed/search/related/chat',
  `rank_score` decimal(10,6) DEFAULT NULL COMMENT '排序分数',
  `evidence_chain` json DEFAULT NULL COMMENT '推荐证据链',
  `is_impressed` tinyint(1) unsigned NOT NULL DEFAULT '0' COMMENT '是否曝光：0-否，1-是',
  `is_clicked` tinyint(1) unsigned NOT NULL DEFAULT '0' COMMENT '是否点击：0-否，1-是',
  `is_liked` tinyint(1) unsigned NOT NULL DEFAULT '0' COMMENT '是否点赞：0-否，1-是',
  `extra` text COMMENT '扩展字段',
  `create_time` bigint(20) unsigned NOT NULL COMMENT '创建时间',
  `update_time` bigint(20) unsigned NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_target` (`target_type`, `target_id`),
  KEY `idx_scene` (`scene`),
  KEY `idx_create_time` (`create_time`),
  KEY `idx_user_scene_time` (`user_id`, `scene`, `create_time`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COMMENT='推荐日志表';
```

#### 2.7.4 content_embeddings - 内容向量表

```sql
CREATE TABLE `content_embeddings` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `target_type` varchar(20) NOT NULL COMMENT '目标类型：post/equipment',
  `target_id` varchar(36) NOT NULL COMMENT '目标ID（帖子或装备的UUID）',
  `embedding_model` varchar(50) DEFAULT NULL COMMENT '模型名称',
  `embedding_vector` blob COMMENT '向量数据',
  `embedding_dimension` int(11) unsigned DEFAULT NULL COMMENT '向量维度',
  `extra` text COMMENT '扩展字段',
  `create_time` bigint(20) unsigned NOT NULL COMMENT '创建时间',
  `update_time` bigint(20) unsigned NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_target_model` (`target_type`, `target_id`, `embedding_model`),
  KEY `idx_target` (`target_type`, `target_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COMMENT='内容向量表';
```

---

### 2.8 分享模块

#### 2.8.1 share_links - 分享链接表

```sql
CREATE TABLE `share_links` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `share_id` varchar(36) NOT NULL COMMENT '分享ID（UUID）',
  `user_id` varchar(36) NOT NULL COMMENT '用户ID，关联users.user_id',
  `post_id` varchar(36) NOT NULL COMMENT '帖子ID，关联posts.post_id',
  `share_type` varchar(20) NOT NULL DEFAULT 'h5' COMMENT '分享类型：h5/deeplink',
  `share_code` varchar(50) DEFAULT NULL COMMENT '分享短码',
  `share_url` varchar(500) DEFAULT NULL COMMENT '分享链接',
  `share_text` varchar(500) DEFAULT NULL COMMENT '分享文案',
  `share_image` varchar(500) DEFAULT NULL COMMENT '分享图片',
  `click_count` int(11) unsigned NOT NULL DEFAULT '0' COMMENT '点击次数',
  `expires_at` bigint(20) unsigned DEFAULT NULL COMMENT '过期时间',
  `extra` text COMMENT '扩展字段',
  `create_time` bigint(20) unsigned NOT NULL COMMENT '创建时间',
  `update_time` bigint(20) unsigned NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_share_id` (`share_id`),
  UNIQUE KEY `uk_share_code` (`share_code`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_post_id` (`post_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COMMENT='分享链接表';
```

---

## 三、缓存设计

### 3.1 缓存架构

```
┌─────────────────────────────────────────────────────────────┐
│                       应用层                                 │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐       │
│  │Profile  │  │Content  │  │Chat     │  │Feed     │       │
│  │Service  │  │Service  │  │Service  │  │Service  │       │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘       │
│       └────────────┼────────────┼────────────┘             │
│                    │            │                          │
│              ┌─────▼────────────▼─────┐                    │
│              │     CacheService       │                    │
│              │  (统一缓存服务层)       │                    │
│              └───────────┬────────────┘                    │
└──────────────────────────┼──────────────────────────────────┘
                           │
              ┌────────────▼────────────┐
              │         Redis          │
              │   ┌─────┬─────┬─────┐  │
              │   │会话 │内容 │计数 │  │
              │   │缓存 │缓存 │器   │  │
              │   └─────┴─────┴─────┘  │
              └─────────────────────────┘
```

### 3.2 缓存键命名规范

```
{业务域}:{实体类型}:{实体ID}[:{子类型}]
```

### 3.3 缓存键清单

#### 3.3.1 用户相关缓存

| 缓存键模板 | 数据类型 | 说明 | TTL | 失效时机 |
|-----------|----------|------|-----|----------|
| `session:{user_id}:{device_id}` | String | 用户会话Token | 7天 | 登出/过期 |
| `user:profile:{user_id}` | Hash | 用户Profile信息 | 1小时 | Profile更新 |
| `user:stats:{user_id}` | Hash | 用户统计数据 | 5分钟 | 计数变化 |
| `user:settings:{user_id}` | Hash | 用户设置 | 1天 | 设置更新 |

**说明**: `user_id` 为 varchar(36) UUID 字符串

#### 3.3.2 内容相关缓存

| 缓存键模板 | 数据类型 | 说明 | TTL | 失效时机 |
|-----------|----------|------|-----|----------|
| `post:detail:{post_id}` | Hash | 帖子详情 | 30分钟 | 帖子更新/删除 |
| `post:stats:{post_id}` | Hash | 帖子统计 | 5分钟 | 计数变化 |
| `comments:{post_id}:{page}` | List | 评论列表 | 10分钟 | 新评论/删除 |
| `comment:detail:{comment_id}` | Hash | 评论详情 | 30分钟 | 评论更新/删除 |

**说明**: `post_id`、`comment_id` 均为 varchar(36) UUID 字符串

#### 3.3.3 首页/Feed相关缓存

| 缓存键模板 | 数据类型 | 说明 | TTL | 失效时机 |
|-----------|----------|------|-----|----------|
| `home:tags` | List | 首页标签列表 | 1小时 | 标签配置变化 |
| `home:content:{tag_id}` | List | 标签内容列表 | 30分钟 | 内容配置变化 |
| `feed:{user_id}:{page}` | List | 用户Feed流 | 5分钟 | 新帖子/行为变化 |
| `hot:posts:{category}` | ZSet | 热门帖子 | 1小时 | 定时刷新 |
| `trending:{date}` | ZSet | 趋势内容 | 10分钟 | 定时刷新 |

#### 3.3.4 用户行为缓存

| 缓存键模板 | 数据类型 | 说明 | TTL | 失效时机 |
|-----------|----------|------|-----|----------|
| `action:{user_id}:{target_type}:{target_id}:{action_type}` | String | 用户行为状态 | 1小时 | 行为变化 |
| `user:liked:{user_id}` | Set | 用户点赞集合 | 1小时 | 点赞变化 |
| `user:collected:{user_id}` | Set | 用户收藏集合 | 1小时 | 收藏变化 |

#### 3.3.5 计数器缓存

| 缓存键模板 | 数据类型 | 说明 | TTL | 同步策略 |
|-----------|----------|------|-----|----------|
| `count:view:{post_id}` | String | 浏览计数 | 1天 | 每100次或每5分钟同步DB |
| `count:like:{post_id}` | String | 点赞计数 | 1天 | 实时同步DB |
| `count:comment:{post_id}` | String | 评论计数 | 1天 | 实时同步DB |
| `count:share:{post_id}` | String | 分享计数 | 1天 | 实时同步DB |

#### 3.3.6 对话相关缓存

| 缓存键模板 | 数据类型 | 说明 | TTL | 失效时机 |
|-----------|----------|------|-----|----------|
| `chat:session:{session_id}` | Hash | 对话会话 | 7天 | 会话更新/删除 |
| `chat:context:{session_id}` | List | 对话上下文(最近10轮) | 7天 | 新消息 |
| `chat:sessions:{user_id}` | List | 用户会话列表 | 30分钟 | 会话变化 |
| `ai:cache:{query_hash}` | String | AI回复缓存 | 1天 | - |

**说明**: `session_id`、`user_id` 均为 varchar(36) UUID 字符串

#### 3.3.7 验证/限流缓存

| 缓存键模板 | 数据类型 | 说明 | TTL | 失效时机 |
|-----------|----------|------|-----|----------|
| `verify:{email}:{device_id}` | Hash | 验证码 | 10分钟 | 验证成功 |
| `rate:{user_id}:{action}` | String | 限流计数 | 1分钟 | 时间窗口过期 |
| `rate:ip:{ip}:{action}` | String | IP限流计数 | 1分钟 | 时间窗口过期 |

#### 3.3.8 推荐相关缓存

| 缓存键模板 | 数据类型 | 说明 | TTL | 失效时机 |
|-----------|----------|------|-----|----------|
| `rec:{user_id}:{scene}` | List | 用户推荐结果 | 5分钟 | 推荐刷新 |
| `similar:post:{post_id}` | List | 相似帖子 | 1天 | - |
| `similar:equipment:{equipment_id}` | List | 相似装备 | 1天 | - |

---

### 3.4 缓存数据结构示例

#### 3.4.1 用户Profile缓存结构

```json
// key: user:profile:{user_id}
// user_id 为 UUID 字符串，如 user:profile:550e8400-e29b-41d4-a716-446655440000
{
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_name": "Joan",
    "avatar": "https://example.com/avatar/joan.png",
    "bio": "Paddle enthusiast",
    "gender": 2,
    "location": "San Francisco, CA",
    "interest_tags": [1, 2],
    "skill_level": "intermediate",
    "follower_count": 128,
    "following_count": 56,
    "post_count": 24
}
```

#### 3.4.2 帖子详情缓存结构

```json
// key: post:detail:{post_id}
// post_id 为 UUID 字符串，如 post:detail:660e8400-e29b-41d4-a716-446655440001
{
    "post_id": "660e8400-e29b-41d4-a716-446655440001",
    "post_type": 1,
    "title": "Great match",
    "description": "Amazing paddle session",
    "content": "...",
    "thumbnail_url": "https://...",
    "img_urls": [],
    "video": {
        "id": "video_001",
        "height": 1920,
        "width": 1080,
        "duration": 60,
        "cover_url": "...",
        "main_url": "...",
        "back_urls": []
    },
    "author": {
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "user_name": "Joan",
        "avatar": "..."
    },
    "like_count": 128,
    "comment_count": 32,
    "share_count": 8,
    "create_time": 1705732200000
}
```

#### 3.4.3 对话上下文缓存结构

```json
// key: chat:context:{session_id}
// session_id 为 UUID 字符串，如 chat:context:770e8400-e29b-41d4-a716-446655440002
// 使用 List 存储最近10轮对话
[
    {
        "role": 1,
        "content": "推荐一款适合初学者的球拍",
        "timestamp": 1705732200000
    },
    {
        "role": 2,
        "content": "根据您的需求，我推荐...",
        "cards": [...],
        "timestamp": 1705732202000
    }
]
```

---

### 3.5 缓存策略

#### 3.5.1 读取策略 - Cache-Aside

```python
async def get_post_detail(post_id: str) -> dict:
    # 1. 先查缓存
    cache_key = f"post:detail:{post_id}"
    cached = await redis.hgetall(cache_key)
    if cached:
        return cached

    # 2. 缓存未命中，查数据库
    post = await db.get(Post, post_id)
    if not post:
        # 缓存空值防止穿透
        await redis.setex(f"post:null:{post_id}", 60, "1")
        return None

    # 3. 回写缓存
    await redis.hset(cache_key, mapping=post.to_dict())
    await redis.expire(cache_key, 1800)  # 30分钟

    return post.to_dict()
```

#### 3.5.2 写入策略 - Write-Through

```python
async def update_user_profile(user_id: str, data: dict):
    # 1. 更新数据库
    await db.update(UserProfile, user_id, data)

    # 2. 更新缓存
    cache_key = f"user:profile:{user_id}"
    await redis.hset(cache_key, mapping=data)
    await redis.expire(cache_key, 3600)  # 1小时
```

#### 3.5.3 缓存失效策略

```python
async def delete_post(user_id: str, post_id: str):
    # 1. 删除数据库记录
    await db.delete(Post, post_id)

    # 2. 删除相关缓存
    await redis.delete(f"post:detail:{post_id}")
    await redis.delete(f"post:stats:{post_id}")
    await redis.delete(f"comments:{post_id}:*")

    # 3. 使用户Feed缓存失效
    await redis.delete(f"feed:{user_id}:*")

    # 4. 更新用户统计
    await redis.hincrby(f"user:stats:{user_id}", "post_count", -1)
```

---

### 3.6 缓存防护策略

#### 3.6.1 缓存穿透防护

```python
async def get_post_safe(post_id: str):
    # 检查空值标记
    if await redis.exists(f"post:null:{post_id}"):
        return None

    cached = await redis.hgetall(f"post:detail:{post_id}")
    if cached:
        return cached

    post = await db.get(Post, post_id)
    if post:
        await redis.hset(f"post:detail:{post_id}", mapping=post.to_dict())
        await redis.expire(f"post:detail:{post_id}", 1800)
    else:
        # 缓存空值，短TTL
        await redis.setex(f"post:null:{post_id}", 60, "1")

    return post
```

#### 3.6.2 缓存雪崩防护

```python
import random

async def set_with_jitter(key: str, value: Any, base_ttl: int):
    # 添加随机过期时间，避免同时过期
    jitter = random.randint(-60, 60)  # ±60秒抖动
    ttl = max(60, base_ttl + jitter)  # 最小60秒
    await redis.setex(key, ttl, value)
```

#### 3.6.3 限流保护

```python
async def check_rate_limit(user_id: str, action: str, limit: int = 100, window: int = 60) -> tuple[bool, int]:
    """
    检查限流
    返回: (是否允许, 剩余次数)
    """
    key = f"rate:{user_id}:{action}"

    current = await redis.incr(key)
    if current == 1:
        await redis.expire(key, window)

    remaining = max(0, limit - current)
    allowed = current <= limit

    return allowed, remaining
```

---

### 3.7 缓存预热

```python
async def warmup_cache():
    """应用启动时预热缓存"""

    # 1. 预热首页标签
    tags = await db.get_active_tags()
    await redis.delete("home:tags")
    await redis.rpush("home:tags", *[json.dumps(t) for t in tags])
    await redis.expire("home:tags", 3600)

    # 2. 预热热门内容
    for tag in tags:
        contents = await db.get_home_contents(tag['id'])
        key = f"home:content:{tag['id']}"
        await redis.delete(key)
        await redis.rpush(key, *[json.dumps(c) for c in contents])
        await redis.expire(key, 1800)

    # 3. 预热热门帖子
    hot_posts = await db.get_hot_posts(limit=100)
    await redis.delete("hot:posts:all")
    for post in hot_posts:
        await redis.zadd("hot:posts:all", {post['id']: post['score']})
    await redis.expire("hot:posts:all", 3600)

    # 4. 预热标准动作库
    actions = await db.get_standard_actions()
    await redis.set("standard_actions", json.dumps(actions))
    await redis.expire("standard_actions", 86400)
```

---

## 四、数据库索引优化建议

### 4.1 复合索引

```sql
-- 用户Feed查询优化
ALTER TABLE `posts` ADD INDEX `idx_status_create_time` (`status`, `create_time` DESC);

-- 用户帖子列表查询（已在建表时添加）
-- KEY `idx_user_status_time` (`user_id`, `status`, `create_time`)

-- 评论列表查询（已在建表时添加）
-- KEY `idx_post_status_time` (`post_id`, `status`, `create_time`)

-- 推荐日志查询（已在建表时添加）
-- KEY `idx_user_scene_time` (`user_id`, `scene`, `create_time`)
```

### 4.2 分区建议

```sql
-- 对于大表考虑按时间分区
-- recommendation_logs 按月分区
ALTER TABLE `recommendation_logs` PARTITION BY RANGE (create_time) (
    PARTITION p202601 VALUES LESS THAN (1738339200000),
    PARTITION p202602 VALUES LESS THAN (1740758400000),
    PARTITION p202603 VALUES LESS THAN (1743436800000),
    PARTITION pmax VALUES LESS THAN MAXVALUE
);
```

---

## 五、监控指标

### 5.1 数据库监控

| 指标 | 说明 | 告警阈值 |
|------|------|----------|
| 连接数 | 当前活跃连接数 | > 80% max_connections |
| 查询耗时 | 慢查询数量 | > 100ms 的查询数 |
| 表大小 | 主要表的数据量 | 单表 > 1000万行 |
| 索引命中率 | 索引使用效率 | < 95% |

### 5.2 缓存监控

| 指标 | 说明 | 告警阈值 |
|------|------|----------|
| 命中率 | 缓存命中率 | < 80% |
| 内存使用 | Redis内存使用率 | > 80% |
| 键数量 | 总键数量 | > 100万 |
| P99延迟 | 99分位延迟 | > 10ms |

---

## 六、版本记录

| 版本 | 日期 | 更新内容 | 编写人 |
|------|------|----------|--------|
| v1.0 | 2026-01-23 | 初始版本 | Joiiee Tech Team |
| v1.1 | 2026-01-23 | 移除外键约束 | Joiiee Tech Team |
| v1.2 | 2026-01-23 | 适配PolarDB MySQL语法，时间戳格式 | Joiiee Tech Team |
| v1.3 | 2026-01-23 | 拆分用户信息表和会话记录表，添加手机号字段 | Joiiee Tech Team |
| v1.4 | 2026-01-23 | 采用双ID方案（自增id + UUID业务ID），添加provider_token字段 | Joiiee Tech Team |

---

**文档版本**: v1.4
**更新日期**: 2026-01-23
**编写人**: Joiiee Tech Team~~
