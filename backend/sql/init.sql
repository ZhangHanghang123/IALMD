-- ============================================================
-- 银行经营智能分析平台 (IALMD) — 数据库初始化脚本
-- 标准化规范:
--   系统表: sys_ 前缀   业务表: IALMD_ 前缀
--   公共字段: id/status/is_deleted/created_by/updated_by/created_at/updated_at
--   状态码值: TINYINT status(0=停用/禁用, 1=启用/正常)
--             VARCHAR exec_status(PENDING/RUNNING/COMPLETED/FAILED)
--             VARCHAR verify_status(PENDING/APPROVED/REJECTED)
-- ============================================================

USE IALMD;

-- ============================================================
-- 1. 系统管理模块 (sys_)
-- ============================================================

-- 1.1 用户表
CREATE TABLE IF NOT EXISTS sys_user (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    username        VARCHAR(64)   NOT NULL COMMENT '登录名',
    password_hash   VARCHAR(256)  NOT NULL COMMENT '密码哈希(BCrypt)',
    real_name       VARCHAR(64)   NOT NULL DEFAULT '' COMMENT '真实姓名',
    email           VARCHAR(128)  NOT NULL DEFAULT '' COMMENT '邮箱',
    phone           VARCHAR(20)   NOT NULL DEFAULT '' COMMENT '手机号',
    institution_id  BIGINT        DEFAULT NULL COMMENT '所属银行机构ID',
    avatar_url      VARCHAR(256)  NOT NULL DEFAULT '' COMMENT '头像URL',
    last_login_at   DATETIME      DEFAULT NULL COMMENT '最后登录时间',
    status          TINYINT       NOT NULL DEFAULT 1 COMMENT '状态: 0=禁用, 1=正常',
    is_deleted      TINYINT       NOT NULL DEFAULT 0 COMMENT '逻辑删除: 0=未删除, 1=已删除',
    created_by      BIGINT        DEFAULT NULL COMMENT '创建人ID',
    updated_by      BIGINT        DEFAULT NULL COMMENT '更新人ID',
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_username (username),
    INDEX idx_institution (institution_id),
    INDEX idx_status (status, is_deleted)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='用户表';

-- 1.2 角色表
CREATE TABLE IF NOT EXISTS sys_role (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    role_name       VARCHAR(64)   NOT NULL COMMENT '角色名称',
    role_code       VARCHAR(64)   NOT NULL COMMENT '角色编码: ANALYST/SENIOR_ANALYST/MANAGER/ADMIN/ADVISOR',
    description     VARCHAR(256)  NOT NULL DEFAULT '' COMMENT '角色描述',
    sort_order      INT           NOT NULL DEFAULT 0 COMMENT '排序号',
    status          TINYINT       NOT NULL DEFAULT 1 COMMENT '状态: 0=停用, 1=启用',
    is_deleted      TINYINT       NOT NULL DEFAULT 0 COMMENT '逻辑删除: 0=未删除, 1=已删除',
    created_by      BIGINT        DEFAULT NULL COMMENT '创建人ID',
    updated_by      BIGINT        DEFAULT NULL COMMENT '更新人ID',
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_role_code (role_code),
    INDEX idx_status (status, is_deleted)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='角色表';

-- 1.3 用户角色关联表
CREATE TABLE IF NOT EXISTS sys_user_role (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    user_id         BIGINT        NOT NULL COMMENT '用户ID',
    role_id         BIGINT        NOT NULL COMMENT '角色ID',
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    UNIQUE KEY uk_user_role (user_id, role_id),
    INDEX idx_role (role_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='用户角色关联表';

-- 1.4 权限表
CREATE TABLE IF NOT EXISTS sys_permission (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    permission_code VARCHAR(128)  NOT NULL COMMENT '权限编码: report:view, indicator:edit',
    permission_name VARCHAR(128)  NOT NULL COMMENT '权限名称',
    parent_id       BIGINT        NOT NULL DEFAULT 0 COMMENT '父权限ID, 0=顶级',
    permission_type VARCHAR(16)   NOT NULL DEFAULT 'MENU' COMMENT '权限类型: MENU/BUTTON/API',
    sort_order      INT           NOT NULL DEFAULT 0 COMMENT '排序号',
    status          TINYINT       NOT NULL DEFAULT 1 COMMENT '状态: 0=停用, 1=启用',
    is_deleted      TINYINT       NOT NULL DEFAULT 0 COMMENT '逻辑删除: 0=未删除, 1=已删除',
    created_by      BIGINT        DEFAULT NULL COMMENT '创建人ID',
    updated_by      BIGINT        DEFAULT NULL COMMENT '更新人ID',
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_permission_code (permission_code),
    INDEX idx_parent (parent_id),
    INDEX idx_status (status, is_deleted)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='权限表';

-- 1.5 角色权限关联表
CREATE TABLE IF NOT EXISTS sys_role_permission (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    role_id         BIGINT        NOT NULL COMMENT '角色ID',
    permission_id   BIGINT        NOT NULL COMMENT '权限ID',
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    UNIQUE KEY uk_role_permission (role_id, permission_id),
    INDEX idx_permission (permission_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='角色权限关联表';

-- ============================================================
-- 2. 银行机构模块 (IALMD_)
-- ============================================================

-- 2.1 银行机构表
CREATE TABLE IF NOT EXISTS IALMD_bank_institution (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    bank_name       VARCHAR(128)  NOT NULL COMMENT '银行全称',
    short_name      VARCHAR(64)   NOT NULL DEFAULT '' COMMENT '银行简称',
    bank_code       VARCHAR(32)   NOT NULL DEFAULT '' COMMENT '银行代码: ICBC/CCB/ABC/BOC/...',
    bank_type       VARCHAR(32)   NOT NULL COMMENT '银行类型: BIG_STATE/POLICY/JOINT_STOCK/CITY/RURAL',
    stock_code      VARCHAR(16)   NOT NULL DEFAULT '' COMMENT '股票代码',
    listing_market  VARCHAR(16)   NOT NULL DEFAULT '' COMMENT '上市地: A/H/A+H/UNLISTED',
    total_assets    DECIMAL(20,2) DEFAULT NULL COMMENT '最新总资产(亿元)',
    website         VARCHAR(256)  NOT NULL DEFAULT '' COMMENT '官网URL',
    status          TINYINT       NOT NULL DEFAULT 1 COMMENT '状态: 0=停用, 1=启用',
    is_deleted      TINYINT       NOT NULL DEFAULT 0 COMMENT '逻辑删除: 0=未删除, 1=已删除',
    created_by      BIGINT        DEFAULT NULL COMMENT '创建人ID',
    updated_by      BIGINT        DEFAULT NULL COMMENT '更新人ID',
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_bank_code (bank_code),
    INDEX idx_bank_type (bank_type),
    INDEX idx_status (status, is_deleted)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='银行机构表';

-- ============================================================
-- 3. 报告采集模块 (IALMD_)
-- ============================================================

-- 3.1 报告记录表
CREATE TABLE IF NOT EXISTS IALMD_report_record (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    institution_id  BIGINT        NOT NULL COMMENT '银行机构ID',
    report_type     VARCHAR(32)   NOT NULL COMMENT '报告类型: ANNUAL/HALF/Q1/Q3/EXPRESS/CAPITAL/LIQUIDITY/ESG/INCLUSIVE/CONSUMER/GREEN',
    report_year     INT           NOT NULL COMMENT '报告年度',
    report_period   VARCHAR(16)   NOT NULL DEFAULT 'FY' COMMENT '报告期间: Q1/Q2/Q3/Q4/H1/FY',
    publish_date    DATE          DEFAULT NULL COMMENT '发布日期',
    report_title    VARCHAR(512)  NOT NULL DEFAULT '' COMMENT '报告标题',
    collect_status  VARCHAR(16)   NOT NULL DEFAULT 'PENDING' COMMENT '采集状态: PENDING/DOWNLOADING/DOWNLOADED/PARSING/PARSED/FAILED',
    page_count      INT           NOT NULL DEFAULT 0 COMMENT '报告页数',
    retry_count     INT           NOT NULL DEFAULT 0 COMMENT '重试次数',
    source_url      VARCHAR(1024) NOT NULL DEFAULT '' COMMENT '源文件URL',
    error_msg       TEXT          DEFAULT NULL COMMENT '错误信息',
    collected_at    DATETIME      DEFAULT NULL COMMENT '采集完成时间',
    status          TINYINT       NOT NULL DEFAULT 1 COMMENT '状态: 0=作废, 1=正常',
    is_deleted      TINYINT       NOT NULL DEFAULT 0 COMMENT '逻辑删除: 0=未删除, 1=已删除',
    created_by      BIGINT        DEFAULT NULL COMMENT '创建人ID',
    updated_by      BIGINT        DEFAULT NULL COMMENT '更新人ID',
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_report (institution_id, report_type, report_year, report_period),
    INDEX idx_collect_status (collect_status),
    INDEX idx_publish_date (publish_date),
    INDEX idx_status (status, is_deleted)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='报告记录表';

-- 3.2 报告文件表
CREATE TABLE IF NOT EXISTS IALMD_report_file (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    report_id       BIGINT        NOT NULL COMMENT '报告记录ID',
    file_name       VARCHAR(256)  NOT NULL COMMENT '文件名',
    file_type       VARCHAR(16)   NOT NULL COMMENT '文件类型: PDF/HTML/DOCX',
    file_size       BIGINT        NOT NULL DEFAULT 0 COMMENT '文件大小(字节)',
    file_hash       VARCHAR(64)   NOT NULL DEFAULT '' COMMENT '文件SHA256哈希',
    storage_path    VARCHAR(512)  NOT NULL COMMENT '对象存储路径(MinIO/COS)',
    download_url    VARCHAR(1024) NOT NULL DEFAULT '' COMMENT '下载URL',
    status          TINYINT       NOT NULL DEFAULT 1 COMMENT '状态: 0=失效, 1=正常',
    is_deleted      TINYINT       NOT NULL DEFAULT 0 COMMENT '逻辑删除: 0=未删除, 1=已删除',
    created_by      BIGINT        DEFAULT NULL COMMENT '创建人ID',
    updated_by      BIGINT        DEFAULT NULL COMMENT '更新人ID',
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_report (report_id),
    INDEX idx_status (status, is_deleted)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='报告文件表';

-- 3.3 采集任务表
CREATE TABLE IF NOT EXISTS IALMD_collect_task (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    task_type       VARCHAR(32)   NOT NULL COMMENT '任务类型: CRAWL/DOWNLOAD/PARSE/EXTRACT',
    target_id       BIGINT        DEFAULT NULL COMMENT '目标ID(银行ID或报告ID)',
    celery_task_id  VARCHAR(128)  NOT NULL DEFAULT '' COMMENT 'Celery异步任务ID',
    exec_status     VARCHAR(16)   NOT NULL DEFAULT 'PENDING' COMMENT '执行状态: PENDING/RUNNING/COMPLETED/FAILED',
    progress        DECIMAL(5,2)  NOT NULL DEFAULT 0.00 COMMENT '进度百分比',
    result_json     JSON          DEFAULT NULL COMMENT '执行结果摘要',
    error_msg       TEXT          DEFAULT NULL COMMENT '错误信息',
    started_at      DATETIME      DEFAULT NULL COMMENT '开始执行时间',
    finished_at     DATETIME      DEFAULT NULL COMMENT '完成时间',
    status          TINYINT       NOT NULL DEFAULT 1 COMMENT '状态: 0=作废, 1=正常',
    is_deleted      TINYINT       NOT NULL DEFAULT 0 COMMENT '逻辑删除: 0=未删除, 1=已删除',
    created_by      BIGINT        DEFAULT NULL COMMENT '创建人ID',
    updated_by      BIGINT        DEFAULT NULL COMMENT '更新人ID',
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_exec_status (exec_status),
    INDEX idx_target (target_id),
    INDEX idx_status (status, is_deleted)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='采集任务表';

-- ============================================================
-- 4. 经营指标模块 (IALMD_)
-- ============================================================

-- 4.1 指标定义表
CREATE TABLE IF NOT EXISTS IALMD_indicator_define (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    indicator_code  VARCHAR(64)   NOT NULL COMMENT '指标编码: NIM/NPL/CET1/ROA/ROE/...',
    indicator_name  VARCHAR(128)  NOT NULL COMMENT '指标中文名称',
    indicator_alias VARCHAR(256)  NOT NULL DEFAULT '' COMMENT '别名(逗号分隔)',
    category_code   VARCHAR(32)   NOT NULL COMMENT '分类编码: SCALE/PROFIT/RISK/CAPITAL/LIQUIDITY/ESG',
    unit            VARCHAR(16)   NOT NULL DEFAULT '' COMMENT '单位: %/亿元/倍/户',
    decimal_places  TINYINT       NOT NULL DEFAULT 2 COMMENT '小数位数',
    calc_formula    VARCHAR(512)  NOT NULL DEFAULT '' COMMENT '计算公式',
    sort_order      INT           NOT NULL DEFAULT 0 COMMENT '排序号',
    status          TINYINT       NOT NULL DEFAULT 1 COMMENT '状态: 0=停用, 1=启用',
    is_deleted      TINYINT       NOT NULL DEFAULT 0 COMMENT '逻辑删除: 0=未删除, 1=已删除',
    created_by      BIGINT        DEFAULT NULL COMMENT '创建人ID',
    updated_by      BIGINT        DEFAULT NULL COMMENT '更新人ID',
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_indicator_code (indicator_code),
    INDEX idx_category (category_code),
    INDEX idx_status (status, is_deleted)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='指标定义表';

-- 4.2 指标值表
CREATE TABLE IF NOT EXISTS IALMD_indicator_value (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    indicator_id    BIGINT        NOT NULL COMMENT '指标定义ID',
    institution_id  BIGINT        NOT NULL COMMENT '银行机构ID',
    report_id       BIGINT        NOT NULL COMMENT '来源报告ID',
    value_numeric   DECIMAL(24,6) DEFAULT NULL COMMENT '指标数值',
    value_text      VARCHAR(128)  NOT NULL DEFAULT '' COMMENT '指标文本值',
    report_year     INT           NOT NULL COMMENT '数据年份',
    report_period   VARCHAR(16)   NOT NULL DEFAULT 'FY' COMMENT '数据期间: Q1/Q2/Q3/Q4/H1/FY',
    confidence      DECIMAL(5,4)  NOT NULL DEFAULT 1.0000 COMMENT '抽取置信度(0-1)',
    extract_page    INT           DEFAULT NULL COMMENT '来源页码',
    extract_context TEXT          DEFAULT NULL COMMENT '抽取上下文原文',
    verify_status   VARCHAR(16)   NOT NULL DEFAULT 'PENDING' COMMENT '审核状态: PENDING/APPROVED/REJECTED',
    verified_by     BIGINT        DEFAULT NULL COMMENT '审核人ID',
    verified_at     DATETIME      DEFAULT NULL COMMENT '审核时间',
    status          TINYINT       NOT NULL DEFAULT 1 COMMENT '状态: 0=作废, 1=正常',
    is_deleted      TINYINT       NOT NULL DEFAULT 0 COMMENT '逻辑删除: 0=未删除, 1=已删除',
    created_by      BIGINT        DEFAULT NULL COMMENT '创建人ID',
    updated_by      BIGINT        DEFAULT NULL COMMENT '更新人ID',
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_value (indicator_id, institution_id, report_year, report_period),
    INDEX idx_institution_year (institution_id, report_year),
    INDEX idx_indicator_year (indicator_id, report_year),
    INDEX idx_verify_status (verify_status),
    INDEX idx_status (status, is_deleted)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='指标值表';

-- ============================================================
-- 5. 本体知识模块 (IALMD_)
-- ============================================================

-- 5.1 本体概念表
CREATE TABLE IF NOT EXISTS IALMD_ontology_class (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    class_code      VARCHAR(64)   NOT NULL COMMENT '本体类编码',
    class_name      VARCHAR(128)  NOT NULL COMMENT '本体类名称',
    parent_id       BIGINT        NOT NULL DEFAULT 0 COMMENT '父类ID, 0=根节点',
    class_level     TINYINT       NOT NULL DEFAULT 1 COMMENT '层级: 1=大类, 2=指标, 3=子指标',
    description     TEXT          DEFAULT NULL COMMENT '类描述',
    indicator_id    BIGINT        DEFAULT NULL COMMENT '绑定的指标定义ID',
    status          TINYINT       NOT NULL DEFAULT 1 COMMENT '状态: 0=停用, 1=启用',
    is_deleted      TINYINT       NOT NULL DEFAULT 0 COMMENT '逻辑删除: 0=未删除, 1=已删除',
    created_by      BIGINT        DEFAULT NULL COMMENT '创建人ID',
    updated_by      BIGINT        DEFAULT NULL COMMENT '更新人ID',
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_class_code (class_code),
    INDEX idx_parent (parent_id),
    INDEX idx_indicator (indicator_id),
    INDEX idx_status (status, is_deleted)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='本体概念表';

-- 5.2 本体关系表
CREATE TABLE IF NOT EXISTS IALMD_ontology_relation (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    source_class_id BIGINT        NOT NULL COMMENT '源本体类ID',
    target_class_id BIGINT        NOT NULL COMMENT '目标本体类ID',
    relation_type   VARCHAR(32)   NOT NULL COMMENT '关系类型: PARENT_CHILD/SYNONYM/DEPENDS_ON/COMPUTED_FROM',
    weight          DECIMAL(5,4)  NOT NULL DEFAULT 1.0000 COMMENT '关系权重',
    confidence      DECIMAL(5,4)  NOT NULL DEFAULT 1.0000 COMMENT '置信度(0-1)',
    verify_status   VARCHAR(16)   NOT NULL DEFAULT 'PENDING' COMMENT '审核状态: PENDING/APPROVED/REJECTED',
    verified_by     BIGINT        DEFAULT NULL COMMENT '审核人ID',
    verified_at     DATETIME      DEFAULT NULL COMMENT '审核时间',
    status          TINYINT       NOT NULL DEFAULT 1 COMMENT '状态: 0=作废, 1=正常',
    is_deleted      TINYINT       NOT NULL DEFAULT 0 COMMENT '逻辑删除: 0=未删除, 1=已删除',
    created_by      BIGINT        DEFAULT NULL COMMENT '创建人ID',
    updated_by      BIGINT        DEFAULT NULL COMMENT '更新人ID',
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_relation (source_class_id, target_class_id, relation_type),
    INDEX idx_target (target_class_id),
    INDEX idx_verify_status (verify_status),
    INDEX idx_status (status, is_deleted)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='本体关系表';

-- 5.3 指标异构映射表
CREATE TABLE IF NOT EXISTS IALMD_indicator_mapping (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    institution_id  BIGINT        NOT NULL COMMENT '银行机构ID',
    local_name      VARCHAR(256)  NOT NULL COMMENT '银行本地指标名称',
    ontology_class_id BIGINT      NOT NULL COMMENT '映射的本体类ID',
    mapping_rule    VARCHAR(32)   NOT NULL DEFAULT 'EXACT' COMMENT '映射规则: EXACT/REGEX/LLM/MANUAL',
    confidence      DECIMAL(5,4)  NOT NULL DEFAULT 1.0000 COMMENT '映射置信度(0-1)',
    verify_status   VARCHAR(16)   NOT NULL DEFAULT 'PENDING' COMMENT '审核状态: PENDING/APPROVED/REJECTED',
    verified_by     BIGINT        DEFAULT NULL COMMENT '审核人ID',
    verified_at     DATETIME      DEFAULT NULL COMMENT '审核时间',
    status          TINYINT       NOT NULL DEFAULT 1 COMMENT '状态: 0=作废, 1=正常',
    is_deleted      TINYINT       NOT NULL DEFAULT 0 COMMENT '逻辑删除: 0=未删除, 1=已删除',
    created_by      BIGINT        DEFAULT NULL COMMENT '创建人ID',
    updated_by      BIGINT        DEFAULT NULL COMMENT '更新人ID',
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_mapping (institution_id, local_name),
    INDEX idx_ontology (ontology_class_id),
    INDEX idx_verify_status (verify_status),
    INDEX idx_status (status, is_deleted)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='指标异构映射表';

-- ============================================================
-- 6. 工作流模块 (IALMD_)
-- ============================================================

-- 6.1 工作流定义表
CREATE TABLE IF NOT EXISTS IALMD_workflow_def (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    workflow_name   VARCHAR(128)  NOT NULL COMMENT '工作流名称',
    workflow_code   VARCHAR(64)   NOT NULL COMMENT '工作流编码',
    description     TEXT          DEFAULT NULL COMMENT '工作流说明',
    node_json       JSON          NOT NULL COMMENT '节点DAG图定义',
    trigger_type    VARCHAR(16)   NOT NULL DEFAULT 'MANUAL' COMMENT '触发方式: MANUAL/SCHEDULED/EVENT',
    cron_expr       VARCHAR(64)   NOT NULL DEFAULT '' COMMENT '定时触发CRON表达式',
    status          TINYINT       NOT NULL DEFAULT 1 COMMENT '状态: 0=停用, 1=启用',
    is_deleted      TINYINT       NOT NULL DEFAULT 0 COMMENT '逻辑删除: 0=未删除, 1=已删除',
    created_by      BIGINT        DEFAULT NULL COMMENT '创建人ID',
    updated_by      BIGINT        DEFAULT NULL COMMENT '更新人ID',
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_workflow_code (workflow_code),
    INDEX idx_status (status, is_deleted)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='工作流定义表';

-- 6.2 工作流执行表
CREATE TABLE IF NOT EXISTS IALMD_workflow_exec (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    workflow_id     BIGINT        NOT NULL COMMENT '工作流定义ID',
    exec_status     VARCHAR(16)   NOT NULL DEFAULT 'PENDING' COMMENT '执行状态: PENDING/RUNNING/COMPLETED/FAILED/CANCELLED',
    input_json      JSON          DEFAULT NULL COMMENT '输入参数',
    output_json     JSON          DEFAULT NULL COMMENT '输出结果',
    error_msg       TEXT          DEFAULT NULL COMMENT '错误信息',
    started_at      DATETIME      DEFAULT NULL COMMENT '开始执行时间',
    finished_at     DATETIME      DEFAULT NULL COMMENT '完成时间',
    triggered_by    BIGINT        DEFAULT NULL COMMENT '触发人ID',
    status          TINYINT       NOT NULL DEFAULT 1 COMMENT '状态: 0=作废, 1=正常',
    is_deleted      TINYINT       NOT NULL DEFAULT 0 COMMENT '逻辑删除: 0=未删除, 1=已删除',
    created_by      BIGINT        DEFAULT NULL COMMENT '创建人ID',
    updated_by      BIGINT        DEFAULT NULL COMMENT '更新人ID',
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_workflow (workflow_id),
    INDEX idx_exec_status (exec_status),
    INDEX idx_status (status, is_deleted)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='工作流执行表';

-- 6.3 工作流节点执行表
CREATE TABLE IF NOT EXISTS IALMD_workflow_node_exec (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    exec_id         BIGINT        NOT NULL COMMENT '工作流执行ID',
    node_id         VARCHAR(64)   NOT NULL COMMENT '节点ID',
    node_type       VARCHAR(32)   NOT NULL COMMENT '节点类型: EXTRACT/CALC/BENCHMARK/ATTRIBUTE/REPORT',
    agent_type      VARCHAR(32)   NOT NULL DEFAULT '' COMMENT 'Agent类型',
    exec_status     VARCHAR(16)   NOT NULL DEFAULT 'PENDING' COMMENT '执行状态: PENDING/RUNNING/COMPLETED/FAILED/SKIPPED',
    input_json      JSON          DEFAULT NULL COMMENT '输入数据',
    output_json     JSON          DEFAULT NULL COMMENT '输出数据',
    error_msg       TEXT          DEFAULT NULL COMMENT '错误信息',
    started_at      DATETIME      DEFAULT NULL COMMENT '开始执行时间',
    finished_at     DATETIME      DEFAULT NULL COMMENT '完成时间',
    status          TINYINT       NOT NULL DEFAULT 1 COMMENT '状态: 0=作废, 1=正常',
    is_deleted      TINYINT       NOT NULL DEFAULT 0 COMMENT '逻辑删除: 0=未删除, 1=已删除',
    created_by      BIGINT        DEFAULT NULL COMMENT '创建人ID',
    updated_by      BIGINT        DEFAULT NULL COMMENT '更新人ID',
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_exec (exec_id),
    INDEX idx_exec_status (exec_status),
    INDEX idx_status (status, is_deleted)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='工作流节点执行表';

-- ============================================================
-- 7. 智能对话模块 (IALMD_)
-- ============================================================

-- 7.1 对话会话表
CREATE TABLE IF NOT EXISTS IALMD_chat_session (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    user_id         BIGINT        NOT NULL COMMENT '用户ID',
    session_title   VARCHAR(256)  NOT NULL DEFAULT '新对话' COMMENT '会话标题',
    session_type    VARCHAR(32)   NOT NULL DEFAULT 'ANALYSIS' COMMENT '会话类型: ANALYSIS/COMPARE/ATTRIBUTION/REPORT',
    context_json    JSON          DEFAULT NULL COMMENT '对话上下文(筛选条件/银行/指标)',
    message_count   INT           NOT NULL DEFAULT 0 COMMENT '消息数量',
    is_archived     TINYINT       NOT NULL DEFAULT 0 COMMENT '是否归档: 0=否, 1=是',
    status          TINYINT       NOT NULL DEFAULT 1 COMMENT '状态: 0=已删除, 1=正常',
    is_deleted      TINYINT       NOT NULL DEFAULT 0 COMMENT '逻辑删除: 0=未删除, 1=已删除',
    created_by      BIGINT        DEFAULT NULL COMMENT '创建人ID',
    updated_by      BIGINT        DEFAULT NULL COMMENT '更新人ID',
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_user (user_id),
    INDEX idx_updated (updated_at),
    INDEX idx_status (status, is_deleted)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='对话会话表';

-- 7.2 对话消息表
CREATE TABLE IF NOT EXISTS IALMD_chat_message (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    session_id      BIGINT        NOT NULL COMMENT '对话会话ID',
    role            VARCHAR(16)   NOT NULL COMMENT '消息角色: USER/ASSISTANT/SYSTEM',
    content         TEXT          NOT NULL COMMENT '消息内容',
    message_type    VARCHAR(32)   NOT NULL DEFAULT 'TEXT' COMMENT '消息类型: TEXT/CHART/TABLE/REPORT_CARD',
    chart_json      JSON          DEFAULT NULL COMMENT 'ECharts图表配置',
    table_json      JSON          DEFAULT NULL COMMENT '表格数据',
    trace_json      JSON          DEFAULT NULL COMMENT '溯源数据(指标来源/报告等)',
    tokens_used     INT           NOT NULL DEFAULT 0 COMMENT '消耗Token数',
    model_name      VARCHAR(64)   NOT NULL DEFAULT '' COMMENT '模型名称',
    status          TINYINT       NOT NULL DEFAULT 1 COMMENT '状态: 0=已删除, 1=正常',
    is_deleted      TINYINT       NOT NULL DEFAULT 0 COMMENT '逻辑删除: 0=未删除, 1=已删除',
    created_by      BIGINT        DEFAULT NULL COMMENT '创建人ID',
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_session (session_id, created_at),
    INDEX idx_status (status, is_deleted)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='对话消息表';

-- ============================================================
-- 8. 同业对标模块 (IALMD_)
-- ============================================================

-- 8.1 同业对标结果表
CREATE TABLE IF NOT EXISTS IALMD_benchmark_compare (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    indicator_id    BIGINT        NOT NULL COMMENT '指标定义ID',
    compare_type    VARCHAR(32)   NOT NULL COMMENT '对比类型: SINGLE/GROUP/TREND/RADAR',
    institution_json JSON         DEFAULT NULL COMMENT '对比银行ID列表',
    result_json     JSON          NOT NULL COMMENT '对比结果(排名/分位/均值/中位数)',
    report_year     INT           NOT NULL COMMENT '数据年份',
    report_period   VARCHAR(16)   NOT NULL DEFAULT 'FY' COMMENT '数据期间: Q1/Q2/Q3/Q4/H1/FY',
    status          TINYINT       NOT NULL DEFAULT 1 COMMENT '状态: 0=作废, 1=正常',
    is_deleted      TINYINT       NOT NULL DEFAULT 0 COMMENT '逻辑删除: 0=未删除, 1=已删除',
    created_by      BIGINT        DEFAULT NULL COMMENT '创建人ID',
    updated_by      BIGINT        DEFAULT NULL COMMENT '更新人ID',
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_indicator_year (indicator_id, report_year),
    INDEX idx_status (status, is_deleted)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='同业对标结果表';

-- ============================================================
-- 9. 系统日志模块 (sys_)
-- ============================================================

-- 9.1 审计日志表（只追加，不修改）
CREATE TABLE IF NOT EXISTS sys_audit_log (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    user_id         BIGINT        DEFAULT NULL COMMENT '操作人ID',
    username        VARCHAR(64)   NOT NULL DEFAULT '' COMMENT '操作人登录名(冗余, 用户删除后仍可追溯)',
    action          VARCHAR(64)   NOT NULL COMMENT '操作类型: LOGIN/VIEW/EXPORT/CREATE/UPDATE/DELETE',
    target_type     VARCHAR(32)   NOT NULL DEFAULT '' COMMENT '目标类型: REPORT/INDICATOR/WORKFLOW/ONTOLOGY/USER',
    target_id       BIGINT        DEFAULT NULL COMMENT '目标ID',
    target_name     VARCHAR(256)  NOT NULL DEFAULT '' COMMENT '目标名称(冗余)',
    detail_json     JSON          DEFAULT NULL COMMENT '操作详情',
    ip_address      VARCHAR(45)   NOT NULL DEFAULT '' COMMENT '客户端IP',
    user_agent      VARCHAR(512)  NOT NULL DEFAULT '' COMMENT '客户端User-Agent',
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_user_time (user_id, created_at),
    INDEX idx_action_time (action, created_at),
    INDEX idx_target (target_type, target_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='审计日志表';

-- ============================================================
-- 10. LLM 配置模块 (sys_)
-- ============================================================

-- 10.1 LLM 配置表
CREATE TABLE IF NOT EXISTS sys_llm_config (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    provider_name   VARCHAR(64)   NOT NULL COMMENT '服务商名称（如DeepSeek/Qwen/OpenAI）',
    provider_code   VARCHAR(32)   NOT NULL COMMENT '服务商编码（deepseek/qwen/openai/mock）',
    api_key         VARCHAR(512)  NOT NULL DEFAULT '' COMMENT 'API密钥',
    base_url        VARCHAR(256)  NOT NULL DEFAULT '' COMMENT 'API地址',
    model_name      VARCHAR(128)  NOT NULL DEFAULT '' COMMENT '模型名称',
    temperature     DECIMAL(3,2)  NOT NULL DEFAULT 0.10 COMMENT '温度参数',
    max_tokens      INT           NOT NULL DEFAULT 4096 COMMENT '最大Token数',
    is_enabled      TINYINT       NOT NULL DEFAULT 0 COMMENT '是否启用: 0=禁用,1=启用',
    is_default      TINYINT       NOT NULL DEFAULT 0 COMMENT '是否默认: 0=否,1=是',
    sort_order      INT           NOT NULL DEFAULT 0 COMMENT '排序号',
    remark          VARCHAR(256)  NOT NULL DEFAULT '' COMMENT '备注',
    status          TINYINT       NOT NULL DEFAULT 1 COMMENT '状态: 0=删除,1=正常',
    created_by      BIGINT        DEFAULT NULL COMMENT '创建人ID',
    updated_by      BIGINT        DEFAULT NULL COMMENT '更新人ID',
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_provider_code (provider_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='LLM配置表';

-- 默认种子数据
INSERT IGNORE INTO sys_llm_config (provider_name, provider_code, api_key, base_url, model_name, temperature, max_tokens, is_enabled, is_default, sort_order, remark, status, created_at, updated_at) VALUES
('DeepSeek',   'deepseek', '', 'https://api.deepseek.com/v1',                            'deepseek-chat', 0.10, 4096, 0, 0,  1, 'DeepSeek大模型，性价比高', 1, NOW(), NOW()),
('通义千问',   'qwen',     '', 'https://dashscope.aliyuncs.com/compatible-mode/v1',      'qwen-plus',     0.10, 4096, 0, 0,  2, '阿里云通义千问', 1, NOW(), NOW()),
('OpenAI',     'openai',   '', 'https://api.openai.com/v1',                              'gpt-4o',        0.10, 4096, 0, 0,  3, 'OpenAI GPT-4o', 1, NOW(), NOW()),
('模拟模式',   'mock',     '', '',                                                        '',              0.10, 4096, 1, 1, 99, '无API Key时的兜底模拟模式', 1, NOW(), NOW());

-- ============================================================
-- 1.7 字典类型表
-- ============================================================
CREATE TABLE IF NOT EXISTS sys_dict_type (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    dict_name       VARCHAR(128)  NOT NULL COMMENT '字典名称',
    dict_code       VARCHAR(64)   NOT NULL COMMENT '字典编码(唯一)',
    description     VARCHAR(256)  NOT NULL DEFAULT '' COMMENT '字典描述',
    sort_order      INT           NOT NULL DEFAULT 0 COMMENT '排序号',
    status          TINYINT       NOT NULL DEFAULT 1 COMMENT '状态: 0=禁用, 1=正常',
    is_deleted      TINYINT       NOT NULL DEFAULT 0 COMMENT '逻辑删除: 0=未删除, 1=已删除',
    created_by      BIGINT        DEFAULT NULL COMMENT '创建人ID',
    updated_by      BIGINT        DEFAULT NULL COMMENT '更新人ID',
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_dict_code (dict_code),
    INDEX idx_status (status, is_deleted)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='字典类型表';

-- 1.8 字典数据表
CREATE TABLE IF NOT EXISTS sys_dict_data (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    dict_type_id    BIGINT        NOT NULL COMMENT '字典类型ID',
    dict_label      VARCHAR(128)  NOT NULL COMMENT '字典标签(显示值)',
    dict_value      VARCHAR(128)  NOT NULL COMMENT '字典键值(存储值)',
    dict_key        VARCHAR(64)   NOT NULL COMMENT '字典键名(CODE)',
    sort_order      INT           NOT NULL DEFAULT 0 COMMENT '排序号',
    status          TINYINT       NOT NULL DEFAULT 1 COMMENT '状态: 0=禁用, 1=正常',
    is_deleted      TINYINT       NOT NULL DEFAULT 0 COMMENT '逻辑删除: 0=未删除, 1=已删除',
    created_by      BIGINT        DEFAULT NULL COMMENT '创建人ID',
    updated_by      BIGINT        DEFAULT NULL COMMENT '更新人ID',
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_dict_type_key (dict_type_id, dict_key),
    INDEX idx_status (status, is_deleted)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='字典数据表';

-- ============================================================
-- 默认字典种子数据
-- ============================================================

-- 通用状态
INSERT IGNORE INTO sys_dict_type (dict_name, dict_code, description, sort_order, status, is_deleted, created_at, updated_at) VALUES
('通用状态', 'common_status', '通用状态枚举', 1, 1, 0, NOW(), NOW());

INSERT IGNORE INTO sys_dict_data (dict_type_id, dict_label, dict_value, dict_key, sort_order, status, is_deleted, created_at, updated_at) VALUES
((SELECT id FROM sys_dict_type WHERE dict_code='common_status'), '禁用', '0', 'DISABLED', 1, 1, 0, NOW(), NOW()),
((SELECT id FROM sys_dict_type WHERE dict_code='common_status'), '正常', '1', 'ENABLED', 2, 1, 0, NOW(), NOW());

-- 执行状态
INSERT IGNORE INTO sys_dict_type (dict_name, dict_code, description, sort_order, status, is_deleted, created_at, updated_at) VALUES
('执行状态', 'exec_status', '工作流/任务执行状态', 2, 1, 0, NOW(), NOW());

INSERT IGNORE INTO sys_dict_data (dict_type_id, dict_label, dict_value, dict_key, sort_order, status, is_deleted, created_at, updated_at) VALUES
((SELECT id FROM sys_dict_type WHERE dict_code='exec_status'), '待执行', 'PENDING', 'PENDING', 1, 1, 0, NOW(), NOW()),
((SELECT id FROM sys_dict_type WHERE dict_code='exec_status'), '执行中', 'RUNNING', 'RUNNING', 2, 1, 0, NOW(), NOW()),
((SELECT id FROM sys_dict_type WHERE dict_code='exec_status'), '执行成功', 'COMPLETED', 'COMPLETED', 3, 1, 0, NOW(), NOW()),
((SELECT id FROM sys_dict_type WHERE dict_code='exec_status'), '执行失败', 'FAILED', 'FAILED', 4, 1, 0, NOW(), NOW());

-- 审核状态
INSERT IGNORE INTO sys_dict_type (dict_name, dict_code, description, sort_order, status, is_deleted, created_at, updated_at) VALUES
('审核状态', 'verify_status', '审核状态枚举', 3, 1, 0, NOW(), NOW());

INSERT IGNORE INTO sys_dict_data (dict_type_id, dict_label, dict_value, dict_key, sort_order, status, is_deleted, created_at, updated_at) VALUES
((SELECT id FROM sys_dict_type WHERE dict_code='verify_status'), '待审核', 'PENDING', 'PENDING', 1, 1, 0, NOW(), NOW()),
((SELECT id FROM sys_dict_type WHERE dict_code='verify_status'), '已通过', 'APPROVED', 'APPROVED', 2, 1, 0, NOW(), NOW()),
((SELECT id FROM sys_dict_type WHERE dict_code='verify_status'), '已拒绝', 'REJECTED', 'REJECTED', 3, 1, 0, NOW(), NOW());

-- 采集状态
INSERT IGNORE INTO sys_dict_type (dict_name, dict_code, description, sort_order, status, is_deleted, created_at, updated_at) VALUES
('采集状态', 'collect_status', '报告采集状态', 4, 1, 0, NOW(), NOW());

INSERT IGNORE INTO sys_dict_data (dict_type_id, dict_label, dict_value, dict_key, sort_order, status, is_deleted, created_at, updated_at) VALUES
((SELECT id FROM sys_dict_type WHERE dict_code='collect_status'), '待采集', 'PENDING', 'PENDING', 1, 1, 0, NOW(), NOW()),
((SELECT id FROM sys_dict_type WHERE dict_code='collect_status'), '采集中', 'RUNNING', 'RUNNING', 2, 1, 0, NOW(), NOW()),
((SELECT id FROM sys_dict_type WHERE dict_code='collect_status'), '采集完成', 'COMPLETED', 'COMPLETED', 3, 1, 0, NOW(), NOW()),
((SELECT id FROM sys_dict_type WHERE dict_code='collect_status'), '采集失败', 'FAILED', 'FAILED', 4, 1, 0, NOW(), NOW());

-- 保险机构类型
INSERT IGNORE INTO sys_dict_type (dict_name, dict_code, description, sort_order, status, is_deleted, created_at, updated_at) VALUES
('保险机构类型', 'bank_type', '保险机构类型枚举', 5, 1, 0, NOW(), NOW());

INSERT IGNORE INTO sys_dict_data (dict_type_id, dict_label, dict_value, dict_key, sort_order, status, is_deleted, created_at, updated_at) VALUES
((SELECT id FROM sys_dict_type WHERE dict_code='bank_type'), '保险集团', 'GROUP', 'GROUP', 1, 1, 0, NOW(), NOW()),
((SELECT id FROM sys_dict_type WHERE dict_code='bank_type'), '寿险公司', 'LIFE', 'LIFE', 2, 1, 0, NOW(), NOW()),
((SELECT id FROM sys_dict_type WHERE dict_code='bank_type'), '财险公司', 'PNC', 'PNC', 3, 1, 0, NOW(), NOW()),
((SELECT id FROM sys_dict_type WHERE dict_code='bank_type'), '再保险公司', 'REINSURANCE', 'REINSURANCE', 4, 1, 0, NOW(), NOW()),
((SELECT id FROM sys_dict_type WHERE dict_code='bank_type'), '健康险公司', 'HEALTH', 'HEALTH', 5, 1, 0, NOW(), NOW()),
((SELECT id FROM sys_dict_type WHERE dict_code='bank_type'), '养老险公司', 'PENSION', 'PENSION', 6, 1, 0, NOW(), NOW());

-- 报告类型
INSERT IGNORE INTO sys_dict_type (dict_name, dict_code, description, sort_order, status, is_deleted, created_at, updated_at) VALUES
('报告类型', 'report_type', '保险报告类型', 6, 1, 0, NOW(), NOW());

INSERT IGNORE INTO sys_dict_data (dict_type_id, dict_label, dict_value, dict_key, sort_order, status, is_deleted, created_at, updated_at) VALUES
((SELECT id FROM sys_dict_type WHERE dict_code='report_type'), '年度报告', 'ANNUAL', 'ANNUAL', 1, 1, 0, NOW(), NOW()),
((SELECT id FROM sys_dict_type WHERE dict_code='report_type'), '半年度报告', 'HALF_YEAR', 'HALF_YEAR', 2, 1, 0, NOW(), NOW()),
((SELECT id FROM sys_dict_type WHERE dict_code='report_type'), '季度报告', 'QUARTERLY', 'QUARTERLY', 3, 1, 0, NOW(), NOW()),
((SELECT id FROM sys_dict_type WHERE dict_code='report_type'), '偿付能力报告', 'SOLVENCY', 'SOLVENCY', 4, 1, 0, NOW(), NOW()),
((SELECT id FROM sys_dict_type WHERE dict_code='report_type'), '精算报告', 'ACTUARIAL', 'ACTUARIAL', 5, 1, 0, NOW(), NOW()),
((SELECT id FROM sys_dict_type WHERE dict_code='report_type'), '保费收入公告', 'PREMIUM_ANNOUNCE', 'PREMIUM_ANNOUNCE', 6, 1, 0, NOW(), NOW()),
((SELECT id FROM sys_dict_type WHERE dict_code='report_type'), 'ESG报告', 'ESG', 'ESG', 7, 1, 0, NOW(), NOW()),
((SELECT id FROM sys_dict_type WHERE dict_code='report_type'), '社会责任报告', 'CSR', 'CSR', 8, 1, 0, NOW(), NOW()),
((SELECT id FROM sys_dict_type WHERE dict_code='report_type'), '消费者权益保护', 'CONSUMER_PROTECTION', 'CONSUMER_PROTECTION', 9, 1, 0, NOW(), NOW()),
((SELECT id FROM sys_dict_type WHERE dict_code='report_type'), '分红实现率公告', 'DIVIDEND_REALIZATION', 'DIVIDEND_REALIZATION', 10, 1, 0, NOW(), NOW());

-- 消息角色
INSERT IGNORE INTO sys_dict_type (dict_name, dict_code, description, sort_order, status, is_deleted, created_at, updated_at) VALUES
('消息角色', 'message_role', '对话消息角色', 7, 1, 0, NOW(), NOW());

INSERT IGNORE INTO sys_dict_data (dict_type_id, dict_label, dict_value, dict_key, sort_order, status, is_deleted, created_at, updated_at) VALUES
((SELECT id FROM sys_dict_type WHERE dict_code='message_role'), '用户', 'USER', 'USER', 1, 1, 0, NOW(), NOW()),
((SELECT id FROM sys_dict_type WHERE dict_code='message_role'), 'AI助手', 'ASSISTANT', 'ASSISTANT', 2, 1, 0, NOW(), NOW()),
((SELECT id FROM sys_dict_type WHERE dict_code='message_role'), '系统', 'SYSTEM', 'SYSTEM', 3, 1, 0, NOW(), NOW());
