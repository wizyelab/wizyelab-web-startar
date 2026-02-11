-- 用户反馈表
CREATE TABLE `user_feedbacks` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `user_id` varchar(20) NOT NULL COMMENT '用户ID，关联users.user_id',
  `post_id` varchar(20) DEFAULT NULL COMMENT '帖子ID，关联posts.post_id',
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
  KEY `idx_post_id` (`post_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='用户反馈表';
