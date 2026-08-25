import { expect, installMockSession, test } from './ui.fixture'

test('教师周报只声明并展示全站聚合范围', async ({ page }) => {
  await installMockSession(page, 'teacher')
  await page.goto('/report')

  await expect(page.getByRole('note')).toContainText('仅展示全站聚合学习数据')
  await expect(page.getByText('当前后端没有班级或课程绑定')).toBeVisible()
  await expect(page.getByRole('link', { name: '用户管理' })).toHaveCount(0)
  await expect(page.getByText(/学生名单|班级排行|学生详情/)).toHaveCount(0)
})

test('管理员可筛选并逻辑注销其他用户', async ({ page, mockApi }) => {
  await installMockSession(page, 'admin')
  await page.goto('/admin/user')

  await page.getByLabel('用户名或昵称').fill('待注销学生')
  await page.getByRole('button', { name: '查询' }).click()
  await expect(page.getByText('second_student', { exact: true }).first()).toBeVisible()
  await page.getByRole('button', { name: '注销用户 待注销学生' }).click()
  await page.getByRole('dialog', { name: '注销用户' }).getByRole('button', { name: '确认注销' }).click()

  await expect(page.getByText('没有找到符合条件的用户', { exact: true })).toBeVisible()
  expect(mockApi.users.some((item) => item.id === 304)).toBe(false)
})

test('管理员可新增并编辑科目', async ({ page, mockApi }) => {
  await installMockSession(page, 'admin')
  await page.goto('/admin/subject')

  await page.getByRole('button', { name: '新增科目' }).click()
  const addDialog = page.getByRole('dialog', { name: '新增科目' })
  await addDialog.getByLabel('科目名称').fill('物理')
  await addDialog.getByLabel('科目编码').fill('PHYSICS')
  await addDialog.getByRole('button', { name: '创建科目' }).click()
  await expect(page.getByRole('heading', { name: '物理' })).toBeVisible()

  const physicsCard = page.locator('.subject-card').filter({ hasText: '物理' })
  await physicsCard.getByRole('button', { name: '编辑' }).click()
  const editDialog = page.getByRole('dialog', { name: '编辑科目' })
  await editDialog.getByLabel('科目名称').fill('大学物理')
  await editDialog.getByRole('button', { name: '保存修改' }).click()

  await expect(page.getByRole('heading', { name: '大学物理' })).toBeVisible()
  expect(mockApi.subjects.some((item) => item.name === '大学物理')).toBe(true)
})

test('管理员可新增章节、添加考点并删除叶节点', async ({ page, mockApi }) => {
  await installMockSession(page, 'admin')
  await page.goto('/admin/knowledge')

  await page.getByRole('button', { name: '新增章节' }).click()
  const chapterDialog = page.getByRole('dialog', { name: '新增章节' })
  await chapterDialog.getByLabel('章节名称').fill('统计与概率')
  await chapterDialog.getByRole('button', { name: '保存' }).click()
  await expect(page.getByRole('heading', { name: '统计与概率' })).toBeVisible()

  const chapterCard = page.locator('.chapter-card').filter({ hasText: '统计与概率' })
  await chapterCard.getByRole('button', { name: '添加考点' }).click()
  const pointDialog = page.getByRole('dialog', { name: '添加考点' })
  await pointDialog.getByLabel('考点名称').fill('条件概率')
  await pointDialog.getByRole('button', { name: '保存' }).click()
  await expect(page.getByText('条件概率', { exact: true })).toBeVisible()

  await page.getByRole('button', { name: '删除考点 条件概率' }).click()
  await page.getByRole('dialog', { name: '删除考点' }).getByRole('button', { name: '确认删除' }).click()
  await expect(page.getByText('条件概率', { exact: true })).toHaveCount(0)
  expect(JSON.stringify(mockApi.knowledgeTree)).not.toContain('条件概率')
})

test('管理员可发布公告且公告立即进入列表', async ({ page, mockApi }) => {
  await installMockSession(page, 'admin')
  await page.goto('/announcement')

  await page.getByRole('button', { name: '发布公告' }).click()
  const dialog = page.getByRole('dialog', { name: '发布公告' })
  await dialog.getByLabel('公告标题').fill('系统维护提醒')
  await dialog.getByLabel('公告内容').fill('今晚 22:00 进行短时维护。')
  await dialog.getByRole('button', { name: '确认发布' }).click()

  await expect(page.getByRole('heading', { name: '系统维护提醒' })).toBeVisible()
  expect(mockApi.announcements[0]?.title).toBe('系统维护提醒')
})
