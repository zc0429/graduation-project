// Capture real report regions; keep full-page originals as independent evidence.
import {chromium} from '../../../web/node_modules/@playwright/test/index.mjs';
import {readFileSync,writeFileSync,copyFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
const dir='.local/thesis-screenshots-20261117',out='docs/validation/thesis-screenshots-20261117';
const records=JSON.parse(readFileSync(`${out}/capture-records.json`));
const browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true});
const page=await browser.newPage({viewport:{width:1280,height:1800},deviceScaleFactor:2,reducedMotion:'reduce'});
async function login(file){let a=JSON.parse(readFileSync(`${dir}/${file}`));await page.goto('http://127.0.0.1:4175/login');await page.getByLabel('用户名').fill(a.username);await page.getByLabel('密码',{exact:true}).fill(a.password);await page.getByRole('button',{name:'进入知错工作台'}).click();await page.waitForURL('http://127.0.0.1:4175/');}
try{
 await login('account.json');
 for(const [route,name] of [['/question/list','questions'],['/review','reviews']]){await page.goto(`http://127.0.0.1:4175${route}`);await page.waitForTimeout(900);await page.screenshot({path:`${out}/runtime-proofs/${name}.png`,animations:'disabled'});}
 await page.goto('http://127.0.0.1:4175/report');await page.locator('.chart-canvas canvas').first().waitFor();await page.waitForTimeout(900);
 copyFileSync(`${dir}/7-7.png`,`${out}/runtime-proofs/student-report-full.png`);
 const regions=[];
 for(const selector of ['.stats-grid','.trend-grid']){let loc=page.locator(selector);const buffer=await loc.screenshot({animations:'disabled'});const box=await loc.boundingBox();regions.push({selector,box,buffer,text:await loc.innerText()});}
 // Stack original region captures at identical native scale with a 16px gap.
 const sheet=await browser.newPage({viewport:{width:Math.ceil(regions[0].box.width),height:1000},deviceScaleFactor:2});
 await sheet.setContent(`<html><body style="margin:0;background:#f7f2e9"><main style="display:grid;gap:16px">${regions.map(r=>`<img style="display:block;width:${r.box.width}px" src="data:image/png;base64,${r.buffer.toString('base64')}">`).join('')}</main></body></html>`);
 await sheet.locator('img').evaluateAll(nodes=>Promise.all(nodes.map(n=>n.decode())));
 await sheet.locator('main').screenshot({path:`${dir}/7-7.png`,animations:'disabled'});await sheet.close();
 let record=records.entries.find(e=>e.number==='7.7');Object.assign(record,{captured_at:new Date().toISOString(),selector:null,box:{x:0,y:0,width:regions[0].box.width,height:regions.reduce((sum,r)=>sum+r.box.height,16)},scope:'Two actual current student-report regions: statistics and both weekly charts, stacked at unchanged pixel scale; full page retained separately',capture_regions:regions.map(({selector,box,text})=>({selector,box,text})),composition:'Original region PNGs at native scale, 16 CSS px gap; no UI data/text changes',text:regions.map(r=>r.text).join('\n'),sha256:createHash('sha256').update(readFileSync(`${dir}/7-7.png`)).digest('hex')});
 await page.evaluate(()=>localStorage.clear());await login('teacher.json');await page.goto('http://127.0.0.1:4175/report');await page.getByText('教师数据范围',{exact:true}).waitFor();await page.waitForTimeout(900);
 copyFileSync(`${dir}/7-8.png`,`${out}/runtime-proofs/teacher-report-full.png`);
 const start=await page.locator('.report-page').boundingBox(),stats=await page.locator('.stats-grid').boundingBox();
 const clip={x:start.x,y:start.y,width:start.width,height:stats.y+stats.height-start.y};
 await page.screenshot({path:`${dir}/7-8.png`,clip,animations:'disabled'});
 record=records.entries.find(e=>e.number==='7.8');Object.assign(record,{captured_at:new Date().toISOString(),selector:'.report-page: top through .stats-grid bottom',box:clip,text:record.text.split('掌握地图')[0].trim(),scope:'Continuous crop of named teacher report: complete page heading, teacher system-wide scope and actual aggregate statistics',sha256:createHash('sha256').update(readFileSync(`${dir}/7-8.png`)).digest('hex')});
 writeFileSync(`${out}/capture-records.json`,JSON.stringify(records,null,2)+'\n');
 console.log('Student report: original statistics + charts; teacher report: continuous scope/metrics crop');
}finally{await browser.close();}
