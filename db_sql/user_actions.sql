-- 用户行为表（点赞/收藏/分享）
CREATE TABLE `user_actions` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `user_id` varchar(20) NOT NULL COMMENT '用户ID，关联users.user_id',
  `target_type` varchar(20) NOT NULL COMMENT '目标类型：post/comment',
  `target_id` varchar(20) NOT NULL COMMENT '目标ID（帖子或评论的UUID）',
  `action_type` tinyint(1) unsigned NOT NULL COMMENT '行为类型：0-浏览，1-点赞，2-收藏，3-分享',
  `status` tinyint(1) unsigned NOT NULL DEFAULT '1' COMMENT '是否有效（用于取消）：0-否，1-是',
  `extra` text COMMENT '扩展字段',
  `create_time` bigint(20) unsigned NOT NULL COMMENT '创建时间',
  `update_time` bigint(20) unsigned NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_action` (`user_id`,`target_type`,`target_id`,`action_type`),
  KEY `idx_target` (`target_type`,`target_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='用户行为表（点赞/收藏/分享）';
