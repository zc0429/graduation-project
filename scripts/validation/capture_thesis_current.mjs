// Actual browser + backend + dedicated MySQL. Model must be explicitly Mock.
import { chromium } from '../../web/node_modules/@playwright/test/index.mjs'
import { mkdirSync, writeFileSync, readFileSync } from 'node:fs'
import { createHash } from 'node:crypto'
import { resolve } from 'node:path'
const dir = resolve('docs/thesis/align-reference1-20261113/screenshots')
mkdirSync(dir, { recursive: true })
const browser = await chromium.launch({ executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || '/usr/bin/chromium', headless: true })
const page = await browser.newPage({ viewport: { width: 1100, height: 1000 }, deviceScaleFactor: 1.5 })
const base = 'http://127.0.0.1:8080/api'
const result = await (await page.request.post(`${base}/auth/login`, { data: { username: 'student', password: '123456' } })).json()
const headers = { Authorization: `Bearer ${result.data.token}` }
const created = await (await page.request.post(`${base}/question`, { headers, data: { subjectId: 1, stem: '求函数 y=x² 在区间 [0,2] 上的值域。', answer: '[0,4]', source: '2026-11-13 论文界面验证，Mock模型，专用数据库' } })).json()
const id = created.data
if (!Number.isInteger(id)) throw new Error('Question creation failed')
const evidence = []
async function capture(name, locator, scope) {
  const path = resolve(dir, name + '.png')
  await locator.screenshot({ path, animations: 'disabled' })
  evidence.push({ file: path.split('/docs/')[1], sha256: createHash('sha256').update(readFileSync(path)).digest('hex'), captured_at: new Date().toISOString(), model: 'explicit Mock', question_id: id, scope })
}
try {
  await page.goto('http://127.0.0.1:4175/login')
  await page.getByLabel('用户名').fill('student')
  await page.getByLabel('密码', { exact: true }).fill('123456')
  await page.getByRole('button', { name: '进入知错工作台' }).click()
  await page.waitForURL('http://127.0.0.1:4175/')
  await page.goto('http://127.0.0.1:4175/question/create')
  await page.getByRole('textbox', { name: '题干', exact: true }).fill('求函数 y=x² 在区间 [0,2] 上的值域。')
  await page.getByPlaceholder('记录正确答案、关键步骤或自己的订正').fill('[0,4]')
  await page.locator('.el-select').first().click()
  await page.getByRole('option', { name: '数学', exact: true }).click()
  await capture('current-create', page.locator('.question-create-page'), 'Current editor and manual form; recognition disabled, no live model claim')
  await page.goto(`http://127.0.0.1:4175/question/${id}`)
  await page.getByRole('tab', { name: '学习与练习' }).click()
  await page.getByRole('button', { name: '获取知识内容', exact: true }).click()
  await page.getByText('知识内容已生成并保存', { exact: true }).waitFor()
  await page.getByRole('button', { name: '再次查看知识内容', exact: true }).click()
  await page.getByText('已复用保存的知识内容', { exact: true }).waitFor()
  await capture('current-knowledge', page.locator('.resource-panel').first(), 'Saved knowledge cache reused through actual UI')
  await page.getByRole('button', { name: '开始练习', exact: true }).click()
  await page.getByText('优先练习本人原题', { exact: true }).waitFor()
  await page.locator('.learning-resources').getByText('答对了', { exact: true }).click()
  await page.getByRole('button', { name: '保存本次练习', exact: true }).click()
  await page.getByRole('button', { name: '重新练习本题', exact: true }).waitFor()
  await page.getByRole('button', { name: '继续练习', exact: true }).click()
  await page.getByText('新题已生成并保存', { exact: true }).waitFor()
  await page.locator('.learning-resources').getByText('仍然答错', { exact: true }).click()
  await page.getByRole('button', { name: '保存本次练习', exact: true }).click()
  await page.getByRole('button', { name: '重新练习本题', exact: true }).waitFor()
  await capture('current-practice', page.locator('.resource-panel').nth(1), 'Original recorded, generated variant recorded as incorrect, repeat action visible')
  writeFileSync(resolve(dir, 'provenance.json'), JSON.stringify(evidence, null, 2) + '\n')
  console.log(JSON.stringify({ screenshots: evidence.length, questionId: id, model: 'Mock', status: 'captured' }))
} finally {
  await page.request.delete(`${base}/question/${id}`, { headers })
  await browser.close()
}
