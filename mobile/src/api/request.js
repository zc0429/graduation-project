import { apiBaseUrl } from '../config.js'

const TOKEN_KEY = 'wrongbook.mobile.token'
const LOGIN_URL = '/pages/login/index'
let redirecting = false

export class ApiError extends Error {
  constructor(message, code) {
    super(message)
    this.name = 'ApiError'
    this.code = code
  }
}

export const storedToken = () => uni.getStorageSync(TOKEN_KEY)
export const saveToken = (token) => uni.setStorageSync(TOKEN_KEY, token)

export function logout() {
  uni.removeStorageSync(TOKEN_KEY)
  const page = getCurrentPages().slice(-1)[0]
  if (redirecting || page?.route === 'pages/login/index') return
  redirecting = true
  uni.reLaunch({
    url: LOGIN_URL,
    complete: () => { redirecting = false },
  })
}

export function requireSession() {
  if (storedToken()) return true
  logout()
  return false
}

export function request(path, options = {}) {
  const { method = 'GET', data, authenticated = true, timeout = 15000 } = options
  const token = authenticated ? storedToken() : ''
  if (authenticated && !token) {
    logout()
    return Promise.reject(new ApiError('请先登录', 401))
  }

  return new Promise((resolve, reject) => {
    uni.request({
      url: apiBaseUrl + path,
      method,
      data,
      timeout,
      header: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      success({ statusCode, data: body }) {
        if (authenticated && token !== storedToken()) {
          reject(new ApiError('当前登录状态已变更', 401))
          return
        }
        if (authenticated && (statusCode === 401 || body?.code === 401)) logout()
        if (statusCode >= 200 && statusCode < 300 && body?.code === 0) {
          resolve(body.data)
          return
        }
        const fallback = statusCode === 401 ? '登录状态已失效，请重新登录' : `请求失败（HTTP ${statusCode}）`
        reject(new ApiError(body?.message || fallback, body?.code || statusCode))
      },
      fail(error) {
        const timedOut = /timeout/i.test(error?.errMsg || '')
        reject(new ApiError(timedOut ? '请求超时，请稍后重试' : '无法连接后端，请检查网络和后端地址'))
      },
    })
  })
}

export function errorMessage(error) {
  return error?.message || '操作失败，请稍后重试'
}
