import { expect, test, type Page } from '@playwright/test'
import { mkdir } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'

const screenshotDir = fileURLToPath(new URL('../../docs/thesis/screenshots/', import.meta.url))

const referenceQuestion = {
  stem: '【自动化测试数据】已知二次函数 y=x²-5x+6，求它与 x 轴的交点坐标。',
  answer: '（1，0）和（2，0）。',
  source: 'Playwright 自动化截图测试',
}

const targetQuestion = {
  stem: '【自动化测试数据】已知二次函数 y=x²-4x+3，求顶点坐标与对称轴。',
  answer: '顶点坐标为（2，-1），对称轴为 x=2。',
  source: 'Playwright 自动化截图测试',
}

interface Question {
  id: number
  stem: string
}

interface PageData<T> {
  records: T[]
  total: number
}

interface AiAnalysis {
  status: number
  referenceIds?: string
}

interface Message {
  title: string
}

async function apiData<T>(
  page: Page,
  apiPath: string,
  init: { method?: string; body?: unknown } = {},
): Promise<T> {
  return page.evaluate(
    async ({ path, method, body }) => {
      const token = localStorage.getItem('token')
      const response = await fetch(path, {
        method,
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: body === undefined ? undefined : JSON.stringify(body),
      })
      const envelope = await response.json()
      if (!response.ok || envelope.code !== 0) {
        throw new Error(envelope.message || `${method} ${path} failed with ${response.status}`)
      }
      return envelope.data
    },
    { path: apiPath, method: init.method || 'GET', body: init.body },
  )
}

async function waitForStableUi(page: Page) {
  await expect(page.locator('.el-loading-mask:visible')).toHaveCount(0, { timeout: 20_000 })
  await expect(page.locator('.el-message:visible')).toHaveCount(0, { timeout: 5_000 }).catch(() => undefined)
  await page.keyboard.press('Escape').catch(() => undefined)
  await page.waitForTimeout(300)
}

async function capture(page: Page, filename: string, scrollTop = 0) {
  await waitForStableUi(page)
  const main = page.locator('.el-main')
  if ((await main.count()) > 0) {
    await main.evaluate((element, top) => element.scrollTo(0, top), scrollTop)
  }
  await page.waitForTimeout(200)
  await page.screenshot({
    path: fileURLToPath(new URL(filename, new URL('../../docs/thesis/screenshots/', import.meta.url))),
    animations: 'disabled',
    caret: 'hide',
  })
}

async function resetSession(page: Page) {
  await page.goto('/login')
  await page.evaluate(() => localStorage.clear())
  await page.reload()
  await expect(page.getByRole('heading', { name: 'AI 错题分析与学习推荐系统' })).toBeVisible()
}

async function login(page: Page, username: 'student' | 'teacher' | 'admin', roleLabel: string) {
  await page.getByPlaceholder('用户名').fill(username)
  await page.getByPlaceholder('密码').fill('123456')
  await page.getByRole('button', { name: /登\s*录/ }).click()
  await expect(page).toHaveURL(/\/$/)
  await expect(page.locator('.role-tag')).toHaveText(roleLabel)
  await expect(page.locator('h2.page-title')).toContainText('欢迎回来')
  await waitForStableUi(page)
}

async function openMenuPage(page: Page, menuName: string, routePath: string, heading: string) {
  await page.getByRole('menuitem', { name: new RegExp(menuName) }).click()
  await expect(page).toHaveURL(new RegExp(`${routePath.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}$`))
  await expect(page.locator('h2.page-title')).toHaveText(heading)
  await waitForStableUi(page)
}

async function listQuestions(page: Page) {
  return apiData<PageData<Question>>(page, '/api/question/page?pageNum=1&pageSize=100')
}

async function createQuestionFixture(page: Page, fixture: typeof targetQuestion) {
  return apiData<number>(page, '/api/question', {
    method: 'POST',
    body: {
      subjectId: 1,
      stem: fixture.stem,
      answer: fixture.answer,
      source: fixture.source,
    },
  })
}

async function ensureQuestion(page: Page, fixture: typeof targetQuestion) {
  const existing = (await listQuestions(page)).records.find((question) => question.stem === fixture.stem)
  return existing?.id ?? createQuestionFixture(page, fixture)
}

async function waitForSuccessfulAnalysis(page: Page, questionId: number) {
  let analysis = await apiData<AiAnalysis | null>(page, `/api/ai/analysis/${questionId}`)
  if (!analysis || analysis.status === 2) {
    await apiData<void>(page, `/api/ai/analyze/${questionId}`, { method: 'POST' })
  }
  await expect
    .poll(async () => (await apiData<AiAnalysis | null>(page, `/api/ai/analysis/${questionId}`))?.status, {
      timeout: 30_000,
    })
    .toBe(1)
  analysis = await apiData<AiAnalysis>(page, `/api/ai/analysis/${questionId}`)
  return analysis
}

