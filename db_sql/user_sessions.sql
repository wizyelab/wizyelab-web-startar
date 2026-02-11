-- 用户会话记录表
CREATE TABLE `user_sessions` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `session_id` varchar(36) NOT NULL COMMENT '会话ID（UUID）',
  `user_id` varchar(20) NOT NULL COMMENT '用户ID，关联users.user_id',
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
  KEY `idx_user_device` (`user_id`,`device_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='用户会话记录表';
