import { expect, installMockSession, test } from './ui.fixture'
import { mkdir } from 'node:fs/promises'
import { resolve } from 'node:path'

test.beforeEach(async ({ page }) => { await installMockSession(page, 'student') })

test('富文本录入、展示、编辑与练习回显保持格式并过滤旧数据脚本', async ({ page, mockApi }, testInfo) => {
  await page.goto('/question/create')
  await page.getByLabel('科目').click()
  await page.getByRole('option', { name: '数学' }).click()
  const editor = page.getByRole('textbox', { name: '题干', exact: true })
  await expect(page.getByRole('toolbar', { name: '文字格式' })).toHaveCount(0)
  await editor.focus()
  await editor.evaluate((element) => {
    const clipboard = new DataTransfer()
    clipboard.setData('text/html', '<p><strong>已知函数</strong> f(x) = x<sup>2</sup> - 5x + 6，求零点。</p><ul><li>保留计算过程</li></ul>')
    clipboard.setData('text/plain', '已知函数 f(x) = x² - 5x + 6，求零点。\n保留计算过程')
    element.dispatchEvent(new ClipboardEvent('paste', { clipboardData: clipboard, bubbles: true, cancelable: true }))
  })
  await expect(editor.locator('strong')).toContainText('已知函数')
  await expect(editor.locator('sup')).toHaveText('2')
  await expect(editor.locator('li')).toHaveText('保留计算过程')
  await page.screenshot({ path: testInfo.outputPath('editor-desktop.png'), fullPage: true })
  await page.setViewportSize({ width: 390, height: 844 })
  await expect(editor).toBeVisible()
  await page.screenshot({ path: testInfo.outputPath('editor-mobile.png'), fullPage: true })
  await page.setViewportSize({ width: 1600, height: 1200 })
  await page.getByRole('button', { name: '保存并启动解析' }).click()
  await expect(page).toHaveURL(/\/question\/203$/)
  expect(mockApi.questions.find(item => item.id === 203)?.stem).toContain('<strong>')
  await expect(page.locator('.stem strong')).toContainText('已知函数')
  await expect(page.locator('.stem sup')).toHaveText('2')
  await expect(page.locator('.stem li')).toHaveText('保留计算过程')
  await page.getByRole('button', { name: '编辑错题' }).click()
  const edit = page.getByRole('dialog', { name: '编辑错题' })
  await expect(edit.locator('[role=textbox] strong')).toContainText('已知函数')
  await expect(edit.locator('[role=textbox] sup')).toHaveText('2')
  await edit.getByRole('textbox', { name: '题干', exact: true }).fill('订正：0 < x < 3')
  await edit.getByRole('button', { name: '保存修改' }).click()
  await expect(edit).toBeHidden()
  await expect(page.locator('.stem')).toHaveText('订正：0 < x < 3')
  await page.getByRole('button', { name: '开始重做' }).click()
  await expect(page.getByRole('dialog').locator('.question-content')).toHaveText('订正：0 < x < 3')
  await page.getByRole('dialog').getByRole('button', { name: '取消', exact: true }).click()
  const q = mockApi.questions.find(item => item.id === 201)!
  q.stem = '<p onclick="window.__xss=1">历史题<strong>格式</strong><script>window.__xss=1</script><img src=x onerror="window.__xss=1"></p>'
  await page.goto('/question/201')
  await expect(page.locator('.stem')).toHaveText('历史题格式')
  expect(await page.evaluate(() => '__xss' in window)).toBe(false)
  await expect(page.locator('.stem img, .stem script')).toHaveCount(0)
})

test('图片识别候选可继续富文本修改，确认前无错题写入并生成本轮界面证据', async ({ page, mockApi }) => {
  await page.goto('/question/create')
  const sample = await page.evaluate(() => {
    const canvas = document.createElement('canvas'); canvas.width = 1000; canvas.height = 330
    const context = canvas.getContext('2d')!
    context.fillStyle = '#fff'; context.fillRect(0, 0, 1000, 330)
    context.fillStyle = '#111'; context.font = '28px sans-serif'
    context.fillText('高一数学课堂练习 · 合成单题测试图片', 36, 65)
    context.fillText('已知 f(x) = x² - 5x + 6，求方程 f(x) = 0 的解。', 36, 150)
    context.fillStyle = '#9c3426'; context.fillText('学生作答：x = 3', 36, 245)
    return canvas.toDataURL('image/png').split(',')[1]!
  })
  await page.locator('input[type=file]').setInputFiles({
    name: 'synthetic-math-question.png', mimeType: 'image/png', buffer: Buffer.from(sample, 'base64'),
  })
  await page.getByRole('button', { name: 'AI 识别题目' }).click()
  const editor = page.getByRole('textbox', { name: '题干', exact: true })
  await expect(editor).toContainText('已知函数')
  expect(mockApi.questions).toHaveLength(2)
  expect(mockApi.requests.filter(item => item.pathname === '/api/question' && item.method === 'POST')).toHaveLength(0)
  await expect(page.getByLabel('正确答案或订正（选填）')).toHaveValue('')
  await editor.press('ControlOrMeta+a')
  await editor.press('ControlOrMeta+b')
  await expect(editor.locator('strong')).toContainText('已知函数')
  const dir = resolve('../docs/thesis/screenshots/advisor-20261026')
  await mkdir(dir, { recursive: true })
  await page.evaluate(() => {
    const mark = document.createElement('div')
    mark.textContent = '2026-10-26 · Mock 接口界面验证 · 非真实 GLM 识别证据'
    mark.style.cssText = 'position:fixed;top:0;left:0;right:0;background:#fff4ce;color:#493100;z-index:99999;text-align:center;padding:6px;font:14px sans-serif'
    mark.id = 'evidence-mark'
    document.body.append(mark)
  })
  await page.getByLabel('正确答案或订正（选填）').click()
  await page.screenshot({ path: resolve(dir, '01-rich-input-recognition-mock.png'), fullPage: true })
  await page.getByRole('button', { name: '保存并启动解析' }).scrollIntoViewIfNeeded()
  await page.screenshot({ path: resolve(dir, '03-image-confirmation-mock.png'), fullPage: true })
  await page.getByRole('button', { name: '保存并启动解析' }).click()
  await expect(page).toHaveURL(/\/question\/203$/)
  await expect(page.locator('.stem strong')).toContainText('已知函数')
  await expect(page.locator('.el-message')).toHaveCount(0, { timeout: 10_000 })
  await page.screenshot({ path: resolve(dir, '02-rich-detail-mock.png'), fullPage: true })
})
