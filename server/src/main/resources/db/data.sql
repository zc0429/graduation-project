-- ============================================================
-- 初始化数据（INSERT IGNORE + 固定主键，重复启动幂等）
-- 账号密码均为 123456（BCrypt 加密存储）
-- ============================================================

-- 用户：1 管理员、1 教师、1 学生（演示用）
INSERT IGNORE INTO `user` (id, username, password, nickname, role, class_name) VALUES
(1, 'admin',   '$2b$10$6mhKfLIf7KUtNEjgVUKvPeVAliH9a.QxgMnn8cMYhrvrh.lTs609G', '系统管理员', 'admin',   NULL),
(2, 'teacher', '$2b$10$6mhKfLIf7KUtNEjgVUKvPeVAliH9a.QxgMnn8cMYhrvrh.lTs609G', '王老师',     'teacher', NULL),
(3, 'student', '$2b$10$6mhKfLIf7KUtNEjgVUKvPeVAliH9a.QxgMnn8cMYhrvrh.lTs609G', '小明',       'student', '2023级软件工程1班');

-- 科目
INSERT IGNORE INTO `subject` (id, name, code, sort) VALUES
(1, '数学', 'MATH',    1),
(2, '物理', 'PHYSICS', 2),
(3, '英语', 'ENGLISH', 3);

-- 知识点（一级章节 parent_id=0，二级考点 parent_id=章节 id）
INSERT IGNORE INTO `knowledge_point` (id, subject_id, parent_id, name, sort) VALUES
(1,  1, 0, '函数',   1),
(2,  1, 1, '一次函数', 1),
(3,  1, 1, '二次函数', 2),
(4,  1, 0, '几何',   2),
(5,  1, 4, '三角形全等', 1),
(6,  1, 4, '圆的性质',  2),
(7,  2, 0, '力学',   1),
(8,  2, 7, '牛顿第二定律', 1),
(9,  2, 7, '摩擦力',    2),
(10, 2, 0, '电学',   2),
(11, 2, 10, '欧姆定律', 1),
(12, 3, 0, '语法',   1),
(13, 3, 12, '定语从句', 1),
(14, 3, 12, '动词时态', 2);

-- 公告
INSERT IGNORE INTO `announcement` (id, title, content, publisher_id) VALUES
(1, '欢迎使用 AI 错题分析与学习推荐系统', '系统支持错题录入、AI 解析、相似题与变式题推荐、遗忘曲线复习计划与学情报告。首次使用请先完善个人信息。', 1);
