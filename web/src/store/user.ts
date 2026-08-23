import { defineStore } from 'pinia'
import { userApi } from '@/api/user'
import type { UserInfo } from '@/types/api'
import { ApiError } from '@/utils/api-error'
import { setUnauthorizedHandler } from '@/utils/request'

export type { UserInfo } from '@/types/api'

const TOKEN_KEY = 'token'
const USER_KEY = 'user'

let pendingSessionCheck: Promise<boolean> | undefined

function readStoredUser(): UserInfo | null {
  const value = localStorage.getItem(USER_KEY)
  if (!value) return null
  try {
    return JSON.parse(value) as UserInfo
  } catch {
    localStorage.removeItem(USER_KEY)
    return null
  }
}

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem(TOKEN_KEY) || '',
    user: readStoredUser(),
    sessionChecked: false,
    sessionValidating: false,
  }),
  getters: {
    isLogin: (s) => !!s.token,
    role: (s) => s.user?.role || '',
    nickname: (s) => s.user?.nickname || s.user?.username || '',
  },
  actions: {
    setLogin(token: string, user: UserInfo) {
      this.token = token
      this.user = user
      this.sessionChecked = true
      localStorage.setItem(TOKEN_KEY, token)
      localStorage.setItem(USER_KEY, JSON.stringify(user))
    },
    setUser(user: UserInfo) {
      this.user = user
      this.sessionChecked = true
      localStorage.setItem(USER_KEY, JSON.stringify(user))
    },
    logout() {
      this.token = ''
      this.user = null
      this.sessionChecked = true
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
    },
    /**
     * Validate a restored token exactly once against `/user/profile`.
     * Resolves false for a missing/expired session; transient failures reject so
     * callers can show an offline state instead of incorrectly logging out.
     */
    ensureSession(): Promise<boolean> {
      if (!this.token) {
        this.sessionChecked = true
        return Promise.resolve(false)
      }
      if (this.sessionChecked && this.user) return Promise.resolve(true)
      if (pendingSessionCheck) return pendingSessionCheck

      const tokenBeingChecked = this.token
      this.sessionValidating = true
      pendingSessionCheck = userApi.profile({ silent: true })
        .then((profile) => {
          if (this.token !== tokenBeingChecked) return Boolean(this.token && this.user)
          this.setUser(profile)
          return true
        })
        .catch((error: unknown) => {
          if (error instanceof ApiError && error.isUnauthorized) {
            this.logout()
            return false
          }
          throw error
        })
        .finally(() => {
          this.sessionValidating = false
          pendingSessionCheck = undefined
        })
      return pendingSessionCheck
    },
  },
})

setUnauthorizedHandler(() => {
  useUserStore().logout()
})
