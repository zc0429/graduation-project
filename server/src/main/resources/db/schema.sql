-- ============================================================
-- AI 错题分析与学习推荐系统 数据库 DDL
-- 对齐毕业论文 5.1 节表 5.1–5.8；message / announcement 两张表
-- 经 2026-08-16 与用户裁定补充（接口表 5.9 与类设计 (10) 已要求，
-- 论文 5.1 将于三稿阶段同步修正为 10 张表）。
-- 约定：主键自增 BIGINT；时间字段由数据库自动维护；逻辑外键不建物理外键；
--      user / subject / question 的 status 为软删除标记（1 正常，0 删除/停用）。
-- ============================================================

-- 表 5.1 用户表
CREATE TABLE IF NOT EXISTS `user` (
    id          BIGINT       NOT NULL AUTO_INCREMENT COMMENT '用户 ID',
    username    VARCHAR(32)  NOT NULL COMMENT '登录用户名',
    password    VARCHAR(128) NOT NULL COMMENT '密码（加密存储）',
    nickname    VARCHAR(32)  DEFAULT NULL COMMENT '昵称',
    role        VARCHAR(16)  NOT NULL DEFAULT 'student' COMMENT '角色：student/teacher/admin',
    class_name  VARCHAR(64)  DEFAULT NULL COMMENT '班级名称',
    email       VARCHAR(64)  DEFAULT NULL COMMENT '邮箱',
    status      TINYINT      NOT NULL DEFAULT 1 COMMENT '状态：1 正常，0 停用',
    create_time DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id),
    UNIQUE KEY uk_username (username)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '用户表';

