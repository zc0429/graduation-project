import AxeBuilder from '@axe-core/playwright'
import { expect, installMockSession, test, type MockRole } from './ui.fixture'
import type { Page } from '@playwright/test'

async function expectNoHighImpactViolations(page: Page) {
  const result = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
    .analyze()
  const findings = result.violations
    .filter((violation) => violation.impact === 'critical' || violation.impact === 'serious')
    .map((violation) => ({
      id: violation.id,
      impact: violation.impact,
      targets: violation.nodes.slice(0, 4).map((node) => ({
        target: node.target.map(String),
        html: node.html,
        summary: node.failureSummary,
      })),
    }))
  expect(findings).toEqual([])
}

async function openAs(page: Page, role: MockRole, path: string) {
  await installMockSession(page, role)
  await page.goto(path)
  await expect(page.locator('main')).toBeVisible()
}

test('登录页没有严重或关键 WCAG A/AA 问题', async ({ page }) => {
  await page.goto('/login')
  await expect(page.getByRole('heading', { name: '回到学习桌' })).toBeVisible()
  await expectNoHighImpactViolations(page)
})

test('学生核心工作台没有严重或关键 WCAG A/AA 问题', async ({ page }) => {
  await openAs(page, 'student', '/')
  await expectNoHighImpactViolations(page)

  for (const path of ['/question/list', '/question/201', '/review', '/report']) {
    await page.goto(path)
    await expectNoHighImpactViolations(page)
  }
})

test('教师与管理员核心页没有严重或关键 WCAG A/AA 问题', async ({ page }) => {
  await openAs(page, 'teacher', '/report')
  await expectNoHighImpactViolations(page)

  await page.evaluate(() => localStorage.clear())
  await openAs(page, 'admin', '/admin/user')
  await expectNoHighImpactViolations(page)
})
