-- 引导配置表
CREATE TABLE `guide_items` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `tag_id` bigint(20) NOT NULL COMMENT '标签id',
  `style` tinyint(1) unsigned NOT NULL DEFAULT '0' COMMENT '引导样式：0-对话式，1-选项条，2-选项卡',
  `guide_words` text COMMENT '引导话术',
  `profile_key` varchar(50) DEFAULT NULL COMMENT '对应profile字段名',
  `sort_order` int(11) NOT NULL DEFAULT '0' COMMENT '排序，数字越小越靠前',
  `options` json DEFAULT NULL COMMENT '选项列表：[{content,description,icon_url}]',
  `head_img` json DEFAULT NULL COMMENT 'Logo上半部分图片',
  `body_img` json DEFAULT NULL COMMENT 'Logo下半部分图片',
  `status` tinyint(1) unsigned NOT NULL DEFAULT '1' COMMENT '状态：0-禁用，1-启用',
  `extra` text COMMENT '扩展字段',
  `create_time` bigint(20) unsigned NOT NULL COMMENT '创建时间',
  `update_time` bigint(20) unsigned NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_sort_order` (`sort_order`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COMMENT='引导配置表';
