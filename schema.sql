
CREATE TABLE `order` (
    `id` BIGINT(20) NOT NULL AUTO_INCREMENT COMMENT 'id',
    `symbol` VARCHAR(20) NOT NULL DEFAULT '' COMMENT '交易对',
    `order_id`  VARCHAR(100) NOT NULL DEFAULT '' COMMENT '订单id',
    `side` VARCHAR(10) NOT NULL DEFAULT '' COMMENT '方向',
    `state` VARCHAR(20) NOT NULL DEFAULT '' COMMENT '状态',
    `price` decimal(20,10) NOT NULL DEFAULT '0.0000000000' COMMENT '价格',
    `amount` decimal(20,10) NOT NULL DEFAULT '0.0000000000' COMMENT '量',
    `filled_amount` decimal(20,10) NOT NULL DEFAULT '0.0000000000' COMMENT '成交量',
    `fill_fees` decimal(20,10) NOT NULL DEFAULT '0.0000000000' COMMENT '手续费',
    `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT "创建时间",
    `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT "更新时间",
    PRIMARY KEY (`id`),
    unique key `ix_order_id` (`order_id`),
    INDEX `ix_created_at` (`created_at`),
    INDEX `ix_updated_at` (`updated_at`)
)
ENGINE = InnoDB DEFAULT CHARSET=utf8 COMMENT '订单表';