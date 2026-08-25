# 基于智谱 GLM 模型的 AI 错题分析与学习推荐系统

本科毕业设计项目，围绕“错题录入 → AI 知识点归类与解析（RAG）→ 变式题练习 → 遗忘曲线复习 → 学情反馈”形成完整学习闭环。前端为 Vue 3 单页应用，后端为 Spring Boot 3.5.16 REST 服务；离线开发和自动化验收默认使用 Mock AI，智谱 GLM 仅在显式配置密钥后启用。

- **英文题目**：Design and Implementation of an AI-Powered Wrong-Question Analysis and Learning Recommendation System Based on the Zhipu GLM Model
- **指导教师**：胡韬（云南工商学院人工智能学院，2027 届）

## 当前实现

- 学生：注册登录、错题录入与图片上传、错题筛选/编辑/删除、带 JWT 的 Excel 导出、AI 解析状态轮询、变式题生成与自评练习、到期/逾期复习、练习历史、周报、消息与个人资料。
- 教师：查看后端现有的全站聚合周报。当前没有班级、课程、任课关系或学生钻取接口，因此界面不会模拟这些能力。
- 管理员：查询与逻辑注销用户，新增/编辑科目，维护两级知识点，查看/发布公告。角色分配、账号恢复、科目删除、公告编辑或下线尚无后端接口。
- 通用：按角色生成导航，恢复会话时校验 JWT，统一处理加载/空/错误/无权状态，支持桌面、平板和移动端布局。

前端结构、设计变量和接口边界详见 [前端架构说明](docs/design/frontend-architecture.md)，运行与验收命令详见 [前端 README](web/README.md)。

## 仓库结构

```text
graduation-project/
├── server/                 # Spring Boot 3.5.16 + MyBatis-Plus + MySQL 8
├── web/                    # Vue 3 + TypeScript + Vite 前端
├── docs/
│   ├── design/             # 前端原型、截图与架构说明
│   ├── materials/          # 学校规范、导师材料和参考样例
│   ├── notes/              # 进度记录、开题与过程文档
│   ├── references/         # BibTeX 与 GB/T 7714 双轨参考文献
│   └── thesis/             # 论文及提交文档的 Markdown 源稿
└── AGENTS.md               # 跨对话项目约束与关键决策
```

## 本地启动

建议环境：JDK 21、MySQL 8、Node.js 22。Windows 启动后端前应确认 `JAVA_HOME` 指向 JDK 21；Linux 使用已配置的 JDK 21 即可。

数据库账号、密码和真实模型密钥只通过当前终端环境变量注入，不能提交到仓库、日志、论文或截图。`DB_URL` 应指向开发数据库；`LLM_PROVIDER` 不设置时默认为 `mock`。

```powershell
# 终端 1：后端（先设置 DB_URL、DB_USERNAME、DB_PASSWORD）
Set-Location 'D:\Documents\GitHub\graduation-project\server'
$env:LLM_PROVIDER = 'mock'
.\mvnw.cmd spring-boot:run

# 终端 2：前端
Set-Location 'D:\Documents\GitHub\graduation-project\web'
npm ci
npm run dev
```

开发服务器默认使用 `http://localhost:5173`，并把 `/api` 与 `/uploads` 代理到 `http://localhost:8080`。首次启动后端会幂等执行 `schema.sql` 与 `data.sql`。

## 质量检查

```powershell
Set-Location 'D:\Documents\GitHub\graduation-project\web'
npm run typecheck
npm run test:unit
npm run build
npm run e2e:smoke
```

跨浏览器、无障碍、Lighthouse 与真实后端 `wrongbook_e2e` 隔离验收的完整步骤见 [web/README.md](web/README.md)。README 不固化可能随代码变化而过期的通过数量；最终结果由当次验收填写并以命令输出为准。

## 已知安全与数据边界

- 后端相似题候选集尚未完成用户隔离，正式前端已停止请求和展示相似题；修复并验证服务端隔离前不得恢复。
- RAG 解析当前只展示后端返回的参考题 ID，不展开题干；候选隔离仍需后端继续修复。
- 管理员停用用户后，已经签发的 JWT 不会立即失效；需要后端增加令牌版本、黑名单或状态实时校验。
- 教师周报是全站聚合结果，不是班级或个人报表；报告接口生成当前统计结果，不提供历史报告归档。
- 复习接口只返回已到期/逾期且未完成的任务，不提供未来日历；“完成复习计划”和“提交练习记录”是两个独立动作。
- 前端菜单和路由守卫用于交互约束，不能替代服务端鉴权。

## 文档与 Git 约定

- 论文、任务书和开题内容先以纯语义 Markdown 写入 `docs/thesis/`，最终导出时再统一套用学校格式。
- `main` 保存稳定成果，`dev` 用于日常开发；功能分支默认使用 `codex/` 前缀。
- 提交信息使用 `类型: 简述`，常用类型为 `docs`、`feat`、`fix`、`chore`、`ref`。
- 远程仓库：`git@github.com:zc0429/graduation-project.git`（Private）。
