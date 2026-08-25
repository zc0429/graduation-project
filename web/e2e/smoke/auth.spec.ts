import { expect, installMockSession, test } from './ui.fixture'

test('学生可以登录并进入工作台', async ({ page }) => {
  await page.goto('/login')

  await page.getByLabel('用户名').fill('student_ui')
  await page.getByLabel('密码', { exact: true }).fill('pass123')
  await page.getByRole('button', { name: '进入知错工作台' }).click()

  await expect(page).toHaveURL(/\/$/)
  await expect(page.getByRole('heading', { name: '学习者，先把今天的两件事做好。' })).toBeVisible()
})

test('登录错误留在表单并显示服务端消息', async ({ page }) => {
  await page.goto('/login')

  await page.getByLabel('用户名').fill('bad_user')
  await page.getByLabel('密码', { exact: true }).fill('pass123')
  await page.getByRole('button', { name: '进入知错工作台' }).click()

  await expect(page).toHaveURL(/\/login$/)
  await expect(
    page.getByRole('region', { name: '回到学习桌' }).getByText('用户名或密码错误', { exact: true }),
  ).toBeVisible()
})

test('注册请求成功后回到登录模式', async ({ page, mockApi }) => {
  await page.goto('/login')

  await page.getByRole('button', { name: '注册' }).click()
  await page.getByLabel('用户名').fill('new_student')
  await page.getByLabel('昵称（选填）').fill('新同学')
  await page.getByLabel('密码', { exact: true }).fill('pass123')
  await page.getByLabel('确认密码').fill('pass123')
  await page.getByRole('button', { name: '创建学生账号' }).click()

  await expect(page.getByRole('button', { name: '登录' })).toHaveAttribute('aria-pressed', 'true')
  await expect(page.getByRole('button', { name: '进入知错工作台' })).toBeVisible()
  expect(mockApi.requests.find((item) => item.pathname === '/api/auth/register')).toMatchObject({
    method: 'POST',
    body: { username: 'new_student', password: 'pass123', nickname: '新同学' },
  })
})

test('恢复的令牌过期时重定向并保留原目标', async ({ page, mockApi }) => {
  mockApi.expiredRoles.push('student')
  await installMockSession(page, 'student')

  await page.goto('/report')

  await expect(page).toHaveURL(/\/login\?reason=expired&redirect=\/report/)
  await expect(page.getByRole('status')).toContainText('登录状态已过期，请重新登录。')
})
