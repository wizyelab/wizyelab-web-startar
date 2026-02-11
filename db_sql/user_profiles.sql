-- 用户画像表
CREATE TABLE `user_profiles` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `user_id` varchar(20) NOT NULL COMMENT '用户ID，关联users.user_id',
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='用户画像表';
