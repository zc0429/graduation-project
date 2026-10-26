# 导师意见落实：本轮验证记录

验证日期：2026-10-26。系统基线 `origin/dev@aae3784`，论文内容基线 `origin/codex/thesis-finalization-20260920@29ae335`。独立工作树 `/workspace/graduation-project-advisor`，分支 `codex/advisor-update-20261026`。所有结果来自本轮执行；旧验证记录、Gate5和真实截图未改写。

## 环境与隔离

JDK 21完整工具链、Maven Wrapper 3.9.16、Node 24.19.0、MySQL 8.4独立容器。测试库 `wrongbook_test`，绑定本机3307；后端Mock服务仅本机8080，缺密钥GLM配置服务仅本机8082。测试密码由临时环境文件注入，文件位于仓库外，不写入本记录。Maven经会话代理下载依赖，凭据和认证头不输出。

前端UI冒烟拦截API并返回固定响应；真实后端浏览器联调用MySQL和Mock AI；缺密钥检查使用真实GLM客户端配置但在发送网络请求前拒绝。因此它们都不是本轮真实GLM服务可用性的证据。

## 实际命令与结果

| 工作目录 | 命令 | 本轮结果 |
|---|---|---|
| 仓库根（最后一轮） | `server/mvnw -f server/pom.xml -s /workspace/scratch/maven-settings.xml test`（进程环境指定完整JDK及TEST_DB变量） | 84项：80通过、4跳过、0失败、0错误 |
| `web` | `npm run verify` | typecheck通过；Vitest 29/29；生产构建通过；四档Mock浏览器46/46 |
| `web` | `npm run e2e:integration` | 4/4，通过真实Spring Boot + MySQL + Mock AI联调 |
| `web` | `npx playwright test e2e/smoke/student-questions.spec.ts --config=playwright.ui.config.ts --project=chromium-desktop` | 5/5专项复查 |
| `web` | `npx playwright test e2e/smoke/rich-question.spec.ts --config=playwright.ui.config.ts --project=chromium-desktop` | 2/2，另生成带Mock标记的合成图片界面截图 |
| 仓库根 | `RUN_ADVISOR_API_CHECK=true python scripts/validation/advisor_runtime_check.py` | Mock链路与真实配置缺密钥检查均通过，见runtime-check.json |
| 仓库根 | `python scripts/documents/build_business_swimlanes.py` | 三页可编辑XML结构及A4 PDF、SVG、300 dpi PNG生成通过 |
| 仓库根 | `python scripts/documents/sync_advisor_figures.py` | 只更新图3.2/3.3/3.4/4.1/5.2，生成五页A4校样 |
| 仓库根 | `python scripts/documents/verify_advisor_delivery.py` | 22图、16表编号连续，10表80字段、36接口一致，20篇参考文献保持最新完整稿原样；三图无节点重叠、边引用有效、标注最小9.34pt；保护文件28份字节未变 |
| 仓库根 | `git diff --check` | 通过 |

最后收窄变式题头部的flex选择器，避免新题干组件的段落被并排排版；`npm run build`再次通过，AI/练习与富文本两份浏览器专项共6/6通过，输出见`frontend-build-final.txt`、`ai-rich-final-recheck.txt`。

前端构建仍有既有大chunk提示，不属于构建失败，本轮未扩展为打包架构重构。后端默认跳过的是Gate5、Embedding重建、真实GLM及真实图片识别入口；未打开付费调用开关。

## 覆盖的关键行为

- DOMPurify与Jsoup白名单：脚本、事件、属性、外链和内嵌资源过滤，空富文本拒绝，2000字纯文本及原始格式大小限制。
- 旧纯文本的比较符、换行兼容；Tiptap保存、重新打开、格式回显；详情、列表及练习安全展示。
- 图片候选按纯文本转义后回填，可继续富文本编辑；确认前没有错题POST；学生作答不污染正确答案；识别失败仍能手工保存。
- MySQL实际保存安全题干、创建五条计划；练习后编辑保留记录和掌握度；待复习列表与手动完成更新真实状态，完成时间有值、日期不重排；复习摘要及XLSX实际单元格无格式标签。
- Embedding、解析与变式提示词使用规范化文本；新增离线用例验证默认GLM请求参数与1024维配置，旧模型显式配置仍可测试。
- 既有数据隔离、异步失效、事务回滚、私有题图和三角色权限回归。
- 隔离Mock API实际完成解析、生成3题、自评正确后15、自评错误后0及周报；没有用这一结果声称真实生成质量。
- 无密钥GLM服务可启动并手工保存；解析、图片识题、变式请求明确报缺密钥，解析记录不伪造成功，不返回Mock结果，已保存题目保留。

## 失败过程与修复

1. 初次Maven无法直连网络，按会话代理配置后可下载；随后发现默认Java只有运行时、缺编译器，使用独立完整JDK修复。未更改项目Java版本或Spring Boot版本。
2. 新编辑器组件单测初次2项失败，原因是Vue/Tiptap挂载跨多次nextTick，等待实际挂载后29项通过。
3. 原44项UI首轮40通过、4失败，均为旧测试按题干标签定位时同时匹配表单分组与富文本框；改为精确textbox角色。加入2项富文本测试后第二轮45通过、1失败，原因是“删除”还匹配“删除线”；改为精确按钮名称。专项5/5、2/2复查及最后完整46/46通过，首轮与第二轮日志都保留。
4. API验证脚本首次错误地把响应体业务成功码当成HTTP 200；修正为分别检查HTTP状态和有效data后完整重跑通过。没有修改接口成功码来迎合测试。
5. 绘图结构检查初次发现两条连接穿过无关节点，调整路径后通过；没有关闭避让断言。

## 证据文件

`test-summary.json`按Surefire实际报告汇总；`backend-tests.txt`、`frontend-verify.txt`、`integration.txt`保存本轮输出。`smoke-first-failure.txt`与`smoke-second-failure.txt`保留失败过程，两个targeted-recheck文件保留专项复查。文本日志只移除ANSI控制符，并防御性替换测试密码，不改写测试结果。

`runtime-check.json`保存两种运行模式的实际结果；`document-check.json`保存正文、图源和历史文件检查。截图位于 `docs/thesis/screenshots/advisor-20261026/`，顶部标注Mock；图导出及逐图目检见 `docs/thesis/business-flow/verification.json`。

## 未执行的验收

本轮环境没有真实GLM密钥，未执行新的联网Chat、图片识题、Embedding或真实RAG/变式测试。历史记录不作为本轮通过项。draw.io仅通过XML节点与连线检查，未在软件中移动节点并保存。完整论文DOCX/PDF未重新导出，Word字段刷新、字体替换和分页仍待复核。未新增真人用户测试、压力测试、长期学习效果或教学准确率数据。
