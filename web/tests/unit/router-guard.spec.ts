import { beforeEach, describe, expect, it } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { createMemoryHistory } from 'vue-router'
import { createAppRouter } from '@/router'
import { useUserStore } from '@/store/user'

async function open(path: string) {
  const router = createAppRouter(createMemoryHistory())
  await router.push(path)
  await router.isReady()
  return router
}

describe('router guards', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
  })

  it('redirects an anonymous protected visit and preserves the target', async () => {
    const router = await open('/question/list')

    expect(router.currentRoute.value.name).toBe('login')
    expect(router.currentRoute.value.query.redirect).toBe('/question/list')
  })

  it('returns a student from an admin route with a visible notice flag', async () => {
    useUserStore().setLogin('unit-token', {
      id: 1,
      username: 'student',
      nickname: '学生',
      role: 'student',
    })

    const router = await open('/admin/user')

    expect(router.currentRoute.value.name).toBe('home')
    expect(router.currentRoute.value.query.notice).toBe('forbidden')
  })

  it('allows a teacher to open the aggregate report but not student routes', async () => {
    useUserStore().setLogin('unit-token', {
      id: 2,
      username: 'teacher',
      nickname: '教师',
      role: 'teacher',
    })

    const reportRouter = await open('/report')
    expect(reportRouter.currentRoute.value.name).toBe('report')

    const studentRouter = await open('/question/list')
    expect(studentRouter.currentRoute.value.name).toBe('home')
    expect(studentRouter.currentRoute.value.query.notice).toBe('forbidden')
  })

  it('sets the document title from route metadata', async () => {
    await open('/login')

    expect(document.title).toBe('登录 · 知错')
  })
})
