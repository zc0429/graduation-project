import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from '@/utils/api-error'

const mocks = vi.hoisted(() => ({
  profile: vi.fn(),
}))

vi.mock('@/api/user', () => ({
  userApi: {
    profile: mocks.profile,
  },
}))

import { useUserStore, type UserInfo } from '@/store/user'

const student: UserInfo = {
  id: 3,
  username: 'student_test',
  nickname: '测试学生',
  role: 'student',
}

describe('user session store', () => {
  beforeEach(() => {
    localStorage.clear()
    mocks.profile.mockReset()
    setActivePinia(createPinia())
  })

  it('persists a successful login and removes it on logout', () => {
    const store = useUserStore()

    store.setLogin('token-for-test', student)
    expect(store.isLogin).toBe(true)
    expect(localStorage.getItem('token')).toBe('token-for-test')
    expect(JSON.parse(localStorage.getItem('user') || 'null')).toMatchObject(student)

    store.logout()
    expect(store.isLogin).toBe(false)
    expect(localStorage.getItem('token')).toBeNull()
    expect(localStorage.getItem('user')).toBeNull()
  })

  it('drops malformed cached user data without throwing', () => {
    localStorage.setItem('token', 'restored-token')
    localStorage.setItem('user', '{not-json')
    setActivePinia(createPinia())

    const store = useUserStore()

    expect(store.token).toBe('restored-token')
    expect(store.user).toBeNull()
    expect(localStorage.getItem('user')).toBeNull()
  })

  it('clears an expired restored session', async () => {
    localStorage.setItem('token', 'expired-token')
    mocks.profile.mockRejectedValue(new ApiError('登录已过期', { code: 401, httpStatus: 401 }))
    setActivePinia(createPinia())
    const store = useUserStore()

    await expect(store.ensureSession()).resolves.toBe(false)

    expect(store.isLogin).toBe(false)
    expect(store.sessionChecked).toBe(true)
    expect(localStorage.getItem('token')).toBeNull()
  })

  it('deduplicates concurrent restored-session checks', async () => {
    localStorage.setItem('token', 'restored-token')
    mocks.profile.mockResolvedValue(student)
    setActivePinia(createPinia())
    const store = useUserStore()

    const first = store.ensureSession()
    const second = store.ensureSession()

    await expect(Promise.all([first, second])).resolves.toEqual([true, true])
    expect(mocks.profile).toHaveBeenCalledTimes(1)
    expect(store.user).toMatchObject(student)
  })
})
