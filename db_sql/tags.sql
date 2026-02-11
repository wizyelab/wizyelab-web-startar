-- 标签表
CREATE TABLE `tags` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '自增主键, 标签ID',
  `tag_name` varchar(50) NOT NULL COMMENT '标签名称：Padel/Tennis/Pickleball',
  `tag_icon` varchar(500) DEFAULT NULL COMMENT '标签图标URL',
  `tag_category` varchar(50) DEFAULT NULL COMMENT '标签分类：sport/equipment/skill',
  `sort_order` int(11) NOT NULL DEFAULT '0' COMMENT '排序，数字越小越靠前',
  `status` tinyint(1) unsigned NOT NULL DEFAULT '1' COMMENT '状态：0-禁用，1-启用',
  `extra` text COMMENT '扩展字段',
  `create_time` bigint(20) unsigned NOT NULL COMMENT '创建时间',
  `update_time` bigint(20) unsigned NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_sort_order` (`sort_order`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COMMENT='标签表';
