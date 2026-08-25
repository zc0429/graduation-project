import { expect, installMockSession, test } from './ui.fixture'

test.beforeEach(async ({ page }) => {
  await installMockSession(page, 'student')
})

test('错题列表支持筛选并以 JWT 导出文件', async ({ page, mockApi }) => {
  await page.goto('/question/list')

  await expect(page.getByRole('heading', { name: '错题本' })).toBeVisible()
  await expect(page.getByRole('link', { name: /已知函数在区间上单调递增/ })).toBeVisible()

  await page.getByLabel('科目').click()
  await page.getByRole('option', { name: '英语' }).click()
  await expect(page.getByRole('link', { name: /阅读短文并判断作者/ })).toBeVisible()
  await expect(page.getByRole('link', { name: /已知函数在区间上单调递增/ })).toHaveCount(0)

  await page.getByRole('button', { name: '导出筛选结果' }).click()
  await expect.poll(() => mockApi.requests.find((item) => item.pathname === '/api/question/export')).toMatchObject({
    method: 'GET',
    authorization: 'Bearer ui-student-token',
  })
})

test('录入错题后进入详情并启动解析', async ({ page, mockApi }) => {
  await page.goto('/question/create')

  await page.getByLabel('科目').click()
  await page.getByRole('option', { name: '数学' }).click()
  await page.getByLabel('来源（选填）').fill('专项训练 · 第 6 题')
  await page.getByLabel('题干').fill('求函数在指定区间内的最大值。')
  await page.getByLabel('正确答案或订正（选填）').fill('先求导，再比较端点值。')
  await page.getByRole('button', { name: '保存并启动解析' }).click()

  await expect(page).toHaveURL(/\/question\/203$/)
  await expect(page.getByRole('heading', { name: '错题 #203' })).toBeVisible()
  expect(mockApi.questions.some((item) => item.stem === '求函数在指定区间内的最大值。')).toBe(true)
  expect(mockApi.requests.some((item) => item.pathname === '/api/ai/analyze/203')).toBe(true)
})

test('错题详情可编辑并在确认后删除', async ({ page, mockApi }) => {
  await page.goto('/question/201')

  await page.getByRole('button', { name: '编辑错题' }).click()
  const editDialog = page.getByRole('dialog', { name: '编辑错题' })
  await editDialog.getByLabel('题干').fill('已修订：讨论函数单调性与参数范围。')
  await editDialog.getByRole('button', { name: '保存修改' }).click()
  await expect(page.getByText('已修订：讨论函数单调性与参数范围。', { exact: true })).toBeVisible()

  await page.getByRole('button', { name: '删除' }).click()
  const confirmDialog = page.getByRole('dialog', { name: '删除错题' })
  await confirmDialog.getByRole('button', { name: '确认删除' }).click()

  await expect(page).toHaveURL(/\/question\/list$/)
  expect(mockApi.questions.some((item) => item.id === 201)).toBe(false)
})
