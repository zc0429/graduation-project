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

-- ============================================================
-- 实训新增（RBAC 权限模块初始化数据，INSERT IGNORE 幂等）
-- ============================================================

-- 角色：与 user.role 字段取值一一对应
INSERT IGNORE INTO `role` (id, role_name, role_key, sort, remark) VALUES
(1, '管理员', 'admin',   1, '拥有全部权限'),
(2, '教师',   'teacher', 2, '查看学生错题与学情，维护科目与知识点'),
(3, '学生',   'student', 3, '维护个人错题、复习计划与练习记录');

-- 权限：一级为模块（menu），二级为操作（button），权限码与后端 @SaCheckPermission 对应
INSERT IGNORE INTO `permission` (id, parent_id, name, permission_key, type, path, sort) VALUES
(1, 0, '用户管理',   'system:user',       'menu', '/admin/user',       1),
(2, 0, '角色管理',   'system:role',       'menu', '/admin/role',       2),
(3, 0, '权限管理',   'system:permission', 'menu', '/admin/permission', 3),
(4, 0, '科目管理',   'business:subject',     'menu', '/admin/subject',     4),
(5, 0, '知识点管理', 'business:knowledge',   'menu', '/admin/knowledge',    5),
(6, 0, '错题管理',   'business:question',    'menu', '/question/list',    6),
(7, 0, '复习计划',   'business:review',      'menu', '/review',       7),
(8, 0, '练习记录',   'business:practice',    'menu', '/practice/history',     8),
(9, 0, '消息通知',   'business:message',     'menu', '/message',     9),
(10, 0, '公告管理',  'business:announcement','menu', '/announcement', 10),
(11, 1, '用户查询', 'system:user:list',   'button', NULL, 1),
(12, 1, '用户新增', 'system:user:add',    'button', NULL, 2),
(13, 1, '用户修改', 'system:user:edit',   'button', NULL, 3),
(14, 1, '用户删除', 'system:user:delete', 'button', NULL, 4),
(21, 2, '角色查询', 'system:role:list',   'button', NULL, 1),
(22, 2, '角色新增', 'system:role:add',    'button', NULL, 2),
(23, 2, '角色修改', 'system:role:edit',   'button', NULL, 3),
(24, 2, '角色删除', 'system:role:delete', 'button', NULL, 4),
(31, 3, '权限查询', 'system:permission:list',   'button', NULL, 1),
(32, 3, '权限新增', 'system:permission:add',    'button', NULL, 2),
(33, 3, '权限修改', 'system:permission:edit',   'button', NULL, 3),
(34, 3, '权限删除', 'system:permission:delete', 'button', NULL, 4),
(41, 4, '科目查询', 'business:subject:list',   'button', NULL, 1),
(42, 4, '科目新增', 'business:subject:add',    'button', NULL, 2),
(43, 4, '科目修改', 'business:subject:edit',   'button', NULL, 3),
(44, 4, '科目删除', 'business:subject:delete', 'button', NULL, 4),
(51, 5, '知识点查询', 'business:knowledge:list',   'button', NULL, 1),
(52, 5, '知识点新增', 'business:knowledge:add',    'button', NULL, 2),
(53, 5, '知识点修改', 'business:knowledge:edit',   'button', NULL, 3),
(54, 5, '知识点删除', 'business:knowledge:delete', 'button', NULL, 4),
(61, 6, '错题查询', 'business:question:list',   'button', NULL, 1),
(62, 6, '错题新增', 'business:question:add',    'button', NULL, 2),
(63, 6, '错题修改', 'business:question:edit',   'button', NULL, 3),
(64, 6, '错题删除', 'business:question:delete', 'button', NULL, 4),
(71, 7, '复习计划查询', 'business:review:list',   'button', NULL, 1),
(72, 7, '复习计划新增', 'business:review:add',    'button', NULL, 2),
(73, 7, '复习计划修改', 'business:review:edit',   'button', NULL, 3),
(74, 7, '复习计划删除', 'business:review:delete', 'button', NULL, 4),
(81, 8, '练习记录查询', 'business:practice:list',   'button', NULL, 1),
(82, 8, '练习记录新增', 'business:practice:add',    'button', NULL, 2),
(83, 8, '练习记录修改', 'business:practice:edit',   'button', NULL, 3),
(84, 8, '练习记录删除', 'business:practice:delete', 'button', NULL, 4),
(91, 9, '消息查询', 'business:message:list',   'button', NULL, 1),
(92, 9, '消息新增', 'business:message:add',    'button', NULL, 2),
(93, 9, '消息修改', 'business:message:edit',   'button', NULL, 3),
(94, 9, '消息删除', 'business:message:delete', 'button', NULL, 4),
(101, 10, '公告查询', 'business:announcement:list',   'button', NULL, 1),
(102, 10, '公告新增', 'business:announcement:add',    'button', NULL, 2),
(103, 10, '公告修改', 'business:announcement:edit',   'button', NULL, 3),
(104, 10, '公告删除', 'business:announcement:delete', 'button', NULL, 4);

-- 角色-权限分配：管理员拥有全部权限
INSERT IGNORE INTO `role_permission` (role_id, permission_id)
SELECT 1, id FROM `permission`;
-- 教师：各业务模块查询 + 科目/知识点维护 + 公告与消息查看
INSERT IGNORE INTO `role_permission` (role_id, permission_id) VALUES
(2,4),(2,5),(2,6),(2,7),(2,8),(2,9),(2,10),
(2,41),(2,42),(2,43),(2,51),(2,52),(2,53),
(2,61),(2,71),(2,81),(2,91),(2,101);
-- 学生：科目/知识点查询 + 错题、复习、练习、消息的查询与维护（不含系统管理与删除基础数据）
INSERT IGNORE INTO `role_permission` (role_id, permission_id) VALUES
(3,4),(3,5),(3,6),(3,7),(3,8),(3,9),
(3,41),(3,51),
(3,61),(3,62),(3,63),(3,64),
(3,71),(3,72),(3,73),(3,74),
(3,81),(3,82),(3,83),
(3,91),(3,93);

-- 用户-角色分配：与演示账号的 user.role 保持一致（1 管理员、2 教师、3 学生）
INSERT IGNORE INTO `user_role` (user_id, role_id) VALUES
(1, 1),
(2, 2),
(3, 3);
