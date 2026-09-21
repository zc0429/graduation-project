# 本轮交付索引

本轮新增：`output/docx/毕业设计封面与诚信声明-待签署.docx` 及同名PDF（2页）；源稿 `docs/thesis/毕业设计封面与诚信声明.md`，构建器 `scripts/documents/build_thesis_frontmatter.py`；当前完整待办 `docs/notes/毕设待完成事项.md`。已纳入更新后的交接包。
2026-09-21，Asia/Shanghai。工作树 D:/Documents/GitHub/graduation-project-thesis-20260920。
**可移交审阅版，论文终稿partial。** 本地分支完成后未推送/合并；最终提交与干净状态见 [本机Git快照](../../../output/handoff/LOCAL-STATUS.json)。该快照在本地提交后生成，不入Git，包含在ZIP中。

## 最先打开
|文件（相对仓库根）|用途|验收|
|---|---|---|
|output/pdf/论文审阅版.pdf|61页，直接审阅|全文逐页查看，机器检查见DOCUMENT-QA|
|output/docx/论文审阅版.docx|同内容可编辑件|原生域/书签齐；Word F9仍待|
|output/pptx/答辩审阅版.pptx|12页可编辑答辩稿|全12页查看、包及图表检查|
|docs/thesis/答辩逐页讲稿.md|约6分40秒建议配时|与12页备注一致，待真人计时|
|docs/thesis/答辩追问要点.md|15个追问|依据真实实现和小样本边界|
|docs/notes/thesis-run-20260920/DEMO-RUNBOOK.md|现场Mock流程和历史GLM证据分开|本机Mock已验证；作者计时与PowerPoint实开待办|
|docs/notes/HANDOFF.md|后续agent入口|HANDOFF-CHECK交接自检|

## 可复用来源
- docs/thesis/毕业论文.md：语义源；此次改动第二章核心对齐、4篇补充收敛和全文引用编号。
- docs/thesis/figures/：保留17图sources JSON、SVG/PNG与说明，未重画。
- scripts/documents/build_thesis_review.py：独立正文模板生成器；verify_thesis_review.py：内容/字段/分页/引用校验。
- scripts/documents/build_defense.mjs：可编辑幻灯片生成及最终化。
- scripts/documents/align_thesis_review.py：仅针对基线的单次修订，可重建身份映射；不要对已修订稿反复运行。
- REFERENCE-MAP / REFERENCE-AUDIT、THESIS-CHANGES.diff：24项身份、编号与局部差异。
- THESIS-CONSISTENCY、FIGURE-TABLE-AUDIT、EXPERIMENT-RECALC、TEST-EVIDENCE-INDEX：事实与证据边界。
- ACCEPTANCE、BLOCKERS、STATE、NEXT、NEXT-AGENT-PROMPT：收尾和后续队列。

## 本地包与异机接手
交接包在 output/handoff/毕设审阅与交接包-20260921.zip；目录同时有 PACKAGE-MANIFEST.json、ARCHIVE-SHA256.txt、LOCAL-STATUS.json 和增量 thesis-20260920.bundle。
ZIP包含审阅件、语义源、图源/PNG/SVG、构建脚本、审计与交接记录、增量Git提交；不包含.env、凭据、node_modules、临时渲染、旧备份或学校原始个人材料。文档示例中的变量名不是凭据。
完整复现需要已有基线仓库及其学校模板、开题/文献/历史验证；这些可从有权限的私有仓库dev基线取得，不把图源包冒称整个系统备份。
异机先取得ZIP和该私有仓库的基线提交，核对SHA256清单，再git bundle verify增量包；在新独立分支/工作树载入增量HEAD，勿覆盖有修改的目录。包未上传任何外部服务。
本机原仓库 D:/Documents/GitHub/graduation-project 的两项未提交修改保留，未混入本轮提交。后续推送/合并需明确指令。
