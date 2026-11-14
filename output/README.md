# 导出交付目录

本目录保存**阶段性交付成果而非编译缓存**。PR #5 已于2026-11-13交付学校2027届母版论文新版；本次集成审计只标识最新版，不覆盖任何已跟踪原件、开题报告、历史图或日志。

| 位置 | 用途与保留规则 |
|---|---|
| [thesis/thesis-audit-20261112/](thesis/thesis-audit-20261112/) | **当前最新九章论文** DOCX/PDF，90页、29图22表；原版字体尚未验收 |
| [thesis/learning-delivery-20261112/](thesis/learning-delivery-20261112/) | PR #5前一阶段88页DOCX/PDF，保留为历史交付，不是最新提交版 |
| docx/、pdf/ 下的任务书与开题报告 | 学校提交文件、视觉校正版等历史成果；已通过开题报告不修改、不删除 |
| backup/2026-09-03-before-template-align/ | 模板对齐前的开题 Word/PDF，作为历史备份保留 |
| pdf/thesis-figures/ | 论文单图 PDF 与历史 A4 校样；旧综合校样不代表 10 月 26 日更新后全部插图的状态 |
| pdf/业务流程图-导师讲解版.pdf | 当前三张泳道图的合并讲解件，源文件在 docs/thesis/business-flow/ |
| pdf/导师意见落实-图示校样-20261026.pdf | 导师修改轮图示校样，保留其验证用途 |
| 文献综述-系统粘贴版.txt、开题报告格式修改说明.md | 系统粘贴交接与修改记录，保留阶段用途 |
| handoff/（本地忽略） | 本地 ZIP/bundle 交接包；忽略不等于可删除，唯一备份应另存并核实可恢复 |

**状态区分**：截至本次集成PR创建，最新90页DOCX/PDF仍在PR #5及集成候选分支，未必已进入远程`dev`。2026年9月历史`论文审阅版.docx/.pdf`、`答辩审阅版.pptx`和封面声明留在`codex/thesis-finalization-20260920@29ae335`及固定标签；不得用旧文件覆盖现行90页论文。

可重建的本地缓存主要为 `server/target/`、`web/node_modules/`、`web/dist/` 和 Python 缓存。`web/test-results/` 可能含尚未归档的失败证据，清理前先筛选。以上均不与本目录的交付导出件混用。
