# 全文实现一致性

2026-09-20；基线见 SOURCE-MANIFEST。只读源码复核，业务测试未重跑。完整七章已有，不进行首次扩写。

|正文事实|本轮读取证据|结论|
|---|---|---|
|10表80字段、逻辑关联|server/src/main/resources/db/schema.sql；current-baseline.json|与正文10个结构表逐字段一致，无FOREIGN KEY物理约束；ai_analysis.question_id唯一|
|36映射，3公开33鉴权|controller/*.java；current-baseline.json|HTTP方法与路径、角色逐项一致|
|三角色、教师系统聚合|ReportServiceImpl.weekly；controller注解|教师不按userId过滤，无班级/学生钻取|
|错题保存与5计划同事务|QuestionServiceImpl.create；ReviewPlanServiceImpl.REVIEW_DAYS|1/2/4/7/15天；AI由前端另行触发|
|RAG top3、同用户同科目排除原题|AiAnalysisServiceImpl；RagServiceImpl.retrieveSimilar|与正文一致；内存余弦，未声称万级性能|
|相似题最多5题，不读取mastery|RecommendServiceImpl.similar|同知识点、难度优先，语义补足；无概率追踪|
|每次3变式，历史可多批|VariantServiceImpl.parseVariants和写入流程|JSON数组严格3，未把历史总数限制为3|
|题目掌握度+15/-20，0—100|PracticeServiceImpl；QuestionMapper|事务内记录与有界原子更新，作答目标二选一|
|固定复习与练习分开|ReviewPlanServiceImpl；PracticeServiceImpl|完成复习不等于提交练习|
|图片识别默认关闭、确认后保存|配置与image-question-recognition.md|识别不写业务表，studentAnswer临时显示|
|三角色14视图与404|web/src/views；router/index.ts|14正常+1兜底|

摘要中英文已按模型、架构、复习节点、分值和验证范围逐项对照，四关键词一致。第6/7章已明确小样本局限、真人体验未实施及非公网边界。未发现需要修改生产代码的事实冲突。

字数见 word-count.json。统计第1—7章，剔除图片路径、链接目标、Markdown标记和文献编号，保守另报汉字数；含表格可见正文，不含文末题录、封面、目录。总汉字约1.9万，绪论1220，主体第3—6章14409，均高于项目下限。综述按汉字及去空白双口径报告。不承诺查重率。

现存预留：系统正式封面、完成日期和作者致谢。局部改动集中第二章与由此触发的全文编号，见差异文件；不会把内部审计话语添加到论文。
