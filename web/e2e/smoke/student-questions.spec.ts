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
  await page.getByRole('textbox', { name: '题干', exact: true }).fill('求函数在指定区间内的最大值。')
  await page.getByLabel('正确答案或订正（选填）').fill('先求导，再比较端点值。')
  await page.getByRole('button', { name: '保存并启动解析' }).click()

  await expect(page).toHaveURL(/\/question\/203$/)
  await expect(page.getByRole('heading', { name: '错题 #203' })).toBeVisible()
  expect(mockApi.questions.some((item) => item.stem === '<p>求函数在指定区间内的最大值。</p>')).toBe(true)
  expect(mockApi.requests.some((item) => item.pathname === '/api/ai/analyze/203')).toBe(true)
})

test('图片识别回填普通表单但不自动保存或污染正确答案', async ({ page, mockApi }) => {
  mockApi.recognitionDelayMs = 250
  await page.goto('/question/create')

  const recognizeButton = page.getByRole('button', { name: 'AI 识别题目' })
  await expect(recognizeButton).toBeDisabled()
  expect(mockApi.requests.some((item) => item.pathname === '/api/question-recognition/recognize')).toBe(false)

  await page.locator('input[type="file"]').setInputFiles({
    name: 'single-question.png',
    mimeType: 'image/png',
    buffer: Buffer.from(
      'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=',
      'base64',
    ),
  })
  await expect(recognizeButton).toBeEnabled()
  await recognizeButton.click()
  await expect(page.getByText('识别中', { exact: true })).toBeVisible()
  await expect(recognizeButton).toBeDisabled()

  await expect(page.locator('.el-select__selected-item').filter({ hasText: '数学' })).toBeVisible()
  await expect(page.getByRole('textbox', { name: '题干', exact: true })).toHaveText('已知函数 f(x) = x² - 5x + 6，求方程 f(x) = 0 的解。')
  await expect(page.getByLabel('来源（选填）')).toHaveValue('高一数学课堂练习')
  await expect(page.getByText('x = 3', { exact: true })).toBeVisible()
  await expect(page.getByText('AI 识别结果仅供辅助，请核对后再保存。')).toBeVisible()
  await expect(page.getByLabel('正确答案或订正（选填）')).toHaveValue('')

  expect(mockApi.requests.filter((item) => item.pathname === '/api/question-recognition/recognize')).toHaveLength(1)
  expect(mockApi.requests.some((item) => item.pathname === '/api/question' && item.method === 'POST')).toBe(false)
  expect(mockApi.questions).toHaveLength(2)
})

test('图片识别失败后仍可手工填写并由用户保存', async ({ page, mockApi }) => {
  mockApi.failNext['POST /api/question-recognition/recognize'] = '图片识别服务暂时不可用'
  await page.goto('/question/create')

  await page.locator('input[type="file"]').setInputFiles({
    name: 'single-question.png',
    mimeType: 'image/png',
    buffer: Buffer.from(
      'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=',
      'base64',
    ),
  })
  await page.getByRole('button', { name: 'AI 识别题目' }).click()
  await expect(page.getByText('图片识别服务暂时不可用')).toBeVisible()

  await page.getByLabel('科目').click()
  await page.getByRole('option', { name: '数学' }).click()
  await page.getByRole('textbox', { name: '题干', exact: true }).fill('识别失败后手工填写的题目。')
  await page.getByRole('button', { name: '保存并启动解析' }).click()

  await expect(page).toHaveURL(/\/question\/203$/)
  expect(mockApi.questions.some((item) => item.stem === '<p>识别失败后手工填写的题目。</p>')).toBe(true)
})

test('错题详情可编辑并在确认后删除', async ({ page, mockApi }) => {
  await page.goto('/question/201')

  await page.getByRole('button', { name: '编辑错题' }).click()
  const editDialog = page.getByRole('dialog', { name: '编辑错题' })
  await editDialog.getByRole('textbox', { name: '题干', exact: true }).fill('已修订：讨论函数单调性与参数范围。')
  await editDialog.getByRole('button', { name: '保存修改' }).click()
  await expect(page.getByText('已修订：讨论函数单调性与参数范围。', { exact: true })).toBeVisible()

  await page.getByRole('button', { name: '删除', exact: true }).click()
  const confirmDialog = page.getByRole('dialog', { name: '删除错题' })
  await confirmDialog.getByRole('button', { name: '确认删除' }).click()

  await expect(page).toHaveURL(/\/question\/list$/)
  expect(mockApi.questions.some((item) => item.id === 201)).toBe(false)
})
