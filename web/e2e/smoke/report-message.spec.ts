import { expect, installMockSession, test } from './ui.fixture'

test.beforeEach(async ({ page }) => {
  await installMockSession(page, 'student')
})

test('周报展示指标、掌握度与可读趋势表，并可重新生成', async ({ page, mockApi }) => {
  await page.goto('/report')

  await expect(page.getByRole('heading', { name: '学情报告' })).toBeVisible()
  await expect(page.getByText('错题累计', { exact: true })).toBeVisible()
  await expect(page.getByLabel('函数单调性掌握度')).toContainText('46%')
  await expect(page.getByText('本周共录入错题 3 次，08/20最多，为 2 次。')).toBeVisible()

  await page.getByText('查看每日错题数据表', { exact: true }).click()
  await expect(page.getByRole('table', { name: '本周每日新增错题数量' })).toBeVisible()
  await page.getByRole('button', { name: '生成本周报告' }).click()
  await expect.poll(() => mockApi.requests.some((item) => item.pathname === '/api/report/generate')).toBe(true)
})

test('消息可按未读筛选并标记为已读', async ({ page, mockApi }) => {
  await page.goto('/message')

  await page.getByRole('button', { name: '未读' }).click()
  await expect(page.getByText('有 1 道逾期错题待复习', { exact: true })).toBeVisible()
  await page.getByRole('button', { name: '标记已读' }).click()

  await expect(page.getByText('当前没有消息', { exact: true })).toBeVisible()
  expect(mockApi.messages.find((item) => item.id === 1001)?.isRead).toBe(1)
})
