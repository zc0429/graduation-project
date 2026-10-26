# advisor-update-20261026 合并验证记录

日期：2026-10-26；目标工作树 `/workspace/graduation-project`，目标分支 `dev`。

## 合并前检查与策略

刷新远程后，dev为 `aae3784d0fb93bc7864878d80bcbd412b605ce5e`，交付分支为 `f1baeb122f77c23179dd66cf7330837adaa726be`。两个工作树均干净，无stash；本地与远程对应分支一致。`git rev-list --left-right --count origin/dev...origin/codex/advisor-update-20261026` 为 `0 3`，共同祖先正是dev原头。

保留3个原提交，用 `git merge --no-ff --no-commit origin/codex/advisor-update-20261026` 形成可追溯的双亲合并；合并无冲突。提交前的合并索引树为 `bdaf570e032556ffd9ab84fadc9b9ca9cb43d066`，与交付分支树完全相同。测试均在该合并工作树执行，不是引用此前的测试结果。

## 成果与论文保护

合并后、追加本次记录前，核对交付分支涉及的110个文件，全部与f1baeb1逐字节一致，见 `retained-delivery-files.json`。本轮后续只新增合并证据、追加进度记录；应用代码、富文本、GLM默认配置、图片识题、泳道图、完整论文、原测试和交付图像保持交付分支原样。

开题报告、学校/导师材料、Gate5与历史真实截图等53份原文件与合并前dev内容相同，见 `protected-files.json`。没有重写论文、重新生成图示或修改已经通过的开题报告；文档验证只读取既有图源和工件。最新完整论文包含第1—7章，20篇参考文献及顺序与论文定稿分支一致；没有发现其他分支中晚于本轮交付的论文正文更新。

## 本轮实际测试

使用新建的独立MySQL 8.4容器与专用wrongbook_test数据库，测试密码只从仓库外临时文件注入；JDK为独立完整21工具链，Maven使用会话代理。普通测试与联调固定Mock，真实模型和维护入口开关均关闭。

| 工作目录 | 实际命令 | 结果 |
|---|---|---|
| `web` | `npm ci` | 依锁文件安装成功，未修改依赖或锁文件 |
| `server` | `./mvnw -s /workspace/scratch/maven-settings.xml test` | 84项：80通过、4真实模型/维护入口跳过、0失败、0错误 |
| `web` | `npm run typecheck` | 通过 |
| `web` | `npm run test:unit` | 29/29通过 |
| `web` | `npm run build` | 通过；既有chunk大小提示保留，未作无关重构 |
| `web` | `npx playwright test --config=playwright.ui.config.ts --project=chromium-desktop --project=chromium-laptop --project=chromium-tablet --project=chromium-mobile --grep-invert '生成本轮界面证据'` | 45/45通过；明确排除1项会覆盖已交付截图的用例，未重制截图 |
| `web` | `npm run e2e:integration` | 真实后端+独立MySQL+Mock AI，4/4通过 |
| 仓库根 | 运行既有`verify_advisor_delivery.py`，仅在进程中将OUT指向本次临时证据目录 | 22图、16表编号连续，10表80字段、36接口、最新20篇引用、图XML与边界检查通过；未改旧验收文件 |
| 仓库根 | `git diff --cached --check`、`git diff --check` | 通过 |

原始本轮输出在本目录对应txt文件，计数见 `backend-summary.json` 和 `summary.json`。归档只去掉ANSI控制符、行尾空格与末尾空行；未改写测试结论。真实GLM联网、draw.io软件实开及完整论文Word/PDF重导仍沿用既有待验证状态，本次没有新增通过结论。

## 尚未整体合并的分支

| 分支 | 独有提交 | 重要内容与处理 |
|---|---:|---|
| `codex/thesis-finalization-20260920` | 7 | 论文正文修订及20篇引用已择取进交付稿；整分支仍保留Word/PDF/PPT、封面声明、答辩材料、导出和交接脚本。未自动导入这些较早导出件，避免与已更新正文混用。 |
| `codex/reference-freeze` | 2 | 历史文献冻结改动，包括早期论文/开题等文件及Word临时锁文件。本次不整分支合入，也不删除。 |

其他已有前后端、隔离修复、GLM、Embedding、RAG实验及图片识题分支均已是本次目标内容的祖先。两个分歧分支的文件清单及SHA保存在本目录，原分支不改写。

## 提交与推送

本次将合并成果、进度追加和本轮验证记录放入同一个双亲合并提交。实际提交号以 `git log -1 --oneline dev` 为准；推送前再次刷新远程确认dev没有新增提交，使用普通 `git push origin dev`，不强推、不改写其他分支。推送后检查远程SHA与本地dev一致。
