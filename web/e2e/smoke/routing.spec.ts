import { expect, installMockSession, test } from './ui.fixture'

test('未登录访问受保护页面会带回跳地址进入登录页', async ({ page }) => {
  await page.goto('/question/list')

  await expect(page).toHaveURL(/\/login\?redirect=\/question\/list/)
  await expect(page.getByRole('heading', { name: '回到学习桌' })).toBeVisible()
})

test('学生访问管理员页面会回到工作台并显示权限提示', async ({ page }) => {
  await installMockSession(page, 'student')
  await page.goto('/admin/user')

  await expect(page).toHaveURL(/\/\?notice=forbidden$/)
  await expect(page.getByRole('alert')).toContainText('当前账号没有访问上一页面的权限')
})

test('已登录用户访问未知地址会看到 404 并可返回工作台', async ({ page }) => {
  await installMockSession(page, 'student')
  await page.goto('/missing-page')

  await expect(page.getByRole('heading', { name: '页面未找到' })).toBeVisible()
  await page.getByRole('button', { name: '返回今日工作台' }).click()
  await expect(page).toHaveURL(/\/$/)
})
