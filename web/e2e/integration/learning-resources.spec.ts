import { expect, test } from '@playwright/test'
import { mkdirSync } from 'node:fs'
import { resolve } from 'node:path'

test('personal resources: saved knowledge, original first, exhausted pool, explicit repetition', async ({ page, request }) => {
  const base = 'http://127.0.0.1:8080/api'
  const login = await request.post(`${base}/auth/login`, { data: { username: 'student', password: '123456' } })
  const auth = (await login.json()).data
  const headers = { Authorization: `Bearer ${auth.token}` }
  const create = await request.post(`${base}/question`, { headers, data: { subjectId: 1, stem: '求函数 y=x² 在区间 [0,2] 上的值域。', answer: '[0,4]', source: '20261112 自动化联调，Mock模型' } })
  const id = (await create.json()).data
  expect(Number(id)).toBeGreaterThan(0)
  try {
    await page.goto('/login')
    await page.getByLabel('用户名').fill('student'); await page.getByLabel('密码', { exact: true }).fill('123456')
    await page.getByRole('button', { name: '进入知错工作台' }).click(); await expect(page).toHaveURL(/\/$/)
    await page.goto(`/question/${id}`); await page.getByRole('tab', { name: '学习与练习' }).click()
    await page.getByRole('button', { name: '获取知识内容' }).click(); await expect(page.getByText('知识内容已生成并保存', { exact: true })).toBeVisible()
    await page.getByRole('button', { name: '再次查看知识内容' }).click(); await expect(page.getByText('已复用保存的知识内容', { exact: true })).toBeVisible()
    await page.getByRole('button', { name: '开始练习', exact: true }).click(); await expect(page.getByText('优先练习本人原题', { exact: true })).toBeVisible()
    await page.locator('.learning-resources').getByText('答对了', { exact: true }).click(); await page.getByRole('button', { name: '保存本次练习' }).click()
    await expect(page.getByText('本次练习已记录。继续练习将重新查询未练题。')).toBeVisible()
    await page.getByRole('button', { name: '继续练习', exact: true }).click(); await expect(page.getByText('新题已生成并保存', { exact: true })).toBeVisible()
    const list = async () => (await (await request.get(`${base}/variant/list?questionId=${id}`, { headers })).json()).data
    const batch = await list(); expect(batch).toHaveLength(3)
    const reused = await request.post(`${base}/learning/practice/next/${id}`, { headers }); expect((await reused.json()).data.source).toBe('existing')
    for (const variant of batch) {
      const result = await request.post(`${base}/practice`, { headers, data: { variantId: variant.id, isCorrect: 0, userAnswer: '自动化自评：答错仍视为已练' } })
      expect((await result.json()).code).toBe(0)
    }
    await page.getByRole('button', { name: '继续练习', exact: true }).click(); await expect.poll(async () => (await list()).length).toBe(6)
    await page.locator('.learning-resources').getByText('答对了', { exact: true }).click(); await page.getByRole('button', { name: '保存本次练习' }).click()
    await expect(page.getByRole('button', { name: '重新练习本题' })).toBeVisible()
    const dir = resolve(process.env.THESIS_EVIDENCE_DIR || '../docs/validation/thesis-audit-20261112/screenshots'); mkdirSync(dir, { recursive: true })
    await page.screenshot({ path: resolve(dir, 'learning-loop-mock.png'), fullPage: true })
    await page.getByRole('button', { name: '重新练习本题' }).click(); await page.locator('.learning-resources').getByText('仍然答错', { exact: true }).click(); await page.getByRole('button', { name: '保存本次练习' }).click()
    await expect(page.getByRole('button', { name: '重新练习本题' })).toBeVisible(); expect(await list()).toHaveLength(6)
  } finally { await request.delete(`${base}/question/${id}`, { headers }) }
})
