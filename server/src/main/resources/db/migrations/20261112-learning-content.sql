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
