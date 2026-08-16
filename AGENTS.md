# AGENTS.md — 毕业设计项目记忆

> 本文件是跨对话的"项目记忆"。每次新对话开始时先阅读本文件与 `docs/notes/进度记录.md`，
> 再结合 `git log` 了解最近工作，即可无缝接续。每次会话结束前更新进度记录。

## 项目概述

- **性质**：本科毕业设计（云南工商学院，人工智能学院，2027 届），指导教师：**胡韬**（邮箱 stevenbug@qq.com，任务书等文档经邮件提交）
- **学生信息**：赵灿，学号 23612801026，2023级【本科】软件工程1班
- **论文关键词（4 个，导师要求录入系统并用于摘要）**：错题分析；个性化推荐；检索增强生成；Spring Boot（备选替换项：知识追踪、遗忘曲线、Vue.js）
- **论文三稿节奏（导师明确要求）**：一稿完成需求分析 → 二稿完成概要设计与详细设计 → 三稿完成编码与测试
- **题目（已定，2026-07-21）**：**基于 Spring Boot+Vue 的 AI 错题分析与学习推荐系统设计与实现**
  （业务闭环：错题录入 → AI 知识点归类与解析（RAG）→ 相似题/变式题推荐 → 遗忘曲线复习计划 → 学情报告；数据库设计 8 张表）
- **论文**：Word 撰写。**写作与格式唯一权威依据 = `docs/materials/附件2：云南工商学院本科毕业论文（设计）.docx`**（实为《撰写规范及要求》，非排版模板；封面/任务书正式表格届时从论文系统导出）。用户明确要求：所有论文相关内容严格按此文档编写
- **用户 Git 身份**：`zc0429 <17268890681@163.com>`（本仓库 local 配置，勿改全局）

## 论文硬性指标（导师要求，勿违反）

- 总字数 > 12000，查重 < 20%；绪论 ≥800 字，文献综述 2000–3000 字，主体 ≥8000 字
- 参考文献 ≥20 篇（近 3 年 ≥15 篇、外文 ≥2 篇），正文角标可跳转
- 系统：总 7–8 张表，必须有业务流程（非单纯增删改查）；题目 ≤25 字且与 AI 有关（非简单调用）
- 选题禁区：购物商城 / 图书管理 / 二手商城
- 详细梳理：`docs/notes/论文要求梳理与选题建议.md`

## 格式红线（依据附件2《撰写规范》，写论文/任务书/开题时必须遵守）

- 中文：小四宋体；**数字与英文字母：Times New Roman 小四**；行距固定值 20 磅；首行缩进 2 字符
- 页面：左 2.75cm，右/上/下 2.5cm，页眉页脚 1.5cm；页码：摘要部分大写罗马数字，正文从绪论起阿拉伯数字
- 标题：理工科编号 `1 / 1.1 / 1.1.1`（最多四级），图表分章编号（图 2.5、表 3.1），三线表
- 参考文献著录：中文条目用**全角标点**（，：（））；**外文作者名前须加国籍**（如 (美)）；作者 >3 位用"等"；电子文献标注 [EB/OL] + 引用日期
- 摘要：中文约 300 字，中英文内容一致；关键词 3–5 个（已定 4 个）

## 关键决策（勿擅自推翻）

1. **正文一律以 Markdown 输出**（任务书/开题/论文各章节都先写 `.md` 源稿存 `docs/thesis/`），采用**纯语义章节结构**（章节标题 + 正文），**不承担排版**；**后续由 opencode 按用户要求单独整理为可交付 DOCX/PDF**，导出时再统一套用附件2 格式红线（直出 docx 的格式用户用不了，勿再直接生成 docx）。竖排标签/vMerge 跨行等版式属于呈现层，只在导出时复刻参考 PDF 实现，不在源稿模拟。
2. 参考文献**双轨制**：`docs/references/references.bib` + `gb7714-list.md`（GB/T 7714-2015 顺序编码制）
3. 文献 PDF 存 `docs/references/pdfs/`，**默认不入库**（.gitignore 已排除）
4. **开发端以 Linux 为主**（论文/文档/编码同机），Windows 作为备份/同步端（可装 IDEA/VS Code 后 `git pull` 取最新）；github.com 已可直连本机 SSH（曾经的"开发必须在 Windows"约束源于"Maven 缺 + github 不通"，已于 2026-08-16 全部解除）
5. `server/`（Spring Boot 4.x 或 3.3.x，见决策7）与 `web/`（Vue 3 + Vite）骨架**仍暂未创建**（用户 2026-08-16 明确暂缓）；后端建时配 Maven Wrapper（`mvnw`）以便 Windows 端免装 Maven 直接构建
6. 分支策略：`main` 稳定 + `dev` 日常开发
7. **Spring Boot 版本待定（2026-08-16 发现）**：start.spring.io 默认当前 GA 已是 **Spring Boot 4.1.0**（基于 Spring Framework 7 / Jakarta EE 11 / 需 JDK 17+）；毕业论文与系统设计章节目前表述为 "Spring Boot 3.x"。建骨架前需用户决策：锁 **3.3.x**（成熟、资料多、教学常用、与现有论文表述一致）还是 **4.1.0**（最新、新特性）。若选 4.x，必须同步更新论文"相关技术介绍/概要设计"等章节的版本表述与文献。

