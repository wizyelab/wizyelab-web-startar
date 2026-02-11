-- 用户标签关联表
CREATE TABLE `user_tags` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `user_id` varchar(20) NOT NULL COMMENT '用户ID，关联users.user_id',
  `tag_id` bigint(20) unsigned NOT NULL COMMENT '标签ID，关联tags.id',
  `level` varchar(20) DEFAULT NULL COMMENT '等级：beginner/intermediate/advanced/professional',
  `priority` tinyint(3) unsigned DEFAULT '0' COMMENT '优先级/偏好程度，数字越大越优先',
  `status` tinyint(1) unsigned NOT NULL DEFAULT '1' COMMENT '状态：0-删除，1-正常',
  `extra` text DEFAULT NULL COMMENT '扩展字段JSON',
  `create_time` bigint(20) unsigned NOT NULL COMMENT '创建时间（毫秒）',
  `update_time` bigint(20) unsigned NOT NULL COMMENT '更新时间（毫秒）',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_tag` (`user_id`,`tag_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='用户标签关联表';
