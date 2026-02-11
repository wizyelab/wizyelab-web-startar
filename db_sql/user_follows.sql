-- 用户关注关系表
CREATE TABLE `user_follows` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `follower_id` varchar(20) NOT NULL COMMENT '关注者ID，关联users.user_id',
  `following_id` varchar(20) NOT NULL COMMENT '被关注者ID，关联users.user_id',
  `status` tinyint(1) unsigned NOT NULL DEFAULT '1' COMMENT '状态：0-取消关注，1-关注中',
  `create_time` bigint(20) unsigned NOT NULL COMMENT '创建时间',
  `update_time` bigint(20) unsigned NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_follow_relation` (`follower_id`,`following_id`),
  KEY `idx_follower_id` (`follower_id`),
  KEY `idx_following_id` (`following_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='用户关注关系表';
