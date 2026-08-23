import { expect, test, type Page } from '@playwright/test'
import { mkdir } from 'node:fs/promises'
import { pathToFileURL } from 'node:url'
import { fileURLToPath } from 'node:url'

const prototypePath = fileURLToPath(new URL('../../docs/design/frontend-prototype.html', import.meta.url))
const screenshotDir = fileURLToPath(new URL('../../docs/design/frontend-prototype-screenshots/', import.meta.url))
const prototypeUrl = pathToFileURL(prototypePath).href

const views = [
  { key: 'auth', role: 'student', name: '01-login-register' },
  { key: 'home', role: 'student', name: '02-student-home' },
  { key: 'detail', role: 'student', name: '03-question-detail' },
  { key: 'review', role: 'student', name: '04-review-plan' },
  { key: 'report', role: 'student', name: '05-learning-report' },
  { key: 'admin', role: 'admin', name: '06-admin-data' },
] as const

const sizes = [
  { prefix: 'desktop-1600x1200', width: 1600, height: 1200, screenshots: true },
  { prefix: 'laptop-1280x800', width: 1280, height: 800, screenshots: false },
  { prefix: 'tablet-820x1180', width: 820, height: 1180, screenshots: true },
  { prefix: 'mobile-390x844', width: 390, height: 844, screenshots: true },
] as const

async function openView(page: Page, key: string, role: string) {
  await page.goto(`${prototypeUrl}?capture=1#${key}:${role}`)
  await page.evaluate(() => document.fonts.ready)
  await page.waitForTimeout(80)
  await expect(page.locator(`[data-screen="${key}"].is-active`)).toBeVisible()
}

async function expectNoPageOverflow(page: Page) {
  const overflow = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    innerWidth: window.innerWidth,
  }))
  expect(overflow.scrollWidth).toBeLessThanOrEqual(overflow.innerWidth + 1)
}

async function expectOneVisibleTitle(page: Page) {
  await expect(page.locator('[data-screen].is-active h1:visible')).toHaveCount(1)
}

test.beforeEach(async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce', colorScheme: 'light' })
})

test('六个代表界面在桌面、笔记本、平板和手机均无页面级横向溢出', async ({ page }) => {
  const pageErrors: string[] = []
  page.on('pageerror', (error) => pageErrors.push(error.message))
  await mkdir(screenshotDir, { recursive: true })

  for (const size of sizes) {
    await page.setViewportSize({ width: size.width, height: size.height })
    for (const view of views) {
      await openView(page, view.key, view.role)
      await expectOneVisibleTitle(page)
      await expectNoPageOverflow(page)
      if (size.screenshots) {
        await page.screenshot({
          path: `${screenshotDir}/${size.prefix}-${view.name}.png`,
          animations: 'disabled',
          caret: 'hide',
          fullPage: false,
        })
      }
    }
  }

  expect(pageErrors).toEqual([])
})

test('三角色首页与教师聚合报告可切换并留存桌面证据', async ({ page }) => {
  await mkdir(screenshotDir, { recursive: true })
  await page.setViewportSize({ width: 1600, height: 1200 })

  await openView(page, 'home', 'teacher')
  await expect(page.getByText('全站聚合学情', { exact: false })).toBeVisible()
  await expect(page.getByText('不提供班级选择', { exact: false })).toBeVisible()
  await page.screenshot({ path: `${screenshotDir}/desktop-1600x1200-07-teacher-home.png`, animations: 'disabled', caret: 'hide' })

  await openView(page, 'home', 'admin')
  await expect(page.getByRole('heading', { name: '系统管理员，维护当前有效数据。' })).toBeVisible()
  await page.screenshot({ path: `${screenshotDir}/desktop-1600x1200-08-admin-home.png`, animations: 'disabled', caret: 'hide' })

  await openView(page, 'report', 'teacher')
  await expect(page.getByText('全站聚合学习数据（无班级绑定）')).toBeVisible()
  await page.screenshot({ path: `${screenshotDir}/desktop-1600x1200-09-teacher-report.png`, animations: 'disabled', caret: 'hide' })
})

test('核心原型交互可用', async ({ page }) => {
  await page.setViewportSize({ width: 1600, height: 1200 })

  await openView(page, 'auth', 'student')
  await page.getByRole('tab', { name: '注册' }).click()
  await expect(page.getByRole('button', { name: '创建学生账号' })).toBeVisible()
  await page.getByRole('tab', { name: '登录' }).click()
  await expect(page.getByRole('button', { name: /进入知错工作台/ })).toBeVisible()

  await openView(page, 'detail', 'student')
  await page.getByRole('button', { name: '查看正确答案' }).click()
  await expect(page.locator('#answer-content')).toBeVisible()
  await page.getByRole('tab', { name: 'RAG 参考' }).click()
  await expect(page.getByRole('heading', { name: '本地参考题 #018' })).toBeVisible()
  await page.getByRole('tab', { name: 'AI 智能解析' }).click()
  await page.getByRole('button', { name: '失败' }).click()
  await expect(page.getByRole('heading', { name: '这次解析没有完成' })).toBeVisible()
  await page.getByRole('button', { name: '部分结果' }).click()
  await expect(page.getByText('部分结果由前端根据字段缺失派生', { exact: false })).toBeVisible()

  await openView(page, 'review', 'student')
  await page.getByRole('button', { name: '已逾期 1' }).click()
  await expect(page.locator('.review-item:visible')).toHaveCount(1)
  await page.getByRole('button', { name: '完成复习' }).click()
  await expect(page.locator('.review-item:visible')).toHaveClass(/is-done/)

  await openView(page, 'admin', 'admin')
  await page.getByRole('tab', { name: '科目' }).click()
  await page.getByRole('button', { name: '新增科目' }).click()
  await expect(page.getByRole('dialog')).toBeVisible()
  await page.getByRole('button', { name: '取消' }).click()
  await expect(page.getByRole('dialog')).toBeHidden()
  await page.getByRole('tab', { name: '用户' }).click()
  await page.getByLabel('按角色筛选').selectOption('teacher')
  await expect(page.locator('#user-table-body tr:visible')).toHaveCount(1)
})
