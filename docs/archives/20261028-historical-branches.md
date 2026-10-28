# 历史分支成果清单（2026-10-28）

比较基准为 `dev@2d5a135f7d22b08673613f268904ddb5c931bb0a`。归档标签固定完整原树；“dev 中不存在的路径”只说明路径差异，不能直接等同于重要新功能。两个原分支继续保留。

## codex/thesis-finalization-20260920

固定标签 `archive/thesis-finalization-20260920-20261028`，剥离后提交 `29ae335c98d9944a50360ed8ffa9a1b07f70cd15`；完整快照 536 个文件、42,711,730 字节，7 个独有提交。

重点是历史 `output/docx/论文审阅版.docx`、`output/pdf/论文审阅版.pdf`、`output/pptx/答辩审阅版.pptx`、封面声明、答辩讲稿、`scripts/documents/` 文档工具与 XSD，以及 `docs/notes/thesis-run-20260920/` 验证证据。当前完整正文已经接入并在 dev 后续更新，这些历史导出件仍属于 9 月版本。

相对当前 dev 有 99 个仅归档树存在的路径：其中 94 个是上轮识别的配套成果，另 5 个是本轮之前已经从 dev 删除的旧空 `.gitkeep`。这 5 个占位文件只随原树保存，不恢复到 dev。

独有提交：

- `29ae335c98d9944a50360ed8ffa9a1b07f70cd15 fix: 论文参考文献统一为开题20篇及原顺序`
- `4774c94e97f01231c1c1737cee5e8204d0eef30f fix: 稳定论文目录更新并补齐封面声明与待办`
- `000e473c68d04b4b48405be915acc5a6830d7f08 fix: 完成离线文档校验与本机Mock演示验证`
- `74ab2956156ed2525600d07ed11c959bc1f8f301 fix: 修正论文目录格式并开放文档工具路径配置`
- `5c942384d673aa1d917c94627109c7791d2a7350 docs: 核对导师范例开题与论文文献顺序`
- `e66095b3ff8346bc9bc0e0cc9a78a8720beaa064 docs: 完成交接自检并记录实际验收边界`
- `86ff8c7db523484a1a61532e1d3dff535b11482e docs: 完成论文审阅导出与答辩材料本地交付`

<details>
<summary>相对当前 dev 不存在的路径清单</summary>

