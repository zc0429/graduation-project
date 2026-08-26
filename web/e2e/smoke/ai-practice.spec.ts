import { expect, installMockSession, test } from './ui.fixture'

test.beforeEach(async ({ page }) => {
  await installMockSession(page, 'student')
})

test('AI 解析展示成功证据并可从空状态重新触发', async ({ page, mockApi }) => {
  mockApi.analyses[201] = null
  await page.goto('/question/201')

  await expect(page.getByText('尚未生成 AI 解析', { exact: true })).toBeVisible()
  await page.getByRole('button', { name: '触发 AI 智能解析' }).click()
  await expect(page.getByText('AI 正在分析这道错题', { exact: true })).toBeVisible()
  await expect(page.getByText('重新检查后发现关键约束遗漏。', { exact: true })).toBeVisible()
  await expect(page.getByText('mock-model', { exact: true })).toBeVisible()
})

test('AI 失败状态明确提供重试动作', async ({ page, mockApi }) => {
  mockApi.analyses[201] = {
    id: 501,
    questionId: 201,
    status: 2,
    createTime: '2026-08-23 12:00:00',
  }

  await page.goto('/question/201')

  await expect(page.getByText('AI 解析失败', { exact: true })).toBeVisible()
  await expect(page.getByRole('button', { name: '重新加载' })).toBeVisible()
})

test('相似题只在打开页签后请求并展示当前账号候选', async ({ page, mockApi }) => {
  await page.goto('/question/201')

  expect(mockApi.requests.some((item) => item.pathname === '/api/recommend/similar')).toBe(false)
  await page.getByRole('tab', { name: /相似题/ }).click()

  await expect(page.getByText('阅读短文并判断作者的主要观点。', { exact: true })).toBeVisible()
  expect(mockApi.requests.filter((item) => item.pathname === '/api/recommend/similar')).toHaveLength(1)
})

test('生成变式题并提交一次变式练习自评', async ({ page, mockApi }) => {
  await page.goto('/question/201')
  await page.getByRole('tab', { name: /AI 变式题/ }).click()

  await expect(page.getByText('若函数在给定区间单调递减，参数应满足什么条件？')).toBeVisible()
  await page.getByRole('button', { name: '生成变式题' }).click()
  await expect(page.getByText('改变区间端点后，重新判断函数单调性。')).toBeVisible()

  const firstVariant = page.locator('.variant-list article').first()
  await firstVariant.getByRole('button', { name: '作答并记录' }).click()
  const practiceDialog = page.getByRole('dialog', { name: '作答变式 1' })
  await practiceDialog.getByLabel('我的作答').fill('令导数不大于零并检查端点。')
  await practiceDialog.getByText('答对了', { exact: true }).click()
  await expect(practiceDialog.getByRole('radio', { name: '答对了' })).toBeChecked()
  await practiceDialog.getByRole('button', { name: '提交练习记录' }).click()

  await expect.poll(() => mockApi.practices[0]).toMatchObject({
    variantId: 701,
    userAnswer: '令导数不大于零并检查端点。',
    isCorrect: 1,
  })
})
