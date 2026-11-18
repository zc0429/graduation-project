// Actual browser, current branch, same real backend/DB; no browser response mocks.
import {chromium} from '../../../web/node_modules/@playwright/test/index.mjs';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {createHash} from 'node:crypto';
const dir='.local/thesis-screenshots-20261117';
const out='docs/validation/thesis-screenshots-20261117';
const history=JSON.parse(readFileSync(`${out}/business-history.json`));
const qid=history.main_question_id;
const account=JSON.parse(readFileSync(`${dir}/account.json`));
const teacher=JSON.parse(readFileSync(`${dir}/teacher.json`));
const browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true});
const context=await browser.newContext({viewport:{width:1280,height:1800},deviceScaleFactor:2,reducedMotion:'reduce'});
const page=await context.newPage();const entries=[];const errors=[];
page.on('pageerror',e=>errors.push(e.message));
async function login(a){
 await page.goto('http://127.0.0.1:4175/login');await page.getByLabel('用户名').fill(a.username);await page.getByLabel('密码',{exact:true}).fill(a.password);await page.getByRole('button',{name:'进入知错工作台'}).click();await page.waitForURL('http://127.0.0.1:4175/');
}
async function stable(){await page.evaluate(()=>document.fonts.ready);await page.waitForTimeout(700);}
async function capture(number,selector,scope,identity='赵灿'){
 await stable();const loc=page.locator(selector);await loc.scrollIntoViewIfNeeded();
 const text=await loc.innerText();const banned=text.match(/测试用户|用户001|题目1|测试数据|demo|Mock|示例/ig)||[];if(banned.length)throw new Error(`${number}: ${banned}`);
 const box=await loc.boundingBox();const path=`${dir}/7-${number}.png`;
 await loc.screenshot({path,animations:'disabled'});
 entries.push({number:`7.${number}`,candidate_path:path,captured_at:new Date().toISOString(),system_branch:history.system_branch,system_commit:history.system_commit,deviceScaleFactor:2,viewport:page.viewportSize(),selector,box,account:{nickname:identity,role:number===8?'teacher':'student'},question_id:number<=6?qid:null,scope,sha256:createHash('sha256').update(readFileSync(path)).digest('hex'),banned_terms_found:banned,text});
 console.log(`Captured 7.${number}: ${Math.round(box.width)} x ${Math.round(box.height)} CSS px`);
}
try{
 await login(account);
 await page.goto(`http://127.0.0.1:4175/question/${qid}`);await page.getByRole('tab',{name:'学习与练习'}).click();
 await page.getByRole('button',{name:'获取知识内容',exact:true}).click();await page.getByText('已复用保存的知识内容',{exact:true}).waitFor();
 await page.getByRole('button',{name:'开始练习',exact:true}).click();await page.getByText('复用本人已有未练题',{exact:true}).waitFor();
 await page.getByLabel('本题作答',{exact:true}).fill('配方时仍把常数项直接保留，写成顶点 (-2,3)，需要再核对补入与减去的常数。');
 await page.locator('.learning-resources').getByText('仍然答错',{exact:true}).click();
 await page.getByRole('button',{name:'保存本次练习',exact:true}).click();await page.getByRole('button',{name:'重新练习本题',exact:true}).waitFor();
 await capture(3,'.resource-panel:nth-of-type(2)','Existing archived variant obtained through next endpoint, actual incorrect self-assessment submitted, completed/retry state');
 await capture(2,'.resource-panel:nth-of-type(1)','Verbatim archived GLM analysis loaded through knowledge cache; actual reused=true response');
 await page.getByRole('tab',{name:'AI 智能解析',exact:true}).click();await capture(4,'.analysis-workbench','Archived GLM analysis completed through actual async analysis service; model, knowledge classification and full text');
 await page.getByRole('tab',{name:'RAG 参考',exact:true}).click();await capture(5,'.analysis-workbench','Actual same-account reference IDs from current backend over the local replay index');
 await page.getByRole('tab',{name:/AI 变式题/}).click();await capture(6,'.analysis-workbench','Three archived real-GLM variant stems with current practice actions; missing original answers remain NULL');
 await page.goto('http://127.0.0.1:4175/question/create');await page.locator('.el-select').first().click();await page.getByRole('option',{name:'数学',exact:true}).click();
 const main=history.questions.find(q=>q.question_id===qid).input;
 await page.getByRole('textbox',{name:'题干',exact:true}).fill(main.stem);
 await page.getByPlaceholder('如：期中试卷 · 第 18 题').fill('数学期中复习卷 · 第 18 题');
 await page.getByPlaceholder('记录正确答案、关键步骤或自己的订正').fill(main.answer);
 await page.getByRole('heading',{name:'录入一道值得重做的题'}).click();await capture(1,'.question-create-page','Manual form filled with archived source question; editor and image-assistance entry visible; no extra duplicate saved');
 await page.goto('http://127.0.0.1:4175/report');await page.getByText('错题累计',{exact:true}).waitFor();await page.locator('.chart-canvas canvas').first().waitFor();await capture(7,'.report-page','Student weekly question, review, knowledge mastery and actual practice-count charts');
 // Additional visual evidence of the same history, outside the eight thesis figures.
 mkdirSync(`${out}/runtime-proofs`,{recursive:true});
 for(const [route,name] of [['/','home'],['/question/list','questions'],['/review','reviews'],['/practice/history','practices'],['/message','messages']]){
  await page.goto(`http://127.0.0.1:4175${route}`);await stable();
  await page.screenshot({path:`${out}/runtime-proofs/${name}.png`,animations:'disabled'});
 }
 await context.clearCookies();await page.evaluate(()=>localStorage.clear());await login(teacher);
 await page.goto('http://127.0.0.1:4175/report');await page.getByText('教师数据范围',{exact:true}).waitFor();await page.locator('.chart-canvas canvas').first().waitFor();await capture(8,'.report-page','Named teacher authenticated; actual system-wide aggregate agrees with student dataset','胡韬');
 if(errors.length)throw new Error(JSON.stringify(errors));
 writeFileSync(`${out}/capture-records.json`,JSON.stringify({entries:entries.sort((a,b)=>a.number.localeCompare(b.number)),browser_errors:errors},null,2)+'\n');
}finally{await browser.close();}
