# 基于智谱GLM模型的AI错题分析与学习推荐系统设计与实现

当前独立交付分支 `codex/learning-delivery-20261112`：个人资源复用与持续练习、九章论文及学校模板DOCX/PDF，见[交付与验证](docs/validation/learning-delivery-20261112/README.md)和[Cloud字体初始化](scripts/cloud/README.md)。原审阅PR保持独立，不自动合并dev。


本科毕业设计项目，围绕“错题录入 → AI 知识点归类与解析（RAG）→ 变式题练习 → 遗忘曲线复习 → 学情反馈”形成完整学习闭环。前端为 Vue 3 单页应用，后端为 Spring Boot 3.5.16 REST 服务；正常运行默认使用真实智谱 GLM 服务与图片识题；离线开发显式选择 Mock，自动化测试使用隔离的 Mock 配置。缺少密钥时给出明确提示，仍可手工保存错题。

- **英文题目**：Design and Implementation of an AI-Powered Wrong-Question Analysis and Learning Recommendation System Based on the Zhipu GLM Model
- **指导教师**：胡韬（云南工商学院人工智能学院，2027 届）

## 当前实现

- 学生：注册登录、富文本题干新增与编辑、图片上传及 GLM-5.3-Flash 单图识别候选回填、错题筛选/编辑/删除、带 JWT 的 Excel 导出、AI 解析状态轮询、变式题生成与自评练习、到期/逾期复习、练习历史、周报、消息与个人资料。图片识别默认开启，识别成功后仍由用户确认并走普通错题创建链。
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
│   ├── thesis/             # 完整论文源稿、建模源文件与必要截图
│   ├── experiments/        # 历史实验数据与人工评价记录
│   └── validation/         # 按轮次保存的验证证据
├── output/                 # 阶段性交付导出件（保留，不是构建缓存）
├── scripts/                # 文档构建与验证脚本
└── AGENTS.md               # 跨对话项目约束与关键决策
```

最新成果从 [项目交接入口](docs/notes/HANDOFF.md) 与 [文档目录导航](docs/README.md) 查找；历史论文/文献快照见 [归档索引](docs/archives/README.md)，云端和 Windows 的操作见 [Git 同步流程](docs/notes/Git同步与分支管理.md)。已授权的清理结果见 [2026-10-28 后续整理记录](docs/notes/仓库后续整理-20261028.md)；更早报告保留为历史快照。

日常开发基准是 `dev`。GitHub 默认分支修改因集成权限不足返回 403，目前仍为 `main`；新克隆请显式指定 `git clone --branch dev https://github.com/zc0429/graduation-project.git`。本地已有仓库按同步流程切换并更新 dev。

## 本地启动

建议环境：JDK 21、MySQL 8、Node.js 22。Windows 启动后端前应确认 `JAVA_HOME` 指向 JDK 21；Linux 使用已配置的 JDK 21 即可。

数据库账号、密码和真实模型密钥只通过当前终端环境变量注入，不能提交到仓库、日志、论文或截图。`DB_URL` 应指向开发数据库；`LLM_PROVIDER` 不设置时默认为 `glm`，文本默认 `glm-5.3-flash`，向量保持 `embedding-3 / 1024`。

```powershell
# 终端 1：后端（先设置 DB_URL、DB_USERNAME、DB_PASSWORD）
Set-Location 'D:\Documents\GitHub\graduation-project\server'
$env:LLM_PROVIDER = 'glm'
# 真实密钥在当前终端或未跟踪 .env 中配置；离线时改为 mock 并设置 IMAGE_RECOGNITION_ENABLED=false
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

最近一次应用回归是 **2026-10-26 的合并验证**：后端 84 项中 80 通过、4 个真实入口跳过；前端类型检查、29 项单测及构建通过；四档 Mock 浏览器 45 项、真实后端配合 Mock AI 的联调 4 项通过。为保留交付截图，排除 1 项会重写截图的用例；实际命令与范围见 [合并验证记录](docs/validation/merge-advisor-20261026/README.md)。此前导师修改轮的 46 项浏览器验证另见 [该轮证据](docs/validation/advisor-20261026/README.md)，两轮不混算。

2026-10-27/28 的仓库整理只做 Git、文件哈希、文档链接及归档校验，没有重跑应用测试。当前默认模型的真实联网、draw.io 软件实开和完整论文 Word/PDF 重导仍待验证。

<details>
<summary>较早验收摘要（历史快照）</summary>

2026-08-28 冻结审计验收：JDK 21 后端 70 项中 66 通过、4 个真实联网入口按预期跳过；前端类型检查和生产构建通过，Vitest 23/23、四档 Mock UI 44/44、`wrongbook_e2e + Mock AI` 真实后端联调 4/4。8 月 25 日的 Chrome/Edge/Firefox 59/59、axe-core 3/3 与 Lighthouse 结果保留为历史快照。完整命令、范围与非永久性验收快照见 [web/README.md](web/README.md)。

</details>

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

## 2026-10-26 导师意见落实

本轮审计、实施与验证见 [交付报告](docs/notes/导师意见落实-20261026-交付报告.md)。[最新完整论文](docs/thesis/毕业论文.md)保留独立论文分支的20篇文献体系；[三张业务泳道图](docs/thesis/business-flow/README.md)已同步正文。真实模型本轮因无密钥未联网验证，历史真实证据保留。
