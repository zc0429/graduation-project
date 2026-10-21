# 业务流程泳道图（导师讲解版）

依据：用户提供的导师聊天截图和两版外卖业务泳道图示例。导师要求从业务人员角度描述，使用泳道区分参与者，考虑判断情况，横向或纵向均可。本套采用纵向泳道，正文动作使用业务用语。

## 文件与用途

- `业务流程图.drawio`：包含三张图的可编辑源文件，可用 draw.io / diagrams.net 打开，节点、文字、菱形和连线均可编辑。
- `01-错题分析与巩固学习.svg` / `.png`：主流程，学生与学习平台交接；五类判断覆盖信息补正、分析重试、是否拓展练习、是否取得可用题目与自评对错。
- `02-按期复习.svg` / `.png`：从保存错题后安排复习开始，说明待复习任务、提醒、人工确认完成和后续复习。
- `03-管理与学情查看.svg` / `.png`：管理员维护基础资料、教师查看系统范围汇总两个独立辅助流程。
- `../../../output/pdf/业务流程图-导师讲解版.pdf`：三页 A3 矢量 PDF，每页一图，便于共享屏幕、缩放查看和打印。
- `业务流程图.json`：节点、位置、连接和分支的结构化源数据；`verification.json` 保存检查结果。

本套是独立讲解工件，未替换论文已有图 3.2，未改论文编号、源稿或现有 DOCX/PDF。

## 流程边界

1. 学生已登录是前提，账号注册和登录不占用学习主线。
2. 保存错题时即建立五条固定日期复习任务，与 AI 是否成功无关；复习图展开该路径，并非在主图结束后才创建计划。
3. 相关参考题限定本人同科目题库；AI 提供辅助分析，不代替学生或教师判断。主图的“是否成功”包括服务未能给出可用结果的情况，不展开网络或字段校验等实现细节。
4. 相似题按请求提供，变式题按请求生成；均不是每次学习必做步骤。无候选题或生成失败时，学生仍可选择已有原题练习，图中不预设必有题可推荐。
5. 学生对照答案自评正确或错误。原题或变式题的练习均按原题更新规则分值，正确增加15、错误减少20，范围0至100；图中的分值调整与记录保存共同构成一次提交的结果，不表示部分成功。
6. 练习提交不自动完成复习任务；学生单独确认完成。逾期未完成任务继续可见；正确与否不重排固定复习日期。
7. 学情在用户访问时汇总，不提前生成历史报告。个人报告与教师的系统范围汇总相区分；不添加班级绑定、教师批改、布置作业或教师审核 AI 等未实现流程。
8. 管理图的资料维护、账号操作、公告发布是按需管理事项，不表示三者每次必须全部完成。

## 现场讲解顺序

先讲图01：“学生把一道做错的题整理提交，信息不完整就返回修改；保存后平台已经安排好五次复习。平台参考本人相关题提供辅助分析，失败可重试，也可以继续学习。学生按需要选择原题或拓展练习，对照答案自评后提交，平台记录练习并更新掌握度，学生可以查看学习情况。”

再讲图02：“复习不以分析成功为前提。到期或逾期任务会出现在列表，当天到期任务另有站内提醒。学生复习后单独确认完成；没有确认就保留未完成。还有任务可以继续处理，否则结束本次复习，之后按原计划继续。”

最后讲图03：“管理员维护科目、知识点、账号和公告，提供基础业务支持。教师按需查看系统汇总学情。这两类业务独立于每一次学生学习，不要求教师参与逐题审核。”

## 实现核对来源

- `server/src/main/java/com/example/wrongbook/service/impl/QuestionServiceImpl.java`：保存错题时建立复习计划。
- `web/src/views/question/QuestionCreateView.vue`、`QuestionDetailView.vue`：保存后独立触发分析与状态反馈，按需获取练习资源。
- `server/src/main/java/com/example/wrongbook/service/impl/AiAnalysisServiceImpl.java`、`RagServiceImpl.java`：个人题库参考与分析成功/失败处理。
- `server/src/main/java/com/example/wrongbook/service/impl/RecommendServiceImpl.java`、`VariantServiceImpl.java`：按需相似题与变式题。
- `server/src/main/java/com/example/wrongbook/service/impl/PracticeServiceImpl.java`：学生提交自评结果与原题掌握度规则。
- `server/src/main/java/com/example/wrongbook/service/impl/ReviewPlanServiceImpl.java`、`service/ScheduleTask.java`、`web/src/views/review/ReviewPlanView.vue`：固定复习、到期提醒、逾期任务、单独确认完成。
- `server/src/main/java/com/example/wrongbook/service/impl/ReportServiceImpl.java` 与管理控制器：按访问汇总、教师权限和基础管理边界。

生成：在仓库根目录运行 `python -X utf8 scripts/documents/build_business_swimlanes.py`。重建后的视觉验收状态恢复为待检查，须重新查看全部三页再标记通过。
