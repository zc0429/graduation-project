import { collectBrowserErrors, expect, installMockSession, test } from './ui.fixture'

test('浏览器基线可完成路由、接口夹具和 Vue 渲染', async ({ page }) => {
  const errors = collectBrowserErrors(page)
  await installMockSession(page, 'student')
  await page.goto('/')

  await expect(page.getByRole('heading', { name: '学习者，先把今天的两件事做好。' })).toBeVisible()
  await expect(page.getByRole('link', { name: '错题本' })).toBeVisible()
  expect(errors).toEqual([])
})
