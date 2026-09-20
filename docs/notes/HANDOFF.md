# 毕设交接入口
更新：2026-09-21，Asia/Shanghai。项目题目：**基于智谱GLM模型的AI错题分析与学习推荐系统设计与实现**。
本轮目标为现有论文对齐、复核、审阅导出和答辩准备；本轮收尾done，移交ready，论文终稿partial。9月22日为集中推进节点，不是最终提交截止日；学校计划仍按AGENTS中2026-09-14明确通知。

## 先读这些文件
AGENTS.md → 本入口 → [STATE](thesis-run-20260920/STATE.md) → [NEXT](thesis-run-20260920/NEXT.md) → [SOURCE-MANIFEST](thesis-run-20260920/SOURCE-MANIFEST.md) → [DELIVERY](thesis-run-20260920/DELIVERY.md) → [ACCEPTANCE](thesis-run-20260920/ACCEPTANCE.md) → [BLOCKERS](thesis-run-20260920/BLOCKERS.md)。
接手指令：[NEXT-AGENT-PROMPT](thesis-run-20260920/NEXT-AGENT-PROMPT.md)。当前Codex自检：[HANDOFF-CHECK](thesis-run-20260920/HANDOFF-CHECK.md)；未声称另一agent已接手。

## 来源和授权
用户“按提示词要求执行任务”授权执行[完整提示词THESIS-20260920-V3](thesis-run-20260920/EXECUTION-PROMPTS.md)的P00→P01—P08→P11。学校系统开题/综述事项完成来自该指令中用户反馈；学校线上最终稿未直接逐字核对，也不推断其他审批。
核心依据为仓库正式开题和系统填报稿；实现依据为实际源码/Schema及带日期验证；格式最高依据是2027学校原件。本轮新证据包括身份映射、源码/图表复核、原CSV复算、导出和视觉检查。历史业务测试和模型调用不是本轮新实验。
允许常规局部文稿、构建脚本、导出与交接修订；不自动push/merge、提交学校、联系导师、使用付费模型/重置卡或新建定时续跑。

## Git和文件位置
私有仓库 git@github.com:zc0429/graduation-project.git。
实际起点与2026-09-20 fetch核实的origin/dev：**3b7fc4768e4a2588583f109133d378a050da8733**；origin/main当时落后49提交，61c0f0b仅是历史。
本轮分支 **codex/thesis-finalization-20260920**；工作树 **D:/Documents/GitHub/graduation-project-thesis-20260920**。
本地提交后生成的[LOCAL-STATUS.json](../../output/handoff/LOCAL-STATUS.json)记录**最终当前HEAD、origin/main/dev、ahead/behind、工作区状态、bundle校验**；在ZIP中亦可读取。接手时须重新git核对，快照不是永远当前。若只取得Git分支而没有本地快照，git rev-parse HEAD及git status为当前依据。
原目录 D:/Documents/GitHub/graduation-project 的2026-09-18进度日志和output/文献综述-系统粘贴版.txt受保护，未混入本轮分支。原目录新增的本地定位提示如存在，只用于指向本工作树，不替代本入口。

## 成果与验证
- [论文语义源](../thesis/毕业论文.md)、[DOCX](../../output/docx/论文审阅版.docx)、[61页PDF](../../output/pdf/论文审阅版.pdf)：已生成，文本/字段/跳转核对和全页视觉检查；不是终稿认证。详[DOCUMENT-QA](thesis-run-20260920/DOCUMENT-QA.md)。
- [12页PPTX](../../output/pptx/答辩审阅版.pptx)、[逐页讲稿](../thesis/答辩逐页讲稿.md)、[15问答](../thesis/答辩追问要点.md)、[演示流程](thesis-run-20260920/DEMO-RUNBOOK.md)：已制作/逐页检查，真人计时和现场动态验证未执行。
- 图源在docs/thesis/figures；构建脚本和证据完整索引见DELIVERY；文献身份对应见[REFERENCE-MAP](thesis-run-20260920/REFERENCE-MAP.md)。
- 环境与命令见[REPRODUCE](thesis-run-20260920/REPRODUCE.md)。实测Windows/Python3.12.14/Node24.19.0/LibreOffice26.8.0.3，无需模型密钥。

## 不能丢失的决定
复用完整七章、17图16表；10物理表80字段、36控制器映射3公开33鉴权。开题20篇是核心，论文主库24篇按身份映射、独立首引编号，4篇保留为明确补充；原主库/开题未改。
mastery为题目级规则分值，正确+15、错误−20、有界0—100，推荐不读取它。复习固定1/2/4/7/15天。未训练BKT/DKT。27题46/54、评分20/6/1，6组RAG ON2/OFF4；不推断一致优势、普遍准确率或长期教学效果。

## 下一步和最少人工事项
前三步均在NEXT中写明输入、动作和验收：①具备Word时更新域并导出复核；②根据作者事实/明确计年口径补封面致谢及文献；③作者演练和隔离本机Mock现场验证。单项缺条件不阻塞独立项。
需补事实：正式封面/完成日期、真实致谢；若线上稿曾改动，提供最终稿；确认“近三年”基点。需真人/环境：Word、现场演练、真实用户体验、Visio。所有尝试与解除条件见BLOCKERS。
追加“镜像”请求仍待具体含义，不据此修改远程或部署环境。

## 运行所有权与可获取性
本轮运行所有者为当前Codex；最终回复后不再写入。已启动的文档构建/渲染均应在移交快照前结束，实际检查见[RUN-OWNERSHIP](thesis-run-20260920/RUN-OWNERSHIP.md)。不要假定当前任务结束等于所有宿主任务停止，接手前再次核对。
本轮没有创建自动续跑；已检查本地自动化目录的结果见运行记录。下次时间未配置；外部计划任务/其他设备未核验。查看或停止Codex任务应在应用界面操作；已知自身构建用对应终端Ctrl+C，不杀不明进程。
成果**仅本地已提交，未推送**。同机可直接读取本工作树；异机必须取得 output/handoff/毕设审阅与交接包-20260921.zip 和基线仓库。ZIP和增量bundle的实际SHA256清单见output/handoff，详情见DELIVERY。不存在自动远端同步保证。
