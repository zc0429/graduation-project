# AGENTS.md — 毕业设计项目记忆

> 本文件是跨对话的"项目记忆"。每次新对话开始时先阅读本文件与 `docs/notes/进度记录.md`，
> 再结合 `git log` 了解最近工作，即可无缝接续。每次会话结束前更新进度记录。

## 项目概述

- **性质**：本科毕业设计（云南工商学院，人工智能学院，2026 届），指导教师：**胡韬**
- **题目（待定）**：基于 Spring Boot + Vue 的 AI ××× 系统设计与实现（选题候选见 `docs/notes/论文要求梳理与选题建议.md`，选题截止 2026-09-18）
- **论文**：Word 撰写，学校模板见 `docs/materials/附件2：云南工商学院本科毕业论文（设计）.docx`
- **用户 Git 身份**：`zc0429 <17268890681@163.com>`（本仓库 local 配置，勿改全局）

## 论文硬性指标（导师要求，勿违反）

- 总字数 > 12000，查重 < 20%；绪论 ≥800 字，文献综述 2000–3000 字，主体 ≥8000 字
- 参考文献 ≥20 篇（近 3 年 ≥15 篇、外文 ≥2 篇），正文角标可跳转
- 系统：总 7–8 张表，必须有业务流程（非单纯增删改查）；题目 ≤25 字且与 AI 有关（非简单调用）
- 选题禁区：购物商城 / 图书管理 / 二手商城
- 详细梳理：`docs/notes/论文要求梳理与选题建议.md`

## 关键决策（勿擅自推翻）

1. 论文用 **Word** 写，仓库不维护 LaTeX/Markdown 版正文
2. 参考文献**双轨制**：`docs/references/references.bib` + `gb7714-list.md`（GB/T 7714-2015 顺序编码制）
3. 文献 PDF 存 `docs/references/pdfs/`，**默认不入库**（.gitignore 已排除）
4. 系统开发在 **Windows** 端进行，经 GitHub 同步；Linux 端只做论文/文档管理，**不在 Linux 构建代码**
5. `server/`（Spring Boot 3）与 `web/`（Vue 3 + Vite）骨架**暂未创建**，待题目确定后在 Windows 端添加；后端仅生成 pom.xml（不配 Maven Wrapper）
6. 分支策略：`main` 稳定 + `dev` 日常开发

## 环境约束（Linux 端）

- 无 Maven / Gradle / LaTeX / gh CLI；有 git、Node 22、Python 3、JDK 21
- **github.com 当前直连不通**（推送需代理或换网络）
- start.spring.io 与 npm registry 可连通

## 目录速查

| 路径 | 用途 |
|---|---|
| `docs/materials/` | 导师提供：概要说明 PDF、学校论文模板、参考论文（含开题/任务书/中期检查范例） |
| `docs/thesis/` | 毕业论文 .docx |
| `docs/notes/` | 开题报告、周报、**进度记录.md** |
| `docs/references/` | 参考文献双轨管理（见其 README） |

## Git 规范

- 提交信息：`类型: 简述`，类型：`docs` / `feat` / `fix` / `chore` / `ref`
- 导师材料、过程文档更新后及时提交留痕
- 推送步骤见根 README（首次需 `git remote add origin`）

## 当前状态与待办

- 最近进度：见 `docs/notes/进度记录.md`（每次会话结束必须更新）
- 下一阶段：与胡韬老师确认选题（候选 4 个已备）→ 参考文献积累（≥20 篇：近 3 年 ≥15、外文 ≥2）→ 撰写开题报告（范例结构已提炼，截止见梳理文档）
