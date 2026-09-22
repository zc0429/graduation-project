"""Persist P01-P05 evidence without changing source evidence or application code."""
from pathlib import Path
import json,hashlib,re
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'docs/notes/thesis-run-20260920'
def put(n,s):(OUT/n).write_text(s.strip()+'\n',encoding='utf-8')
def main():
    if (OUT/'opening-reference-check.json').exists():
        raise SystemExit('Historical snapshot generator: do not overwrite the 2026-09-22 opening-reference alignment.')
    coverage=(ROOT/'docs/notes/开题研究内容与论文章节对应核对.md').read_text(encoding='utf-8').split('## 本轮处理')[0]
    put('OPENING-TO-THESIS.md','# 2026-09-20 开题与论文覆盖复核\n\n以当前完整七章逐项复核，下表沿用2026-09-16映射，17个检查项仍有对应内容。第二章本轮按国内14篇、国外6篇核心逐篇对齐。学校系统完成来自用户反馈，线上最终稿没有导出件，未直接核对。\n\n'+coverage)
    put('REQUIRED-INPUTS.md','''# 作者与外部条件

1. 学校线上最终稿：如与仓库开题不一致，需导出件核对。现有任务按仓库对应稿完成，不要求再次提交学校系统。
2. 正式封面与完成日期：姓名、学号、学院、班级、导师已有；最终系统封面和完成日期未提供，不编造日期。
3. 致谢：原稿预留，已询问作者实际帮助事实。未收到事实时保留空白致谢页。
4. 文献近三年的计年基点：当前2024—2026有16篇，若学校按2027毕业年计算2025—2027，仅6篇。需导师明确最终口径后处理。
5. 真人体验、Visio实开及现场演示需相应人员或环境。本轮不伪造体验分数，不调用付费模型。

这些事项不阻塞本地审阅版、讲稿、可编辑答辩材料和交接。
''')
    put('THESIS-CONSISTENCY.md','''# 全文实现一致性

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
''')
    b=json.loads((OUT/'current-baseline.json').read_text(encoding='utf-8'))
    put('FIGURE-TABLE-AUDIT.md','''# 图表复核

2026-09-20 实际调用现有 audit_thesis_figures.baseline()/verify()，将结果写本轮目录，未覆写2026-09-16旧工件。

17图16表编号连续、图题匹配、所有PNG/SVG/单图PDF存在、SVG无foreignObject、证据路径有效；原始截图SHA-256全部保持不变。10张结构表字段、类型、约束与Schema一致；36接口与权限表一致。结果见 current-figure-check.json。

图源JSON、manifest、fact-baseline、verification及README已读取。数据库无物理外键；知识点parent_id=0是根哨兵；practice_record的两个可空目标由服务端强制二选一；变式次数与每次数量有区分。图3.1保留角色与权限命名。未发现需重画的明确差异，未重建图源。

既有34页校样只作历史校样；本轮最终视觉检查随全文P06进行。Visio未注册/未实开，不生成虚假VSDX。截图仅作2026-08-26真实链路证据，后续图片识别功能不能借用这些截图证明。
''')
    put('EXPERIMENT-RECALC.md',f'''# 原始实验复算

2026-09-20，从 docs/experiments/gate5/manual/error-cause-review.csv 与 rag-ab-review.csv 使用csv.DictReader、utf-8-sig、newline空字符串解析；解盲依据results/rag-ab-key.json。

实际结果：27题，46/54，均分46/27={46/27:.10f}；2分20题，1分6题，0分1题。总分占比不是准确率。6组偏好解盲RAG_ON=2、RAG_OFF=4，无平局，不进行显著性或长期效果推断。

原始自动JSON generatedAt=2026-08-27，人工表属于2026-09-07批次。JSON中的27题、26题知识点命中及检索数据与论文记录一致；本轮未重新请求模型。旧summary人工待评保留为历史。

RAG两组自动覆盖均88.89%，人工偏好不支持一致优势。结构合规、概念覆盖、人工判断属于不同指标，不互相替代。34次失败尝试不代表34道独立错题。现有样本为合成错题，不是学习成绩实验。

本轮复算数据见current-baseline.json的gate5_manual。没有修改原始CSV、JSON、模型输出、解盲键。
''')
    put('TEST-EVIDENCE-INDEX.md','''# 历史测试证据索引

本轮只读核对记录与原始数据，未重跑下列业务测试。

|日期|证据文件（仓库根目录相对）|结果与范围|
|---|---|---|
|2026-09-07|docs/validation/deploy-test-validation.md|后端73项，69通过4跳过；非公网本机部署|
|2026-09-07|docs/validation/user-experience-test-plan.md|前端23/23、typecheck/build；浏览器44/44；真人体验尚未实施|
|2026-09-07|docs/validation/isolated-functional-validation.md|隔离数据库Mock联调4/4|
|2026-08-25|docs/validation/live-glm-validation.md|最终轮结构化分析5/5、变式3/3；保留历史失败|
|2026-08-26|docs/validation/embedding-rebuild.md|3/3历史向量重建1024维|
|2026-08-26|docs/validation/real-ai-e2e.md|真实浏览器业务链，参考题、变式、练习|
|专项记录所载日期|docs/validation/image-question-recognition.md|8张合成图，首轮7/8，失败即时重试成功|

各批次不得相加成一个通过率。并发性能、长期学习效果、公网部署与真人体验没有完成证据。
''')
    put('artifact.md','''# 正文模板执行契约

参考：docs/materials/27届毕业设计学校通知和模板/附件3：毕业论文（设计）相关模板（2027）/附件4：毕业论文（设计）正文模板.docx。
SHA256 79da5538204e7d6a9dcf9f3d4a4db297c9dc69fbbe807f493dca4ae6ed1c6c8e。
LibreOffice经技能render_docx渲染19页，已查看全部19页。模板有重复空白页、示例文字、批注和公式；这些属于替换区域。结构证据见TEMPLATE-STRUCTURE.json，全文规范见SCHOOL-REQUIREMENTS-TEXT.txt。

四节：题目页、目录、摘要中英文、正文。A4；左2.75cm其余2.5cm；原模板页眉1.5cm页脚1.75cm，按学校原文及项目明确要求校准页脚1.5cm。封面无页眉页码，目录起保持原学校LOGO页眉；目录无页码，摘要I/II，正文从1起。模板偶发多余空白不继承。

替换槽：word/document.xml 直接body下p[1..8]保留logo及题目页组件，更换中英文题目；题目后补已有学生信息，日期留白。余下示例正文全部由现有作者Markdown各章节替换。内容顺序为题目、目录、中英文摘要、七章正文、24篇文献、致谢。附录无实际内容不插入示例附录。

正文宋体12pt、英文数字Times New Roman12pt，固定20pt行距、两端对齐、首行24pt。标题使用原Heading样式并按理工章节编号；一级16pt黑体居中、段前24pt后18pt，二级14pt黑体、三级12pt黑体，标题与下段同页。规范内部标题字号存在不同条款，采用其“章节标识”明确条款及模板样式层级。页码TNR10.5pt居中。

图题在下、表题在上，宋体10.5pt；原17幅PNG保持比例，157.5mm宽；三线表上/下1.5pt、表头下1pt，无竖线、无底色。表格10.5pt宋体，英文数字TNR，单倍行距、段前后3pt，行不跨页、续页重复表头。长接口表分块加续表标题。代码文本10.5pt、明确保留换行。

题注SEQ域、正文REF域及文献书签超链接可编辑。目录TOC域与PAGEREF缓存，Word不可用则updateFields=true并明确Word全选F9仍需作者执行。不以LibreOffice回存DOCX刷新字段，PDF渲染可使用其只读转换。

保留原package所有未改部分字节：header及其rels、logo原始media、主题、字体表、编号、customXml。允许修改document、styles、settings、document关系及content types，并新增插图；清除示例批注/脚注文字（仅输出副本），原模板不变。图表及新正文是明确替换内容，因此页数不要求等于模板。

保真验收：原件hash不变，四节及几何对应、校徽页眉部件字节一致、无示例会计内容/批注、17图16表、24个参考文献目标、目录/页码/图题/交叉引用、全文逐页视觉检查。致谢事实缺失时标题后留白并在独立说明列出，不能复制模板个人经历。
''')
    put('STATE.md','''# 本轮状态
计划 THESIS-20260920-V3；2026-09-20 Asia/Shanghai。
基线 origin/dev=3b7fc4768e4a2588583f109133d378a050da8733。
工作树 D:/Documents/GitHub/graduation-project-thesis-20260920；分支 codex/thesis-finalization-20260920。

|阶段|状态|验收依据|
|---|---|---|
|P00|done|独立worktree、实际远端SHA、保护原目录修改|
|P01|done|学校原文提取、19页模板查看、OPENING-TO-THESIS|
|P02|partial|第二章对齐及24篇身份映射完成；最终计年口径待确认|
|P03|done|THESIS-CONSISTENCY与字数统计|
|P04|done|current-figure-check；全文视觉交P06|
|P05|done|EXPERIMENT-RECALC、TEST-EVIDENCE-INDEX；无新业务实验|
|P06|in_progress|模板契约artifact.md已保存，构建全文|
|P07|pending|答辩包待生成|
|P08|pending|总交付待收口|
|P11|in_progress|稳定入口已建立，最终自检待做|

本轮尚未创建定时任务。运行所有者为当前Codex；不并行修改。
''')
    put('CHANGELOG.md','''# 改动记录

2026-09-20 P00：fetch核实远端、建立独立文档分支。原目录进度与粘贴稿保持不变。
P01：读取学校原规范和模板，渲染查看19页，保存结构与哈希。
P02：第二章改为国内先于国外，20篇核心逐篇评述，原4篇另作补充；正文独立首引重排，开题和主库不变。
P03—P05：只读事实核对、17图16表完整性、人工CSV复算通过，未重跑业务测试。
''')
if __name__=='__main__': main()
