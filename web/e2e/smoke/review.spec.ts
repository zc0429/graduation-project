import { expect, installMockSession, test } from './ui.fixture'

test.beforeEach(async ({ page }) => {
  await installMockSession(page, 'student')
})

test('复习筛选区分逾期与今日任务', async ({ page }) => {
  await page.goto('/review')

  await page.getByRole('button', { name: '已逾期 1' }).click()
  await expect(page.getByText('函数单调性与参数范围', { exact: true })).toBeVisible()
  await expect(page.getByText('阅读理解主旨判断', { exact: true })).toHaveCount(0)

  await page.getByRole('button', { name: '今日 1' }).click()
  await expect(page.getByText('阅读理解主旨判断', { exact: true })).toBeVisible()
  await expect(page.getByText('函数单调性与参数范围', { exact: true })).toHaveCount(0)
})

test('确认完成复习后从清单移除任务', async ({ page, mockApi }) => {
  await page.goto('/review')

  const reviewItem = page.locator('.review-item').filter({ hasText: '函数单调性与参数范围' })
  await reviewItem.getByRole('button', { name: '完成复习' }).click()
  const dialog = page.getByRole('dialog', { name: '完成第 2 轮复习' })
  await dialog.getByRole('button', { name: '确认完成' }).click()

  await expect(page.getByText('函数单调性与参数范围', { exact: true })).toHaveCount(0)
  expect(mockApi.reviewPlans.some((item) => item.id === 801)).toBe(false)
})
