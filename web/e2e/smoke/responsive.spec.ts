import {
  collectBrowserErrors,
  expect,
  expectDocumentWithinViewport,
  installMockSession,
  test,
} from './ui.fixture'

test('登录页在当前视口无页面级横向溢出', async ({ page }) => {
  const errors = collectBrowserErrors(page)
  await page.goto('/login')

  await expect(page.getByRole('heading', { name: /把每一道错题/ })).toBeVisible()
  await expectDocumentWithinViewport(page)
  expect(errors).toEqual([])
})

test('学生错题目录在当前视口无页面级横向溢出', async ({ page }) => {
  const errors = collectBrowserErrors(page)
  await installMockSession(page, 'student')
  await page.goto('/question/list')

  await expect(page.getByRole('heading', { name: '错题本' })).toBeVisible()
  await expectDocumentWithinViewport(page)
  expect(errors).toEqual([])
})

test('周报密集布局在当前视口无页面级横向溢出', async ({ page }) => {
  const errors = collectBrowserErrors(page)
  await installMockSession(page, 'student')
  await page.goto('/report')

  await expect(page.getByRole('heading', { name: '学情报告' })).toBeVisible()
  await expect(page.getByText('知识点掌握度', { exact: true })).toBeVisible()
  await expectDocumentWithinViewport(page)
  expect(errors).toEqual([])
})