-- 表 5.2 科目表
CREATE TABLE IF NOT EXISTS `subject` (
    id          BIGINT      NOT NULL AUTO_INCREMENT COMMENT '科目 ID',
    name        VARCHAR(32) NOT NULL COMMENT '科目名称（如数学、物理）',
    code        VARCHAR(32) DEFAULT NULL COMMENT '科目编码',
    sort        INT         NOT NULL DEFAULT 0 COMMENT '排序号',
    status      TINYINT     NOT NULL DEFAULT 1 COMMENT '状态：1 启用，0 停用',
    create_time DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (id),
    UNIQUE KEY uk_name (name)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '科目表';

-- 表 5.3 知识点表
CREATE TABLE IF NOT EXISTS `knowledge_point` (
    id          BIGINT      NOT NULL AUTO_INCREMENT COMMENT '知识点 ID',
    subject_id  BIGINT      NOT NULL COMMENT '所属科目，逻辑外键 → subject(id)',
    parent_id   BIGINT      NOT NULL DEFAULT 0 COMMENT '父级 ID：0 表示一级章节',
    name        VARCHAR(64) NOT NULL COMMENT '知识点名称',
    sort        INT         NOT NULL DEFAULT 0 COMMENT '排序号',
    create_time DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '知识点表';

-- 表 5.4 错题表
CREATE TABLE IF NOT EXISTS `question` (
    id                 BIGINT       NOT NULL AUTO_INCREMENT COMMENT '错题 ID',
    user_id            BIGINT       NOT NULL COMMENT '所属学生，逻辑外键 → user(id)',
    subject_id         BIGINT       NOT NULL COMMENT '所属科目，逻辑外键 → subject(id)',
    knowledge_point_id BIGINT       DEFAULT NULL COMMENT '知识点（AI 归类后回填），逻辑外键 → knowledge_point(id)',
    stem               TEXT         NOT NULL COMMENT '题干',
    answer             TEXT         DEFAULT NULL COMMENT '答案',
    source             VARCHAR(128) DEFAULT NULL COMMENT '题目来源（如作业、试卷）',
    image_url          VARCHAR(255) DEFAULT NULL COMMENT '题目图片地址',
    difficulty         TINYINT      DEFAULT NULL COMMENT '难度（1-5，AI 评估）',
    mastery            INT          NOT NULL DEFAULT 0 COMMENT '掌握度（0-100）',
    embedding          TEXT         DEFAULT NULL COMMENT '题干语义向量（JSON 数组）',
    status             TINYINT      NOT NULL DEFAULT 1 COMMENT '状态：1 正常，0 删除',
    create_time        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id),
    KEY idx_user_subject (user_id, subject_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '错题表';

-- 表 5.5 AI 解析记录表（analysis 为 MySQL 8 保留字，需反引号）
CREATE TABLE IF NOT EXISTS `ai_analysis` (
    id                 BIGINT       NOT NULL AUTO_INCREMENT COMMENT '解析记录 ID',
    question_id        BIGINT       NOT NULL COMMENT '对应错题，逻辑外键 → question(id)',
    knowledge_point_id BIGINT       DEFAULT NULL COMMENT 'AI 归类知识点，逻辑外键 → knowledge_point(id)',
    error_cause        TEXT         DEFAULT NULL COMMENT '错因分析',
    `analysis`         TEXT         DEFAULT NULL COMMENT '解析内容',
    reference_ids      VARCHAR(255) DEFAULT NULL COMMENT '参考的本地题目 ID（JSON）',
    llm_model          VARCHAR(64)  DEFAULT NULL COMMENT '所用大模型标识',
    status             TINYINT      NOT NULL DEFAULT 0 COMMENT '状态：0 生成中，1 成功，2 失败',
    create_time        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (id),
    UNIQUE KEY uk_question (question_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = 'AI 解析记录表';

-- 表 5.6 变式题表
CREATE TABLE IF NOT EXISTS `variant_question` (
    id          BIGINT   NOT NULL AUTO_INCREMENT COMMENT '变式题 ID',
    question_id BIGINT   NOT NULL COMMENT '原题 ID，逻辑外键 → question(id)',
    stem        TEXT     NOT NULL COMMENT '变式题题干',
    answer      TEXT     DEFAULT NULL COMMENT '变式题答案',
    difficulty  TINYINT  DEFAULT NULL COMMENT '难度（1-5）',
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '变式题表';

-- 表 5.7 复习计划表
CREATE TABLE IF NOT EXISTS `review_plan` (
    id           BIGINT   NOT NULL AUTO_INCREMENT COMMENT '复习计划 ID',
    user_id      BIGINT   NOT NULL COMMENT '所属学生，逻辑外键 → user(id)',
    question_id  BIGINT   NOT NULL COMMENT '待复习错题，逻辑外键 → question(id)',
    review_stage TINYINT  NOT NULL DEFAULT 1 COMMENT '复习阶段（第 1-5 次）',
    plan_date    DATE     NOT NULL COMMENT '计划复习日期',
    status       TINYINT  NOT NULL DEFAULT 0 COMMENT '状态：0 待复习，1 已完成，2 已过期',
    finish_time  DATETIME DEFAULT NULL COMMENT '完成时间',
    create_time  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (id),
    KEY idx_user_date (user_id, plan_date)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '复习计划表';

-- 表 5.8 练习记录表
CREATE TABLE IF NOT EXISTS `practice_record` (
    id           BIGINT   NOT NULL AUTO_INCREMENT COMMENT '练习记录 ID',
    user_id      BIGINT   NOT NULL COMMENT '作答学生，逻辑外键 → user(id)',
    question_id  BIGINT   DEFAULT NULL COMMENT '重做的错题，逻辑外键 → question(id)',
    variant_id   BIGINT   DEFAULT NULL COMMENT '作答的变式题，逻辑外键 → variant_question(id)',
    user_answer  TEXT     DEFAULT NULL COMMENT '学生作答内容',
    is_correct   TINYINT  DEFAULT NULL COMMENT '是否正确：1 正确，0 错误',
    duration     INT      DEFAULT NULL COMMENT '作答用时（秒）',
    create_time  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (id),
    KEY idx_user_time (user_id, create_time)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '练习记录表';

-- 补充表（2026-08-16 裁定）：消息通知表，对应接口表 5.9 消息通知管理与类设计 (10) MessageService
CREATE TABLE IF NOT EXISTS `message` (
    id          BIGINT       NOT NULL AUTO_INCREMENT COMMENT '消息 ID',
    user_id     BIGINT       NOT NULL COMMENT '接收用户，逻辑外键 → user(id)',
    type        VARCHAR(32)  NOT NULL DEFAULT 'system' COMMENT '消息类型：review_remind 复习提醒/report 报告/system 系统',
    title       VARCHAR(128) NOT NULL COMMENT '消息标题',
    content     VARCHAR(512) DEFAULT NULL COMMENT '消息内容',
    is_read     TINYINT      NOT NULL DEFAULT 0 COMMENT '是否已读：1 已读，0 未读',
    create_time DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (id),
    KEY idx_user_time (user_id, create_time)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '消息通知表';

-- 补充表（2026-08-16 裁定）：公告表，对应接口表 5.9 公告管理
CREATE TABLE IF NOT EXISTS `announcement` (
    id           BIGINT       NOT NULL AUTO_INCREMENT COMMENT '公告 ID',
    title        VARCHAR(128) NOT NULL COMMENT '公告标题',
    content      TEXT         DEFAULT NULL COMMENT '公告内容',
    publisher_id BIGINT       DEFAULT NULL COMMENT '发布人，逻辑外键 → user(id)',
    status       TINYINT      NOT NULL DEFAULT 1 COMMENT '状态：1 正常，0 下线',
    create_time  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '公告表';

-- Personal knowledge-content cache; additive and idempotent, preserves the original ten tables.
CREATE TABLE IF NOT EXISTS `learning_content` (
    id BIGINT NOT NULL AUTO_INCREMENT COMMENT '知识内容ID',
    user_id BIGINT NOT NULL COMMENT '所属学生',
    question_id BIGINT NOT NULL COMMENT '关联原题',
    knowledge_point_id BIGINT DEFAULT NULL COMMENT '关联知识点',
    input_hash CHAR(64) NOT NULL COMMENT '生成输入快照SHA-256',
    content TEXT NOT NULL COMMENT '经校验的纯文本知识讲解',
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_learning_question (question_id),
    KEY idx_learning_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='个人知识学习资源';
