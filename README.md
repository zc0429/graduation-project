# 基于智谱GLM模型的AI错题分析与学习推荐系统设计与实现

本科毕业设计项目，围绕“错题录入 → AI 知识点归类与解析（RAG）→ 变式题练习 → 遗忘曲线复习 → 学情反馈”形成完整学习闭环。前端为 Vue 3 单页应用，后端为 Spring Boot 3.5.16 REST 服务；离线开发和自动化验收默认使用 Mock AI，智谱 GLM 仅在显式设置 `LLM_PROVIDER=glm` 并通过环境变量配置密钥与模型后启用。

- **英文题目**：Design and Implementation of an AI-Powered Wrong-Question Analysis and Learning Recommendation System Based on the Zhipu GLM Model
- **指导教师**：胡韬（云南工商学院人工智能学院，2027 届）

## 当前实现

- 学生：注册登录、手工错题录入与图片上传、可选的 GLM-5.3-Flash 单图识别回填、错题筛选/编辑/删除、带 JWT 的 Excel 导出、AI 解析状态轮询、变式题生成与自评练习、到期/逾期复习、练习历史、周报、消息与个人资料。图片识别默认关闭，识别成功后仍由用户确认并走普通错题创建链。
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

开发服务器默认使用 `http://localhost:5173`，并把 `/api` 代理到 `http://localhost:8080`。题图不再匿名映射 `/uploads/**`，只在本人已鉴权的错题详情响应中以内联数据返回。首次启动后端会幂等执行 `schema.sql` 与 `data.sql`。

## 质量检查

```powershell
Set-Location 'D:\Documents\GitHub\graduation-project\web'
npm run typecheck
npm run test:unit
npm run build
npm run e2e:smoke
```

2026-08-28 冻结审计验收：JDK 21 后端 70 项中 66 通过、4 个真实联网入口按预期跳过；前端类型检查和生产构建通过，Vitest 23/23、四档 Mock UI 44/44、`wrongbook_e2e + Mock AI` 真实后端联调 4/4。8 月 25 日的 Chrome/Edge/Firefox 59/59、axe-core 3/3 与 Lighthouse 结果保留为历史快照。完整命令、范围与非永久性验收快照见 [web/README.md](web/README.md)。

## 已知安全与数据边界

- RAG 与相似题候选在查询层和结果层都绑定源题所属学生；管理员内部处理也沿用源题 owner 作为候选边界。
- 每次受保护请求都会核验数据库中的当前账号状态和角色；账号停用后旧 JWT 立即失效，角色变更也不会继续沿用令牌中的旧角色。
- Question、AI、Practice、ReviewPlan、Variant、Recommend 与图片识别接口在服务端限定为 student；报告接口只允许 student/teacher，前端路由不是唯一权限边界。
- 题图文件名使用随机 UUID，上传目录不做匿名静态映射；本人错题详情以内联 Data URI 返回题图，替换或删除错题时清理旧文件。
- `data.sql` 的 `123456` 种子账号仅用于可信本机演示和隔离测试；任何局域网或公网部署都必须先更换账号密码并显式配置 `JWT_SECRET`。
- 教师周报是全站聚合结果，不是班级或个人报表；报告接口生成当前统计结果，不提供历史报告归档。
- 复习接口只返回已到期/逾期且未完成的任务，不提供未来日历；“完成复习计划”和“提交练习记录”是两个独立动作。
- 掌握度由练习结果更新并进入周报；相似题推荐以指定原题的知识点、难度和 RAG 为依据，不读取 mastery，不能描述为练习反馈驱动的自适应推荐。

## 文档与 Git 约定

- 论文、任务书和开题内容先以纯语义 Markdown 写入 `docs/thesis/`，最终导出时再统一套用学校格式。
- 学校格式、进度与提交要求优先读取 `docs/materials/27届毕业设计学校通知和模板/`；旧附件和导师范例仅在新材料未覆盖时补充参考。
- `main` 保存稳定成果，`dev` 用于日常开发；功能分支默认使用 `codex/` 前缀。
- 提交信息使用 `类型: 简述`，常用类型为 `docs`、`feat`、`fix`、`chore`、`ref`。
- 远程仓库：`git@github.com:zc0429/graduation-project.git`（Private）。
