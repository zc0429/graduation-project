# 九章论文审计与交付验证

审计基线：Draft PR #5，`ed7d94c1fa9666e8156528b18c633ec76ce86cf5`。应用测试和文献核验执行于2026-11-12，最终排版复核于2026-11-13。目录名保留启动日期。所有修正在`codex/learning-delivery-20261112`完成，不合并dev，不修改PR #1/#4。

交付：[正文](../../thesis/毕业论文.md)、[DOCX](../../../output/thesis/thesis-audit-20261112/毕业论文.docx)、[PDF](../../../output/thesis/thesis-audit-20261112/毕业论文.pdf)、[文献逐条核验](../../references/参考文献核验-20261112.md)、[逐页复核](visual-review.md)。本轮修正文稿、图示、排版和证据定位；应用功能沿用PR #5基线，SQL仅修改注释，浏览器用例仅改变截图保存目录。

## 依据及核验范围

执行优先级为导师最新明确要求、2027届学校模板与规范、《参考论文1》的结构/分析/图表方法、实际实现和测试证据。导师要求来源包括本次用户明确转述、仓库导师记录，以及Google Drive“毕业设计”材料中的2026-11-01胡韬会议逐字稿（[原会议压缩包](https://drive.google.com/file/d/133DpKG1TrVD724VA6xi5WUsmpsDThftG/view)）。逐字稿已通读：00:32平台先处理；01:34标识AI模型；02:43区分知识学习和做题、先查再生成保存；05:35记录实际已练题目；07:22学习与复习合图、适配A4；08:55管理/教师分支；12:11需求、用例、DFD及字典；19:50非功能与模型要求。没有获得微信群最新通知原文，不能声称已独立核实群内所有新要求。

学校母版为`docs/materials/27届毕业设计学校通知和模板/附件3：毕业论文（设计）相关模板（2027）/附件4：毕业论文（设计）正文模板.docx`；SHA-256见[document-check.json](document-check.json)。直接加载母版并保留原始页眉等包部件，未另造近似模板。模板冲突以导师指定母版实际段落为准：章标题14pt黑体，正文12pt宋体/Times New Roman、固定20pt；目录一级14pt黑体、二三级12pt黑体、1.5倍行距；文献10.5pt、22pt行距、无悬挂缩进。左边距2.75cm，其余2.5cm，页眉页脚1.5cm；摘要罗马页码、正文重新从1开始。章间9个真正的Word分页符；三张业务图采用横向A4节。

《参考论文1》用于九章安排、业务泳道、分层数据流与黑白图表分析方式，不复制该论文的调查、功能或实验结论。

## 九章审计结果

| 章节 | 核对及修正 | 证据/边界 |
|---|---|---|
| 1 绪论 | 背景、意义和研究工作与错题平台一致；调整前置引用使首次出现严格按1—32顺序 | 绪论1224个中文字符，不把模型能力表述为本系统已证明的教学收益 |
| 2 文献综述 | 原20篇保号逐篇评述；新增12篇近期研究；压缩重复表述 | 2254个中文字符、去标记非空字符2551，符合2000—3000范围；不是Word官方统计 |
| 3 需求分析 | 14项需求、6个核心用例、三张业务图、顶层/0层/P4的1层DFD和字典相互追踪；五类非功能与模型需求 | 学习入口改为本人原题或复习任务原题；读取不算已练；作答与完成复习独立；DFD父子边界重新计算一致 |
| 4 相关技术 | 核对Vue、Spring Boot、MyBatis-Plus/MySQL、GLM、RAG实际用途 | RAG检索与已生成资源复用分开；未写成训练了知识追踪或自适应推荐模型 |
| 5 概要设计 | 分层、8类实现模块、角色/数据范围及可靠性边界一致 | 教师仅系统聚合，无班级/师生关联；外部模型不直接写库 |
| 6 详细设计 | 11表88字段及约束/索引逐项匹配DDL；39个映射的方法、路径、角色逐项匹配；补学习服务和访问控制职责 | 3公开、36鉴权；修正learning_content的8字段约束及索引名称；Mapper示例明确省略部分方法；逻辑关联不冒充物理外键 |
| 7 开发实现 | 缓存命中、原题优先、未练筛选、耗尽生成、显式重做、快照失效与权限对应代码 | 历史真实GLM截图与历史Mock图片识别截图保留并注明批次；不将旧界面当成新功能验证 |
| 8 系统测试 | 分开历史实验、PR #5前一批MySQL8.4验证与本次MySQL8.0.46验证；更新本次真实浏览器截图 | 只陈述实际执行的测试；保留失败记录；取消真人体验，不虚构满意度、教学效果或性能数字 |
| 9 总结展望 | 已完成与限制对应实现和证据 | 个人隔离、快照匹配、重做等为已实现的暂定规则，仍待导师最终认可；不列真人体验待办 |

[code-thesis-audit.json](code-thesis-audit.json)记录静态一致性、DFD、图表编号和历史保护检查；[runtime-schema-check.json](runtime-schema-check.json)及[mysql-columns.tsv](mysql-columns.tsv)来自本轮实际数据库的88列回读。29图、22张逻辑表（含续表共24个Word表格）、77个目录目标均已校验。第1—9章中文字符合计27287，统计口径见[word-count.json](word-count.json)，不等同于学校系统字数或查重结果。

## 文献数量与真实性

| 项目 | 结果 |
|---|---|
| 总数 | 32篇，要求一般不少于20篇 |
| 按撰写年2026的近三自然年2024—2026 | 24篇，达到15篇 |
| 按毕业届2027的近三自然年2025—2027 | 截至审计日已正式发表15篇，达到15篇；没有预填未来2027文献 |
| 外文 | 7篇（6篇英文、1篇德文），按语种而非作者国籍统计 |

原[1]—[20]全部保留编号；[10]作者更正为喻彦琨，[16]按出版社正式年更正为1994。新增[21]—[32]均有可检索来源，正式年采用卷期年，不依据DOI中的数字或网页检索年。[24][25]核验到国家科技期刊开放平台题录与摘要，未宣称核读全文。文献库、论文文末与正文引用同步，32项均有正文实质引用，引用上标链接到文末书签。旧24项工作文献库完整归档到`docs/references/archive/pre-audit-20261112/`。

学校材料没有明确“近三年”是自然年还是滚动36个月。两种常见自然年口径均已达标；最终统计基准仍请导师确认。批准的开题报告及导出件完全不改，不反向替换其历史文献。

## 本轮实际测试

环境：JDK21.0.13、Node.js24.22.1、MySQL8.0.46、系统Chromium；隔离数据库`wrongbook_audit`，显式Mock模型，图片识别关闭。数据库容器仅监听本机，本轮结束已移除临时容器/卷，保留元数据和日志；未访问或清理本人原数据库。

| 验证 | 结果 | 原始证据 |
|---|---|---|
| Maven后端全量 | 106项，102通过、4按条件跳过，0失败/错误 | [backend-tests.log](backend-tests.log) |
| Vitest前端 | 33/33通过 | [frontend-unit.log](frontend-unit.log) |
| 类型检查及生产构建 | 通过；保留主包约773.7KB的大包警告 | [frontend-build.log](frontend-build.log) |
| 实际Spring Boot + MySQL + Chromium | 5/5通过，44秒 | [browser-integration.log](browser-integration.log)、[backend-runtime.log](backend-runtime.log) |
| 运行数据库与论文/DDL | 11表88字段，列名/类型/可空/默认/自增匹配 | [runtime-schema-check.json](runtime-schema-check.json) |
| 文献、代码/图表、DOCX/PDF | 校验通过；90页均渲染并目检 | 三个校验脚本、[document-check.json](document-check.json)、[visual-review.csv](visual-review.csv) |

浏览器5项包括新增资源闭环（知识保存后复用、本人原题优先、首批3题耗尽后累计6题、显式重做）及学生增删改练习/导出、教师聚合范围、管理员页面、私有图片归属。真实运行是指页面、后端和数据库实际执行；生成内容来自Mock，不是新的GLM联网验证。

四个跳过入口是`LiveQuestionRecognitionTests`、`LiveGlmValidationTests`、`EmbeddingRebuildMaintenanceLiveTests`、`Gate5AiRagExperimentTests`。本轮没有重跑53项页面冒烟、真实GLM、图片AI或历史Gate5实验，不把历史数据累计为新样本。真人体验测试按用户要求取消。

原始日志保留工具输出的行尾空格，MySQL TSV保留空末列的制表符；这些证据不为通过空白检查而改写。其余源稿/脚本和生成CSV通过`git diff --check`。

失败也保留：第一次Maven运行误用测试配置默认3307端口，连接失败，完整见[backend-first-environment-failure.log](backend-first-environment-failure.log)；随后显式配置`TEST_DB_URL`到隔离3306端口并重新全量执行通过。首次文档导出遇到本轮Docker VFS缓存占满磁盘，清理可重建缓存并在完成数据库回读后移除本轮临时数据库，重导成功。`backend-runtime.log`末尾连接错误发生在验证结束、临时数据库停止的清理阶段，不计为额外测试通过记录。

复现应用测试：按项目测试配置提供隔离数据库的`TEST_DB_URL / TEST_DB_USERNAME / TEST_DB_PASSWORD / TEST_UPLOAD_DIR`后执行`bash mvnw test`；本云端JDK缺ct.sym时附加`-Dmaven.compiler.release= -Dmaven.compiler.source=21 -Dmaven.compiler.target=21`。前端执行`npm run test:unit -- --maxWorkers=2`及`npm run build`；在真实后端以显式Mock启动后，执行`PLAYWRIGHT_CHROMIUM_EXECUTABLE=/usr/bin/chromium npm run e2e:integration`。环境变量和代理凭据保存在忽略目录，不入库。文档复现命令见[scripts/cloud/README.md](../../../scripts/cloud/README.md)。

## 历史保护与尚需本人/导师确认

相对基线逐字节保护186个文件：学校材料、已通过开题及导出、历史实验/截图、历史论文交付目录等均一致。新业务图和截图写入新目录；没有覆盖PR #1候选图或PR #4成果。远程PR状态以最终交接说明及GitHub实际记录为准。

本轮PDF使用合法替代字体，DOCX仍声明学校要求字体；**原版宋体、黑体、Times New Roman尚未核验**。在合法具备原字体的Word环境中更新域并导出后，应再核对分页。需本人提供或与导师核对微信群最新通知原文；请导师确认近三年统计基准和已实现的暂定资源规则。当前模型新增功能的真实联网质量尚未新测，历史证据不能替代；查重、本人签字和学校系统提交由本人办理。本报告不声称导师审批或学校验收已通过。