function parseReferenceIds(value?: string) {
  try {
    return JSON.parse(value || '[]') as number[]
  } catch {
    return []
  }
}

test('三角色核心业务页面走查并生成论文截图', async ({ page }) => {
  await mkdir(screenshotDir, { recursive: true })

  await resetSession(page)
  await capture(page, '01-login.png')
  await login(page, 'student', '学生')
  await capture(page, '02-student-home.png')

  await openMenuPage(page, '错题录入', '/question/create', '错题录入')
  await capture(page, '03-student-question-create.png')

  const referenceId = await ensureQuestion(page, referenceQuestion)
  await waitForSuccessfulAnalysis(page, referenceId)
  const targetId = await ensureQuestion(page, targetQuestion)
  let targetAnalysis = await waitForSuccessfulAnalysis(page, targetId)
  if (!parseReferenceIds(targetAnalysis.referenceIds).includes(referenceId)) {
    await apiData<void>(page, `/api/ai/analyze/${targetId}`, { method: 'POST' })
    await expect
      .poll(async () => {
        targetAnalysis = await apiData<AiAnalysis>(page, `/api/ai/analysis/${targetId}`)
        return targetAnalysis.status === 1 && parseReferenceIds(targetAnalysis.referenceIds).includes(referenceId)
      }, { timeout: 30_000 })
      .toBe(true)
  }

  await page.goto('/question/list')
  await expect(page.locator('h2.page-title')).toHaveText('错题本')
  await expect(page.getByText(targetQuestion.stem, { exact: true })).toBeVisible()
  await capture(page, '04-student-question-list.png')

  await page.goto(`/question/${targetId}`)
  await expect(page.locator('h2.page-title')).toHaveText('错题详情')
  await expect(page.getByText('解析内容', { exact: true })).toBeVisible({ timeout: 30_000 })
  await expect(page.getByText(referenceQuestion.stem, { exact: true })).toBeVisible()
  const variants = await apiData<unknown[]>(page, `/api/variant/list?questionId=${targetId}`)
  if (variants.length === 0) {
    await page.getByRole('button', { name: '生成变式题' }).click()
  }
  await expect(page.getByText(/变式 1 · 难度/)).toBeVisible({ timeout: 20_000 })
  await capture(page, '05-student-question-detail.png', 180)

  await openMenuPage(page, '复习计划', '/review', '复习计划')
  await capture(page, '06-student-review-plan.png')

  await openMenuPage(page, '学情报告', '/report', '学情报告')
  await expect(page.locator('.chart canvas')).toHaveCount(3)
  await capture(page, '07-student-report.png')
  const messages = await apiData<PageData<Message>>(page, '/api/message/page?pageNum=1&pageSize=100')
  if (!messages.records.some((message) => message.title === '学情周报已生成')) {
    await page.getByRole('button', { name: '手动生成本周周报' }).click()
    await expect(page.getByText('周报已生成，消息中心可查看通知')).toBeVisible()
    await waitForStableUi(page)
  }

  await openMenuPage(page, '消息中心', '/message', '消息中心')
  await expect(page.getByText('学情周报已生成', { exact: true })).toBeVisible()
  await capture(page, '08-student-message.png')

  await openMenuPage(page, '个人中心', '/profile', '个人中心')
  await capture(page, '09-student-profile.png')

  await resetSession(page)
  await login(page, 'teacher', '教师')
  await openMenuPage(page, '学情报告', '/report', '学情报告')
  await expect(page.getByText(/教师视角：全科目聚合/)).toBeVisible()
  await expect(page.locator('.chart canvas')).toHaveCount(3)
  await capture(page, '10-teacher-report.png')

  await resetSession(page)
  await login(page, 'admin', '管理员')
  await openMenuPage(page, '用户管理', '/admin/user', '用户管理')
  await capture(page, '11-admin-user.png')

  await openMenuPage(page, '科目管理', '/admin/subject', '科目管理')
  await capture(page, '12-admin-subject.png')

  await openMenuPage(page, '知识点管理', '/admin/knowledge', '知识点管理')
  await capture(page, '13-admin-knowledge.png')

  await openMenuPage(page, '公告', '/announcement', '公告')
  await expect(page.getByRole('button', { name: '发布公告' })).toBeVisible()
  await capture(page, '14-admin-announcement.png')
})
