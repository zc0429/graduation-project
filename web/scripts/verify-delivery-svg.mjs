import { chromium } from 'playwright'
import { readFileSync, mkdirSync, writeFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
const root=fileURLToPath(new URL('../../', import.meta.url)).replace(/\/$/, '');const out=root+'/docs/validation/learning-delivery-20261112/svg-rendered';mkdirSync(out,{recursive:true})
const browser=await chromium.launch({executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || undefined,headless:true,args:['--no-sandbox']});const page=await browser.newPage({viewport:{width:850,height:1200}})
const result=[]
for(const key of ['3-5','3-6','3-7','3-8','3-9','5-1','6-5','6-9']){
 await page.setContent(readFileSync(`${root}/docs/thesis/delivery-20261112/figures/${key}.svg`,'utf8'));await page.evaluate(()=>document.fonts.ready)
 const info=await page.evaluate(()=>({fonts:[...document.fonts].map(f=>({family:f.family,status:f.status})),textCount:document.querySelectorAll('text').length}))
 await page.locator('svg').screenshot({path:`${out}/${key}.png`});result.push({figure:key,...info})
}
writeFileSync(root+'/docs/validation/learning-delivery-20261112/svg-render.json',JSON.stringify(result,null,2));await browser.close()
