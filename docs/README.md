# 文档目录导航

日常工作基于最新远程 `dev`。本导航只说明位置与状态，不迁移、重命名或删除既有成果。开始会话先读根目录 [AGENTS.md](../AGENTS.md) 和 [进度记录](notes/进度记录.md)。

统一交接入口为 [HANDOFF.md](notes/HANDOFF.md)，历史分支的固定快照从 [archives/](archives/README.md) 进入。GitHub 默认分支仍为 main（修改被集成权限拒绝）；新克隆需显式指定 dev。

| 位置 | 内容与使用方式 |
|---|---|
| [materials/](materials/README.md) | 学校通知、模板、导师材料和参考论文原件；保留原名与内容 |
| [thesis/毕业论文.md](thesis/毕业论文.md) | 当前完整第 1—7 章正文源稿；2026-10-26 已接入完整论文分支并同步导师要求 |
| [thesis/](thesis/README.md) | 任务书、已通过开题报告、历史写作提纲；形成阶段不同，不作为重复文件删除 |
| [thesis/business-flow/](thesis/business-flow/README.md) | 三张业务泳道图，保留 draw.io 源及 SVG、PNG、PDF；合并版与单图是不同使用入口 |
| [thesis/figures/](thesis/figures/README.md) | 论文图源、导出图、manifest 与校验结果；archive 是改图前历史源，不能按缓存清除 |
| thesis/screenshots/ | Mock 走查、真实 GLM、导师修改轮截图；来源与日期不同，保留区分 |
| [validation/](validation/) | 模型验证、业务回归和各轮验证原始证据；相同结果也可能来自独立执行 |
| [experiments/gate5/](experiments/gate5/README.md) | 历史实验数据、人工评价、统计记录；保留原始证据 |
| [references/](references/README.md) | BibTeX 与顺序编码文献库；论文当前采用已确认的 20 篇及原顺序，不随整理重新编号 |
| [design/](design/frontend-architecture.md) | 前端架构、早期设计和截图，保留其阶段性用途 |
| [notes/](notes/README.md) | 进度、交付、需求讲解与历史交接记录；旧日志状态须结合顶部最新说明阅读 |
| [archives/](archives/README.md) | 历史分支固定标签、成果清单和恢复步骤；保存完整原提交，正文仍取当前 dev |
| [../output/](../output/README.md) | 开题、任务书、图示等可交付导出物及历史备份；不可整体当作 dist 清除 |
| [../scripts/](../scripts/) | 文档生成与校验程序；仅审计时不要运行会覆盖交付文件的生成命令 |

独立论文分支 `codex/thesis-finalization-20260920@29ae335` 仍有 7 个未合并提交，包含 Word/PDF/PPT、封面声明、答辩讲稿、文档脚本和验证记录；当前 `dev` 已选取完整正文，其他成果未整体接入。该分支已建立固定归档标签，具体入口和恢复命令见 [历史成果索引](archives/20261028-historical-branches.md)。旧 Windows 绝对路径仅作历史定位，当前正文与图示继续使用 dev 版本。

完整 Word/PDF 重导、draw.io 软件实开和默认真实模型联网验收仍为既有待验证事项。本次目录整理不改变其状态。

[仓库整理报告](notes/仓库整理报告-20261027.md)列出逐分支建议、拟删除清单和保护范围；[Git 同步与分支管理](notes/Git同步与分支管理.md)说明双端操作。
