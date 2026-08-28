import { expect, test, type Page } from '@playwright/test'

const seedPassword = '123456'
const apiBase = 'http://127.0.0.1:8080'

async function login(page: Page, username: 'student' | 'teacher' | 'admin') {
  await page.goto('/login')
  await page.getByLabel('用户名').fill(username)
  await page.getByLabel('密码', { exact: true }).fill(seedPassword)
  await page.getByRole('button', { name: '进入知错工作台' }).click()
  await expect(page).toHaveURL(/\/$/)
  await expect(page.getByRole('navigation', { name: '功能目录' })).toBeVisible()
}

async function authHeader(page: Page) {
  const token = await page.evaluate(() => localStorage.getItem('token'))
  expect(token).toBeTruthy()
  return { Authorization: `Bearer ${token}` }
}

test.describe('wrongbook_e2e real backend', () => {
  test('student can create, edit, practise, export with JWT, and delete a question', async ({ page }) => {
    const uniqueStem = `E2E 二次函数错题 ${Date.now()}`
    const editedStem = `${uniqueStem}（已订正）`
    let exportAuthorization = ''

    page.on('request', (request) => {
      if (request.url().includes('/api/question/export')) {
        exportAuthorization = request.headers().authorization || ''
      }
    })

    await login(page, 'student')
    await page.goto('/question/create')
    await expect(page.getByRole('heading', { name: '录入一道值得重做的题' })).toBeVisible()

    await page.locator('.el-select').first().click()
    await page.getByRole('option', { name: '数学' }).click()
    await page.getByPlaceholder('完整抄录题目条件与问题，便于后续检索和解析').fill(uniqueStem)
    await page.getByPlaceholder('记录正确答案、关键步骤或自己的订正').fill('y = x²，先判断开口方向。')
    await page.getByPlaceholder('如：期中试卷 · 第 18 题').fill('wrongbook_e2e 自动化验收')
    await page.getByRole('button', { name: '保存并启动解析' }).click()

    await expect(page).toHaveURL(/\/question\/\d+$/)
    await expect(page.getByText(uniqueStem, { exact: true })).toBeVisible()

    await page.getByRole('button', { name: '编辑错题' }).click()
    const editDialog = page.getByRole('dialog', { name: '编辑错题' })
    await expect(editDialog).toBeVisible()
    await editDialog.locator('textarea').first().fill(editedStem)
    await editDialog.getByRole('button', { name: '保存修改' }).click()
    await expect(editDialog).toBeHidden()
    await expect(page.getByText(editedStem, { exact: true })).toBeVisible()

    await page.getByRole('button', { name: '开始重做' }).click()
    const practiceDialog = page.getByRole('dialog', { name: '重做这道错题' })
    await practiceDialog.locator('textarea').fill('先配方，再根据顶点式判断。')
    await practiceDialog.getByText('答对了', { exact: true }).click()
    await practiceDialog.getByRole('button', { name: '提交练习记录' }).click()
    await expect(practiceDialog).toBeHidden()

    await page.goto('/question/list')
    await expect(page.getByRole('heading', { name: '错题本' })).toBeVisible()
    const downloadPromise = page.waitForEvent('download')
    await page.getByRole('button', { name: '导出错题本' }).click()
    const download = await downloadPromise
    expect(download.suggestedFilename()).toMatch(/\.xlsx$/i)
    expect(exportAuthorization).toMatch(/^Bearer\s+\S+$/)

    await page.getByRole('link', { name: `查看错题：${editedStem}` }).click()
    await page.getByRole('button', { name: '删除' }).click()
    await page.getByRole('button', { name: '确认删除' }).click()
    await expect(page).toHaveURL(/\/question\/list$/)
  })

  test('teacher is limited to the aggregate report surface', async ({ page }) => {
    await login(page, 'teacher')
    await expect(page.getByRole('link', { name: '学情报告' })).toBeVisible()
    await expect(page.getByRole('link', { name: '错题本' })).toHaveCount(0)
    await page.goto('/question/list')
    await expect(page).toHaveURL(/\/?notice=forbidden$/)

    const response = await page.request.post(`${apiBase}/api/question`, {
      headers: await authHeader(page),
      data: { subjectId: 1, stem: '教师不应创建错题' },
    })
    expect(response.status()).toBe(403)
    await expect(response.json()).resolves.toMatchObject({ code: 403 })
  })

  test('administrator reaches the real management surfaces', async ({ page }) => {
    await login(page, 'admin')
    await page.getByRole('link', { name: '用户管理' }).click()
    await expect(page).toHaveURL(/\/admin\/user$/)
    await expect(page.getByRole('heading', { name: '用户管理' })).toBeVisible()
    await page.getByRole('link', { name: '科目管理' }).click()
    await expect(page.getByRole('heading', { name: '科目管理' })).toBeVisible()
    await page.getByRole('link', { name: '知识点管理' }).click()
    await expect(page.getByRole('heading', { name: '知识点管理' })).toBeVisible()
  })

  test('question images are returned only through an owned authenticated detail', async ({ page }) => {
    await login(page, 'student')
    const headers = await authHeader(page)
    const stem = `E2E 私有题图 ${Date.now()}`
    const createResponse = await page.request.post(`${apiBase}/api/question`, {
      headers,
      data: {
        subjectId: 1,
        stem,
        answer: '测试答案',
        source: 'wrongbook_e2e 私有题图验收',
        imageBase64: 'data:image/gif;base64,R0lGODlhAQABAAAAACw=',
      },
    })
    expect(createResponse.status()).toBe(200)
    const createBody = await createResponse.json() as { data: number }
    const questionId = createBody.data

    try {
      const detailResponse = await page.request.get(`${apiBase}/api/question/${questionId}`, { headers })
      expect(detailResponse.status()).toBe(200)
      const detailBody = await detailResponse.json() as { data: { imageUrl?: string } }
      expect(detailBody.data.imageUrl).toMatch(/^data:image\/gif;base64,/)

      const pageResponse = await page.request.get(`${apiBase}/api/question/page?pageNum=1&pageSize=100`, { headers })
      const pageBody = await pageResponse.json() as { data: { records: Array<{ id: number, imageUrl?: string }> } }
      const storedPath = pageBody.data.records.find((item) => item.id === questionId)?.imageUrl
      expect(storedPath).toMatch(/^\/uploads\//)

      const anonymousImage = await page.request.get(`${apiBase}${storedPath}`)
      expect(anonymousImage.status()).toBe(404)
    } finally {
      const deleteResponse = await page.request.delete(`${apiBase}/api/question/${questionId}`, { headers })
      expect(deleteResponse.status()).toBe(200)
    }
  })
})