| 路径 | 字节 |
|---|---:|
| `.gitattributes` | 217 |
| `docs/notes/thesis-run-20260920/ACCEPTANCE.md` | 2877 |
| `docs/notes/thesis-run-20260920/BLOCKERS.md` | 2751 |
| `docs/notes/thesis-run-20260920/CHANGELOG.md` | 1530 |
| `docs/notes/thesis-run-20260920/CHAPTER2-AFTER.md` | 8201 |
| `docs/notes/thesis-run-20260920/CHAPTER2-BEFORE.md` | 6298 |
| `docs/notes/thesis-run-20260920/CONTINUATION-20260921.md` | 5726 |
| `docs/notes/thesis-run-20260920/DEFENSE-QA.md` | 1072 |
| `docs/notes/thesis-run-20260920/DELIVERY.md` | 3380 |
| `docs/notes/thesis-run-20260920/DEMO-RUNBOOK.md` | 4222 |
| `docs/notes/thesis-run-20260920/DOCUMENT-QA.md` | 5433 |
| `docs/notes/thesis-run-20260920/DOCX-FULL-VALIDATOR-ENVIRONMENT.txt` | 273 |
| `docs/notes/thesis-run-20260920/DOCX-OFFLINE-XSD.json` | 3872 |
| `docs/notes/thesis-run-20260920/DOCX-OFFLINE-XSD.txt` | 765 |
| `docs/notes/thesis-run-20260920/DOCX-STRUCTURE-CHECK.txt` | 908 |
| `docs/notes/thesis-run-20260920/EXECUTION-PROMPTS.md` | 35526 |
| `docs/notes/thesis-run-20260920/EXPERIMENT-RECALC.md` | 1033 |
| `docs/notes/thesis-run-20260920/FIGURE-TABLE-AUDIT.md` | 994 |
| `docs/notes/thesis-run-20260920/FRONTMATTER-CHECK.txt` | 762 |
| `docs/notes/thesis-run-20260920/HANDOFF-CHECK.md` | 3147 |
| `docs/notes/thesis-run-20260920/NATIVE-APP-CHECK.json` | 425 |
| `docs/notes/thesis-run-20260920/NEXT-AGENT-PROMPT.md` | 2447 |
| `docs/notes/thesis-run-20260920/NEXT.md` | 2016 |
| `docs/notes/thesis-run-20260920/OFFLINE-XSD-RENDER-COMPARE.json` | 236 |
| `docs/notes/thesis-run-20260920/OPENING-TO-THESIS.md` | 3166 |
| `docs/notes/thesis-run-20260920/PRIORITY-FIXES-20260921.md` | 4668 |
| `docs/notes/thesis-run-20260920/REFERENCE-ALIGNMENT-20260922.md` | 3528 |
| `docs/notes/thesis-run-20260920/REFERENCE-AUDIT.md` | 1513 |
| `docs/notes/thesis-run-20260920/REPRODUCE.md` | 4067 |
| `docs/notes/thesis-run-20260920/REQUIRED-INPUTS.md` | 1044 |
| `docs/notes/thesis-run-20260920/RUN-OWNERSHIP.md` | 2113 |
| `docs/notes/thesis-run-20260920/SCHOOL-REQUIREMENTS-STRUCTURE.json` | 635405 |
| `docs/notes/thesis-run-20260920/SCHOOL-REQUIREMENTS-TEXT.txt` | 27853 |
| `docs/notes/thesis-run-20260920/SOURCE-MANIFEST.md` | 776 |
| `docs/notes/thesis-run-20260920/STATE.md` | 2593 |
| `docs/notes/thesis-run-20260920/TEMPLATE-STRUCTURE.json` | 551480 |
| `docs/notes/thesis-run-20260920/TEMPLATE-TEXT.txt` | 13851 |
| `docs/notes/thesis-run-20260920/TEST-EVIDENCE-INDEX.md` | 1059 |
| `docs/notes/thesis-run-20260920/THESIS-CHANGES.diff` | 28119 |
| `docs/notes/thesis-run-20260920/THESIS-CONSISTENCY.md` | 2834 |
| `docs/notes/thesis-run-20260920/artifact.md` | 3878 |
| `docs/notes/thesis-run-20260920/current-baseline.json` | 27590 |
| `docs/notes/thesis-run-20260920/current-figure-check.json` | 341 |
| `docs/notes/thesis-run-20260920/defense-notes.json` | 6737 |
| `docs/notes/thesis-run-20260920/document-check.json` | 1626 |
| `docs/notes/thesis-run-20260920/heading-keys.json` | 2860 |
| `docs/notes/thesis-run-20260920/mock-demo-20260921/01-mock-analysis.png` | 181846 |
| `docs/notes/thesis-run-20260920/mock-demo-20260921/02-mock-variants.png` | 192231 |
| `docs/notes/thesis-run-20260920/mock-demo-20260921/03-practice-recorded.png` | 191468 |
| `docs/notes/thesis-run-20260920/mock-demo-20260921/05-report.png` | 197212 |
| `docs/notes/thesis-run-20260920/mock-demo-20260921/SHA256.json` | 1601 |
| `docs/notes/thesis-run-20260920/mock-demo-20260921/attempt1-browser-result.json` | 301 |
| `docs/notes/thesis-run-20260920/mock-demo-20260921/attempt1-environment-result.json` | 703 |
| `docs/notes/thesis-run-20260920/mock-demo-20260921/attempt2-browser-result.json` | 549 |
| `docs/notes/thesis-run-20260920/mock-demo-20260921/attempt2-environment-result.json` | 745 |
| `docs/notes/thesis-run-20260920/mock-demo-20260921/demo-browser.mjs` | 5752 |
| `docs/notes/thesis-run-20260920/mock-demo-20260921/final-browser-result.json` | 5536 |
| `docs/notes/thesis-run-20260920/mock-demo-20260921/final-environment-result.json` | 744 |
| `docs/notes/thesis-run-20260920/mock-demo-20260921/run-demo.py` | 6504 |
| `docs/notes/thesis-run-20260920/opening-reference-check.json` | 4194 |
| `docs/notes/thesis-run-20260920/page-map.json` | 771 |
| `docs/notes/thesis-run-20260920/pdf-page-image-hashes.json` | 4630 |
| `docs/notes/thesis-run-20260920/ppt-slide-image-hashes.json` | 905 |
| `docs/notes/thesis-run-20260920/presentation-validation.json` | 7286 |
| `docs/notes/thesis-run-20260920/priority-fix-check.json` | 1644 |
| `docs/notes/thesis-run-20260920/reference-map.json` | 2882 |
| `docs/notes/thesis-run-20260920/reference-year-check-20260921.json` | 2232 |
| `docs/notes/thesis-run-20260920/word-count.json` | 451 |
| `docs/notes/导师范例开题与论文文献顺序核对.md` | 4294 |
| `docs/notes/毕设待完成事项.md` | 5468 |
| `docs/thesis/毕业设计封面与诚信声明.md` | 945 |
| `docs/thesis/答辩追问要点.md` | 3973 |
| `docs/thesis/答辩逐页讲稿.md` | 7608 |
| `output/docx/毕业设计封面与诚信声明-待签署.docx` | 76529 |
| `output/docx/论文审阅版.docx` | 2123968 |
| `output/pdf/毕业设计封面与诚信声明-待签署.pdf` | 133076 |
| `output/pdf/论文审阅版.pdf` | 3983642 |
| `output/pptx/答辩审阅版.pptx` | 124397 |
| `scripts/documents/align_thesis_references_to_opening.py` | 4219 |
| `scripts/documents/align_thesis_review.py` | 6645 |
| `scripts/documents/build_defense.mjs` | 14599 |
| `scripts/documents/build_thesis_frontmatter.py` | 4097 |
| `scripts/documents/build_thesis_review.py` | 20896 |
| `scripts/documents/inspect_thesis_materials.py` | 1932 |
| `scripts/documents/package_thesis_handoff.py` | 4268 |
| `scripts/documents/record_thesis_audit.py` | 11950 |
| `scripts/documents/schemas/dublincore/README.md` | 546 |
| `scripts/documents/schemas/dublincore/dc.xsd` | 4112 |
| `scripts/documents/schemas/dublincore/dcmitype.xsd` | 1442 |
| `scripts/documents/schemas/dublincore/dcterms.xsd` | 11171 |
| `scripts/documents/schemas/dublincore/sources.json` | 874 |
| `scripts/documents/schemas/dublincore/xml.xsd` | 4726 |
| `scripts/documents/verify_docx_offline.py` | 5821 |
| `scripts/documents/verify_thesis_review.py` | 9633 |
| `server/src/main/java/com/example/wrongbook/dto/.gitkeep` | 0 |
| `server/src/main/java/com/example/wrongbook/service/.gitkeep` | 0 |
| `server/src/main/java/com/example/wrongbook/service/impl/.gitkeep` | 0 |
| `server/src/main/java/com/example/wrongbook/util/.gitkeep` | 0 |
| `server/src/main/java/com/example/wrongbook/vo/.gitkeep` | 0 |

