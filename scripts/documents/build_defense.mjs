import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {Presentation,PresentationFile} from '@oai/artifact-tool';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const skill='C:/Users/can/.codex/plugins/cache/openai-primary-runtime/presentations/26.909.12148/skills/presentations';
const runtime='C:/Users/can/.cache/codex-runtimes/codex-primary-runtime/dependencies';
const build=path.join(root,'tmp/defense-build',new Date().toISOString().replace(/[:.]/g,'-'));
const out=path.resolve(root,process.env.DEFENSE_OUTPUT || 'output/pptx/答辩审阅版.pptx');
await fs.mkdir(build,{recursive:true});await fs.mkdir(path.dirname(out),{recursive:true});
const {finalizePresentation,applyPresentationChartFont}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
const p=Presentation.create({slideSize:{width:1280,height:720}});
const family='Microsoft YaHei';
const navy='#16334A',ink='#243B4A',muted='#526675',teal='#117A7C';
const notes=[];
function text(s,value,x,y,w,h,size=28,color=ink,bold=false){
 const t=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 t.text=value;t.text.style={typeface:family,fontSize:size,color,bold,autoFit:'none'};return t;
}
function slide(title,note,source){
 const s=p.slides.add();s.background.fill='#FFFFFF';
 text(s,title,64,42,1150,80,44,navy,true);
 text(s,'赵灿   本科毕业设计',64,674,700,26,18,muted);
 text(s,String(p.slides.items.length).padStart(2,'0'),1160,674,56,26,18,muted);
 s.speakerNotes.textFrame.setText(note+'\n\n来源：'+source);
 notes.push({title,note,source});return s;
}
async function picture(s,id,x=664,y=145,w=540,h=490){
 s.images.add({blob:await fs.readFile(path.join(root,`docs/thesis/figures/png/${id}.png`)),contentType:'image/png',alt:`论文图${id.replace('-','.')}`,fit:'contain',position:{left:x,top:y,width:w,height:h}});
}
function table(s,values,widths=[310,770],y=170,height=390){
 const t=s.tables.add({rows:values.length,columns:values[0].length,left:72,top:y,width:1136,height,columnWidths:widths,values});
 t.borders.assign({style:'solid',fill:'#CCD7DD',width:1});
 for(let r=0;r<values.length;r++)for(let c=0;c<values[r].length;c++){
  const cell=t.getCell(r,c);cell.fill=r===0?navy:'#FFFFFF';
  cell.text.style={typeface:family,fontSize:26,color:r===0?'#FFFFFF':ink,bold:r===0,autoFit:'none'};
 }
 return t;
}
{
 const s=slide('本科毕业设计答辩',
 '各位老师好，我是赵灿。我的课题是基于智谱GLM模型的AI错题分析与学习推荐系统设计与实现。系统面向个人错题学习，把题目录入、解析、练习和复习放在同一个业务流程中。下面介绍研究依据、系统实现和测试结果。',
 'docs/thesis/毕业论文.md；项目已确认题目与作者信息。');
 text(s,'基于智谱GLM模型的\nAI错题分析与学习推荐系统\n设计与实现',72,200,1140,250,56,navy,true);
 text(s,'赵灿   软件工程\n指导教师：胡韬',76,525,900,90,28,muted);
}
{
 const s=slide('问题与研究目标',
 '个人错题往往分散在不同材料里，即使获得题目解析，后续练习和复习也容易断开。本课题围绕这个问题设计一个可运行系统：首先保存错题及答案，再组织知识点和错因解释，最后提供相关练习与复习记录。目标是完成可追溯的学习流程，测试结果不用于声称已经提高学习成绩。',
 'docs/thesis/毕业论文.md 第1、3章。');
 text(s,'个人错题的解析与复习容易脱节',72,174,1080,65,36,teal,true);
 text(s,'保存题干、答案与题目来源\n结合个人题库生成知识点和错因解释\n衔接相关练习、复习计划与学情报告',72,286,1110,215,32);
 text(s,'研究目标：实现可运行、可追溯的错题学习流程',72,571,1100,58,30,navy,true);
}
{
 const s=slide('文献启示与技术选择',
 '文献综述以开题报告中的二十篇文献为核心，国内十四篇、国外六篇。教育大模型研究提示需要检查内容准确性和适用边界，RAG研究提供了结合外部材料的方法，知识追踪研究强调学习过程的数据记录。考虑本项目的数据条件，我选择个人题库检索和规则化状态记录，没有训练BKT或DKT模型，也没有实现多智能体教学。',
 'docs/thesis/毕业论文.md 第2章；docs/notes/thesis-run-20260920/REFERENCE-MAP.md。');
 table(s,[['研究启示','本系统采用的路线'],['教育大模型与可靠性','结构化输出校验，失败留痕，人工核查'],['检索增强生成','检索同一用户、同一科目的历史错题'],['知识追踪与间隔复习','题目级规则分值与固定复习节点']],[340,796]);
 text(s,'BKT、DKT与多智能体属于相关研究，本项目未训练或实现',72,596,1120,45,25,muted);
}
{
 const s=slide('错题学习业务闭环',
 '录入错题时，后端在同一事务中保存题目并创建五个复习节点。保存成功后，前端另行发起异步AI解析。学生查看解析、相似题和变式题后，可以记录练习结果。提交练习更新题目级掌握度，完成复习则更新复习状态，这两个动作相互独立。学情报告在用户访问时聚合已有记录。',
 'docs/thesis/毕业论文.md 第3.4、5.6章；图3.2；ReviewPlanServiceImpl、PracticeServiceImpl。');
 const steps=[['01  保存错题','同一事务建立五个复习节点'],['02  异步解析','前端另行触发，查看知识点与错因'],['03  练习与复习','分别记录作答反馈和复习完成状态'],['04  学情报告','访问时聚合题量、掌握度与练习记录']];
 steps.forEach(([a,b],i)=>{text(s,a,72,180+i*112,365,58,34,teal,true);text(s,b,455,182+i*112,760,66,30);});
}
{
 const s=slide('系统架构与数据规模',
 '系统采用前后端分离架构，前端使用Vue，后端使用Spring Boot，业务数据保存在MySQL。模型网关连接智谱聊天模型和向量模型。真实数据库包含十张物理表、八十个字段；控制器包含三十六个方法和路径映射，其中三个公开、三十三个鉴权。教师看到的是系统级聚合结果，不提供班级或学生钻取。',
 'docs/thesis/毕业论文.md 第4、5章；图4.1；current-baseline.json。');
 table(s,[['层次','技术与职责'],['浏览器','Vue 3，页面交互与请求'],['业务后端','Spring Boot 3.x，鉴权与业务服务'],['持久化','MyBatis-Plus、MySQL 8'],['模型网关','智谱GLM解析与1024维向量']],[290,846],160,408);
 text(s,'10表 / 80字段     36接口：3公开、33鉴权',72,604,1150,48,30,teal,true);
}
{
 const s=slide('数据隔离与输入一致性',
 '数据隔离由服务端执行，学生访问错题时受所属用户约束，检索候选也受用户与科目限制。停用账号的旧令牌失效，角色以数据库状态为准。另一项问题是异步解析期间题目可能被编辑，因此回写会核对输入快照，避免旧任务覆盖新题干。这里展示的是实现与测试覆盖的机制，不把它等同于全面安全认证。',
 'docs/thesis/毕业论文.md 第6.2.1、6.2.2、6.4章；docs/notes/进度记录.md，2026-08-28最终交付审计。');
 table(s,[['约束位置','实际行为'],['学生业务数据','服务端核对所属用户及角色'],['RAG检索候选','限制同用户、同科目，并排除源题'],['停用与角色变更','旧JWT请求仍须检查当前账号状态'],['异步模型回写','题目输入快照改变时，拒绝旧结果']],[315,821],170,430);
}
{
 const s=slide('GLM解析与RAG检索',
 '正式验证使用glm-4.7-flash和embedding-3，向量维度为一千零二十四。系统在个人题库范围内计算余弦相似度，最多取三条参考材料组织提示词，随后校验结构化结果。RAG参考材料与相似题列表是不同用途，检索命中也不能保证解释更正确。真实调用曾出现失败，因此实现了有限重试、超时和失败状态记录。',
 'docs/thesis/毕业论文.md 第6.2.3章；图6.3；docs/validation/live-glm-validation.md。');
 text(s,'glm-4.7-flash + embedding-3\n1024维向量，余弦相似度\n最多3条历史题作为解析参考',72,156,1130,164,32);
 await picture(s,'6-3',72,339,700,289);
 text(s,'输出结构校验\n有限重试与超时\n失败状态留痕',824,394,385,170,30,teal,true);
}
{
 const s=slide('推荐、掌握度与复习的边界',
 '这里需要区分三个机制。相似题推荐最多返回五题，优先同知识点，再由语义检索补充。变式题每次生成严格三道，历史累计数量可以更多。掌握度是题目级规则分值，练习自评正确加十五、错误减二十，并限制在零到一百。当前推荐不读取该分值，复习使用固定的一、二、四、七、十五天节点。',
 'docs/thesis/毕业论文.md 第5.3、5.6、6.2.4、6.2.5章；RecommendServiceImpl、PracticeServiceImpl。');
 table(s,[['功能','实现规则'],['相似题推荐','最多5题，同知识点优先，语义检索补充'],['变式题','每次严格3道，历史可累计'],['mastery','自评后+15 / -20，限制在0—100'],['复习计划','固定1、2、4、7、15天节点']],[300,836],158,436);
 text(s,'推荐不读取mastery；该分值不表示知识掌握概率',72,614,1140,40,25,muted);
}
{
 const s=slide('真实GLM解析的历史界面',
 '这张图来自八月二十六日的真实GLM浏览器验证，展示知识点、错因和解释结果。该轮还检查了向量、参考题、三道变式题以及练习后的数据回读。它证明当时的业务调用链完成，不能替代本次现场启动。演示时会明确区分本地Mock流程与历史真实模型证据，现场不临时启用未经授权的付费调用。',
 'docs/thesis/figures/png/6-2.png；docs/validation/real-ai-e2e.md，2026-08-26。');
 text(s,'历史真实模型证据\n2026-08-26',72,205,540,120,36,teal,true);
 text(s,'结构化错因与知识点\n参考题及变式题可追溯\n练习后数据库回读',72,369,540,190,30);
 await picture(s,'6-2',630,138,575,512);
}
{
 const s=slide('系统测试证据',
 '系统测试有不同批次和不同对象，需要分别解释。九月七日的后端默认测试为七十三项，六十九项通过、四项跳过。已有前端单元测试二十三项、Mock浏览器测试四十四项，以及隔离数据库联调四项通过。这些是历史记录，本轮只核对证据，没有重跑业务测试。它们也不代表已经完成真人体验或并发性能评估。',
 'docs/notes/thesis-run-20260920/TEST-EVIDENCE-INDEX.md；表6.1。');
 table(s,[['测试范围','已有记录'],['后端默认测试','69通过，4跳过，共73项'],['前端单元测试','23 / 23通过'],['Mock浏览器流程','44 / 44通过'],['隔离数据库联调','4 / 4通过']],[410,726],163,430);
 text(s,'历史批次分别统计；真人体验、并发性能仍待验证',72,614,1135,40,25,muted);
}
{
 const s=slide('小样本结果与解释边界',
 '人工错因评价使用二十七道固定合成题，按零到二分评分，总分四十六分，满分五十四分。二分二十题、一分六题、零分一题，这个总分占比不能称为准确率。六组RAG盲评解盲后，开启RAG获偏好两组，关闭获偏好四组。这组结果不支持RAG具有一致优势，样本量和题目来源也不足以推断长期学习效果。',
 'docs/experiments/gate5/manual/error-cause-review.csv、rag-ab-review.csv；docs/notes/thesis-run-20260920/EXPERIMENT-RECALC.md。');
 text(s,'27题人工错因评分',72,157,570,50,30,navy,true);
 text(s,'46 / 54',72,232,535,96,68,teal,true);
 text(s,'2分：20题\n1分：6题\n0分：1题',72,362,520,160,30);
 text(s,'6组RAG盲评偏好',650,155,560,52,30,navy,true);
 const c=s.charts.add('bar',{position:{left:620,top:228,width:580,height:329},categories:['RAG ON','RAG OFF'],series:[{name:'获偏好组数',values:[2,4],fill:teal}],barOptions:{direction:'column',grouping:'clustered'},hasLegend:false,xAxis:{textStyle:{fontSize:26,fill:navy}},dataLabels:{showValue:true,position:'outEnd',textStyle:{fontSize:28,fill:navy,bold:true}}});
 applyPresentationChartFont(c,{fontFamily:family});
 text(s,'固定合成小样本；不支持一致优势或长期教学效果结论',72,610,1150,48,25,muted);
}
{
 const s=slide('完成内容与后续验证',
 '本课题完成了错题管理、智谱模型接入、个人题库检索以及练习、复习和学情报告的业务闭环，并形成了可复核的实现与测试材料。后续首先需要组织真实用户体验，检验操作流程和解释的可理解性，再在更丰富的题目与评价条件下研究检索质量。现场演示将按录入、解析展示、练习记录和学情报告的顺序进行。谢谢各位老师。',
 'docs/thesis/毕业论文.md 第7章；docs/validation/user-experience-test-plan.md。');
 text(s,'已完成',72,175,1090,48,32,teal,true);
 text(s,'错题管理、GLM解析和个人题库检索\n练习记录、固定复习计划与学情报告',72,243,1100,120,32);
 text(s,'后续验证',72,416,1090,48,32,teal,true);
 text(s,'真实用户体验与更丰富的题目评价\n现场环境启动及演示流程复核',72,486,1100,117,32);
}
const candidate=path.join(build,'candidate.pptx');
await (await PresentationFile.exportPptx(p)).save(candidate);
const result=await finalizePresentation({workspaceDir:root,candidatePath:candidate,finalPath:out,
 pythonExecutable:path.join(runtime,'python/python.exe'),
 integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
 layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit',...[3,5,6,8,10].flatMap(x=>['--require-native-table-slide',String(x)])],
 explicitTotalSlideCount:12,requiredNativeTableOwnerSlides:[3,5,6,8,10],requiredNativeChartOwnerSlides:[11],
 materializeLiteralChartWorkbooks:true,fontPolicy:{basis:'design',families:[family]},verifyArtifactToolImport:true,
 receiptPath:path.join(build,'validation.json')});
console.log(JSON.stringify(result));
await fs.writeFile(path.join(root,'docs/notes/thesis-run-20260920/defense-notes.json'),JSON.stringify(notes,null,2));
console.log(out);
