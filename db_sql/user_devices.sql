-- 用户设备表
CREATE TABLE `user_devices` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `user_id` varchar(20) NOT NULL COMMENT '用户ID，关联users.user_id',
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
  UNIQUE KEY `uk_user_device` (`user_id`,`device_id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_device_id` (`device_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='用户设备表';