</details>

## codex/reference-freeze

固定标签 `archive/reference-freeze-20261028`，剥离后提交 `7698cadd9a448b3e4b78ce7f934ea6cc922446db`；完整快照 332 个文件、21,757,153 字节，3 个独有提交。

该分支保留早期文献冻结与引用调整，以及普通子提交删除 Word 锁文件的记录。主要文献文件在当前 dev 也有后续版本，属于同路径历史差异；不表示其内容已经整体合并。

仅此分支存在的 5 个路径全部为旧空占位文件，没有新的待拷贝业务文件。文献元数据、任务书、开题和旧论文差异应在需要时针对性审阅；本次不修改已通过开题报告。

独有提交：

- `7698cadd9a448b3e4b78ce7f934ea6cc922446db chore: 删除历史文献分支误提交的Word锁文件`
- `7a80cb9542d5c1f2caa2bf100579c30aae8e9966 Create ~$2：云南工商学院本科毕业论文（设计）.docx`
- `9ac47700f709be522f90b2e27c371d725aa45543 docs: 冻结参考文献与引用编号`

<details>
<summary>相对当前 dev 不存在的路径清单</summary>

| 路径 | 字节 |
|---|---:|
| `server/src/main/java/com/example/wrongbook/dto/.gitkeep` | 0 |
| `server/src/main/java/com/example/wrongbook/service/.gitkeep` | 0 |
| `server/src/main/java/com/example/wrongbook/service/impl/.gitkeep` | 0 |
| `server/src/main/java/com/example/wrongbook/util/.gitkeep` | 0 |
| `server/src/main/java/com/example/wrongbook/vo/.gitkeep` | 0 |

</details>

## 取用与后续处理

获取命令见 [归档入口](README.md)，固定标签对象、源头、树和文件哈希见 [archives.json](../validation/repository-maintenance-20261028/archives.json)。本轮通过远程标签剥离 SHA 和树一致性验证；没有生成新 Word/PDF/PPT，没有在 Office 或 draw.io 中进行打开验收。

未来需要接入文档工具或讲稿时，从归档逐项选取并按当前系统事实复核；两个原分支的保留/关闭另行决定。标签不因将来分支推进而改变。
