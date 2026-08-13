-- ============================================================
-- 流动性压力测试及风险缓释 — 数据库表
-- ============================================================

-- 1. G21流动性期限缺口数据表
DROP TABLE IF EXISTS `ialmd_g21_gap`;
CREATE TABLE `ialmd_g21_gap` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `report_period` VARCHAR(20) NOT NULL COMMENT '报告期，如2025Q2',
    `item_code` VARCHAR(64) NOT NULL COMMENT '科目编码',
    `item_name` VARCHAR(128) NOT NULL COMMENT '科目名称',
    `category` VARCHAR(32) NOT NULL COMMENT '分类: ASSET(资产端)/LIABILITY(负债端)/OFF_BALANCE(表外)',
    `overnight_amount` DECIMAL(24,4) DEFAULT 0 COMMENT '隔夜金额(万元)',
    `day7_amount` DECIMAL(24,4) DEFAULT 0 COMMENT '7天金额(万元)',
    `day14_amount` DECIMAL(24,4) DEFAULT 0 COMMENT '14天金额(万元)',
    `month1_amount` DECIMAL(24,4) DEFAULT 0 COMMENT '1个月金额(万元)',
    `month3_amount` DECIMAL(24,4) DEFAULT 0 COMMENT '3个月金额(万元)',
    `month6_amount` DECIMAL(24,4) DEFAULT 0 COMMENT '6个月金额(万元)',
    `year1_amount` DECIMAL(24,4) DEFAULT 0 COMMENT '1年金额(万元)',
    `year5_amount` DECIMAL(24,4) DEFAULT 0 COMMENT '5年以上金额(万元)',
    `unlimited_amount` DECIMAL(24,4) DEFAULT 0 COMMENT '无期限金额(万元)',
    `total_amount` DECIMAL(24,4) DEFAULT 0 COMMENT '合计金额(万元)',
    `status` TINYINT NOT NULL DEFAULT 1 COMMENT '状态: 0禁用 1启用',
    `is_deleted` TINYINT NOT NULL DEFAULT 0 COMMENT '软删除: 0正常 1已删除',
    `created_by` BIGINT DEFAULT NULL COMMENT '创建人ID',
    `updated_by` BIGINT DEFAULT NULL COMMENT '更新人ID',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    INDEX `idx_report_period` (`report_period`),
    INDEX `idx_category` (`category`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='G21流动性期限缺口数据';

-- 2. HQLA优质流动性资产表
DROP TABLE IF EXISTS `ialmd_hqla_asset`;
CREATE TABLE `ialmd_hqla_asset` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `report_period` VARCHAR(20) NOT NULL COMMENT '报告期，如2025Q2',
    `asset_level` VARCHAR(16) NOT NULL COMMENT '资产层级: LEVEL1/LEVEL2A/LEVEL2B',
    `asset_name` VARCHAR(256) NOT NULL COMMENT '资产名称',
    `asset_type` VARCHAR(64) NOT NULL COMMENT '资产类型: 现金/国债/政金债/地方债/信用债/准备金/央票/股票/其他',
    `face_value` DECIMAL(24,4) DEFAULT 0 COMMENT '面值(万元)',
    `market_value` DECIMAL(24,4) DEFAULT 0 COMMENT '市场价值(万元)',
    `haircut_rate` DECIMAL(6,4) DEFAULT 0 COMMENT '扣减率(小数，如0.15=15%)',
    `discounted_value` DECIMAL(24,4) DEFAULT 0 COMMENT '折后价值(万元) = market_value*(1-haircut_rate)',
    `hqla_value` DECIMAL(24,4) DEFAULT 0 COMMENT '计入HQLA金额(万元)',
    `status` TINYINT NOT NULL DEFAULT 1 COMMENT '状态: 0禁用 1启用',
    `is_deleted` TINYINT NOT NULL DEFAULT 0 COMMENT '软删除: 0正常 1已删除',
    `created_by` BIGINT DEFAULT NULL COMMENT '创建人ID',
    `updated_by` BIGINT DEFAULT NULL COMMENT '更新人ID',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    INDEX `idx_report_period` (`report_period`),
    INDEX `idx_asset_level` (`asset_level`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='HQLA优质流动性资产';

-- 3. 压力测试版本表（中枢）
DROP TABLE IF EXISTS `ialmd_stress_version`;
CREATE TABLE `ialmd_stress_version` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `version_code` VARCHAR(32) NOT NULL COMMENT '版本编号，如V2025Q2-005',
    `version_name` VARCHAR(256) NOT NULL COMMENT '版本名称',
    `version_desc` TEXT COMMENT '版本描述',
    `version_status` VARCHAR(20) NOT NULL DEFAULT 'DRAFT' COMMENT '版本状态: DRAFT/PUBLISHED/ARCHIVED',
    `g21_period` VARCHAR(20) NOT NULL COMMENT '引用的G21报告期',
    `hqla_period` VARCHAR(20) NOT NULL COMMENT '引用的HQLA快照期',
    `scenario_type` VARCHAR(32) NOT NULL COMMENT '情景类型: BASE/MILD/MODERATE/SEVERE/CUSTOM',
    `test_window` INT NOT NULL DEFAULT 30 COMMENT '测试窗口(天)',
    `scenario_params_json` JSON COMMENT '情景参数JSON',
    `benchmark_results_json` JSON COMMENT '基准测试结果JSON',
    `stress_results_json` JSON COMMENT '压力测试结果JSON (含多情景对比)',
    `cash_flow_gaps_json` JSON COMMENT '现金流缺口分析JSON',
    `mitigation_measures_json` JSON COMMENT '缓释措施JSON',
    `mitigation_results_json` JSON COMMENT '缓释后指标JSON',
    `status` TINYINT NOT NULL DEFAULT 1 COMMENT '状态: 0禁用 1启用',
    `is_deleted` TINYINT NOT NULL DEFAULT 0 COMMENT '软删除: 0正常 1已删除',
    `created_by` BIGINT DEFAULT NULL COMMENT '创建人ID',
    `updated_by` BIGINT DEFAULT NULL COMMENT '更新人ID',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    INDEX `idx_version_code` (`version_code`),
    INDEX `idx_version_status` (`version_status`),
    INDEX `idx_g21_period` (`g21_period`),
    INDEX `idx_hqla_period` (`hqla_period`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='压力测试版本';
