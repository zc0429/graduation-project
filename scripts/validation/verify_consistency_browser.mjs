// Supplemental real UI flows. Uses actual Spring Boot/MySQL, explicit Mock AI.
import { createRequire } from 'node:module'
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { resolve } from 'node:path'
const root = fileURLToPath(new URL('../../', import.meta.url))
const require = createRequire(new URL('../../web/package.json', import.meta.url))
const { chromium, expect } = require('@playwright/test')
const run = resolve(root, 'docs/validation/thesis-system-consistency-20261113')
const base = process.env.AUDIT_WEB || 'http://127.0.0.1:4175'
const fixture = JSON.parse(readFileSync(resolve(root, '.local/browser-fixture.json'), 'utf8'))
const browser = await chromium.launch({ executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || '/usr/bin/chromium', headless: true })
const rows = [], created = {}
mkdirSync(resolve(run, 'screenshots'), { recursive: true })
async function login(role) {
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } })
  const page = await context.newPage()
  await page.goto(base + '/login')
  await page.getByLabel('用户名').fill(role)
  await page.getByLabel('密码', { exact: true }).fill('123456')
  await page.getByRole('button', { name: '进入知错工作台' }).click()
  await expect(page).toHaveURL(/\/$/)
  return { context, page }
}
async function mutation(page, url, method, action) {
  const response = page.waitForResponse(r => r.url().endsWith(url) && r.request().method() === method)
  await action()
  const result = await response
  expect(result.status()).toBe(200)
  const body = await result.json(); expect(body.code).toBe(0)
  return body.data
}
try {
  const { context: adminContext, page: admin } = await login('admin')
  await admin.goto(base + '/admin/subject')
  await admin.getByRole('button', { name: '新增科目', exact: true }).click()
  let dialog = admin.getByRole('dialog', { name: '新增科目' })
  const subjectName = '审计UI科目' + fixture.suffix
  await dialog.getByLabel('科目名称').fill(subjectName)
  await dialog.getByLabel('科目编码').fill('AUDIT_UI')
  created.subjectId = await mutation(admin, '/api/subject', 'POST', () => dialog.getByRole('button', { name: '创建科目' }).click())
  const card = admin.locator('.subject-card').filter({ hasText: subjectName })
  await expect(card).toBeVisible(); await card.getByRole('button', { name: '编辑' }).click()
  dialog = admin.getByRole('dialog', { name: '编辑科目' })
  await dialog.getByLabel('科目编码').fill('AUDIT_UI_EDIT')
  await mutation(admin, `/api/subject/${created.subjectId}`, 'PUT', () => dialog.getByRole('button', { name: '保存修改' }).click())
  await expect(card).toContainText('AUDIT_UI_EDIT')
  await admin.goto(base + '/admin/knowledge')
  const chapter = '审计UI章节' + fixture.suffix, point = '审计UI考点' + fixture.suffix
  await admin.getByRole('button', { name: '新增章节', exact: true }).click()
  dialog = admin.getByRole('dialog', { name: '新增章节' })
  await dialog.getByLabel('章节名称').fill(chapter)
  created.chapterId = await mutation(admin, '/api/knowledge-point', 'POST', () => dialog.getByRole('button', { name: '保存', exact: true }).click())
  await admin.locator('.chapter-card').filter({ hasText: chapter }).getByRole('button', { name: '添加考点' }).click()
  dialog = admin.getByRole('dialog', { name: '添加考点' })
  await dialog.getByLabel('考点名称').fill(point)
  created.pointId = await mutation(admin, '/api/knowledge-point', 'POST', () => dialog.getByRole('button', { name: '保存', exact: true }).click())
  await admin.getByRole('button', { name: '删除考点 ' + point, exact: true }).click()
  await mutation(admin, `/api/knowledge-point/${created.pointId}`, 'DELETE', () => admin.getByRole('dialog', { name: '删除考点' }).getByRole('button', { name: '确认删除' }).click())
  await expect(admin.getByText(point, { exact: true })).toHaveCount(0)
  await admin.getByRole('button', { name: '删除空章节 ' + chapter, exact: true }).click()
  await mutation(admin, `/api/knowledge-point/${created.chapterId}`, 'DELETE', () => admin.getByRole('dialog', { name: '删除空章节' }).getByRole('button', { name: '确认删除' }).click())
  rows.push({ flow: 'admin real catalog create/edit/add/delete', passed: true })

  await admin.goto(base + '/announcement')
  await admin.getByRole('button', { name: '发布公告', exact: true }).click()
  dialog = admin.getByRole('dialog', { name: '发布公告' })
  const title = '审计UI公告' + fixture.suffix
  await dialog.getByLabel('公告标题').fill(title)
  await dialog.getByLabel('公告内容').fill('实际界面发布，隔离数据库回读。')
  created.announcementId = await mutation(admin, '/api/announcement', 'POST', () => dialog.getByRole('button', { name: '确认发布' }).click())
  await expect(admin.getByRole('heading', { name: title, exact: true })).toBeVisible()
  const { context: studentContext, page: student } = await login('student')
  await student.goto(base + '/announcement')
  await expect(student.getByRole('heading', { name: title, exact: true })).toBeVisible()
  rows.push({ flow: 'admin publishes and student reads actual announcement', passed: true })

  const { context: teacherContext, page: teacher } = await login('teacher')
  const reportResponse = teacher.waitForResponse(r => r.url().endsWith('/api/report/weekly'))
  await teacher.goto(base + '/report')
  expect((await reportResponse).status()).toBe(200)
  await expect(teacher.getByRole('note')).toContainText('仅展示全站聚合学习数据')
  await expect(teacher.getByRole('heading', { name: '学情报告', exact: true })).toBeVisible()
  await teacher.screenshot({ path: resolve(run, 'screenshots/teacher-report-real-backend.png'), fullPage: true })
  await student.goto(base + '/report')
  await mutation(student, '/api/report/generate', 'POST', () => student.getByRole('button', { name: '生成本周报告' }).click())
  await student.goto(base + '/message')
  const unread = student.getByRole('button', { name: '标记已读', exact: true }).first()
  await expect(unread).toBeVisible()
  const readResponse = student.waitForResponse(r => /\/api\/message\/\d+\/read$/.test(r.url()) && r.request().method() === 'PUT')
  await unread.click(); expect((await readResponse).status()).toBe(200)
  rows.push({ flow: 'teacher aggregate report and student generate/read message', passed: true })

  await student.goto(base + '/review')
  const review = student.locator('.review-item').filter({ hasText: fixture.stem })
  await expect(review).toBeVisible()
  await review.getByRole('button', { name: '去重做' }).click()
  await expect(student).toHaveURL(new RegExp(`/question/${fixture.questionId}$`))
  await student.getByRole('button', { name: '开始重做', exact: true }).click()
  dialog = student.getByRole('dialog', { name: '重做这道错题' })
  await dialog.getByText('答对了', { exact: true }).click()
  await mutation(student, '/api/practice', 'POST', () => dialog.getByRole('button', { name: '提交练习记录' }).click())
  await expect(dialog).toBeHidden()
  await student.goto(base + '/review')
  await review.getByRole('button', { name: '完成复习' }).click()
  await mutation(student, `/api/review-plan/${fixture.planId}/finish`, 'PUT', () => student.getByRole('dialog').getByRole('button', { name: '确认完成' }).click())
  await expect(review).toHaveCount(0)
  rows.push({ flow: 'due review opens original, records answer, separately confirms selected plan', passed: true })
  await Promise.all([adminContext.close(), studentContext.close(), teacherContext.close()])
} finally {
  writeFileSync(resolve(run, 'browser-supplement.json'), JSON.stringify({ model: 'explicit Mock', flows: rows, created, fixture, allFourPassed: rows.length === 4 }, null, 2) + '\n')
  await browser.close()
}
console.log(JSON.stringify({ supplementalFlowsPassed: rows.length, expected: 4 }))