## 开发工具链（Linux 端，2026-08-16 配置完成）

- JDK 21.0.11（apt openjdk-21）、Maven 3.9.16（免安装包 `~/tools/maven`，PATH 已写入 `~/.bashrc` + `~/.profile`）、Node 22.23.1 / npm 10.9.8
- Maven 镜像：`~/.m2/settings.xml` 配阿里云 public（实测 0.034s vs Maven Central 0.81s，约 24 倍速）
- VS Code（snap）已装全套 Java/Spring 扩展：`redhat.java` + `vscjava.vscode-java-pack` + `vscode-maven` + `vscode-spring-initializr` + `vscode-spring-boot-dashboard` + `vmware.vscode-spring-boot` + `vscode-java-debug/test/dependency`
- Git + ed25519 SSH 已通；远程 `zc0429/graduation-project` 已推送并设 upstream
- 仍无（不需）：Gradle（用 Maven 即可）、LaTeX（论文走 Markdown→docx 路径）、gh CLI（用网页操作）、IDEA（VS Code 已替代）
- start.spring.io 与 npm registry 可连通，可拉 Spring Boot 起步与 Vue 项目

## 目录速查

| 路径 | 用途 |
|---|---|
| `docs/materials/` | 导师提供：概要说明 PDF、学校论文模板、参考论文（含开题/任务书/中期检查范例） |
| `docs/thesis/` | 毕业论文与提交文档：Markdown 源稿（按需单独导出 DOCX/PDF） |
| `docs/notes/` | 开题报告、周报、**进度记录.md** |
| `docs/references/` | 参考文献双轨管理（见其 README） |

## Git 规范

- 提交信息：`类型: 简述`，类型：`docs` / `feat` / `fix` / `chore` / `ref`
- 导师材料、过程文档更新后及时提交留痕
- 推送步骤见根 README（首次需 `git remote add origin`）

## 当前状态与待办

- 最近进度：见 `docs/notes/进度记录.md`（每次会话结束必须更新）
- **已完成（2026-07-26）**：任务书复核修正；参考文献 24 篇双轨入库（近 3 年 17、外文 14，全部联机核验真实条目，6 篇 OA PDF 在 `pdfs/`）；开题报告定稿（`docs/thesis/开题报告.md`）；毕业论文一稿+二稿源稿（`docs/thesis/毕业论文.md`：摘要+绪论+文献综述+系统分析+概要设计+详细设计，总字数 13338，自检 8 项全过）
- **已完成（2026-08-16）**：届次修正为 2027 届；GitHub 首次推送（main+dev 设 upstream）；Linux 端开发环境配置完成（Maven 3.9.16 + 阿里云镜像 + VS Code Java/Spring 扩展套件）
- **待办**：①三稿内容（第 6 章实现与测试/第 7 章总结/甘特图，待本机端系统开发，禁止编造）②建骨架前先决策 Spring Boot 3.3.x vs 4.1.0（见决策7，影响论文表述）③中文文献 [15][17][21] 页码待知网补全 ④任务书导出 DOCX/PDF 发导师 ⑤UML 图补画（论文占位处）

## GitHub 同步

- 远程仓库已建立：`git@github.com:zc0429/graduation-project.git`（Private）
- 本机 ed25519 SSH 密钥已登记；`main` / `dev` 均已推送并设 upstream
- 日常用 `git push` / `git pull` 在 Linux（论文/文档）与 Windows（编码）间同步
