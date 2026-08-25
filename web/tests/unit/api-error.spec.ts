import { describe, expect, it } from 'vitest'
import { ApiError, toApiError } from '@/utils/api-error'

describe('API error normalization', () => {
  it('keeps an existing ApiError unchanged', () => {
    const original = new ApiError('登录已过期', { code: 401, httpStatus: 401 })

    expect(toApiError(original)).toBe(original)
    expect(original.isUnauthorized).toBe(true)
  })

  it('uses the response payload before a generic transport message', () => {
    const error = toApiError({
      message: 'Request failed',
      response: {
        status: 403,
        data: { code: 403, message: '当前角色无权访问' },
      },
    })

    expect(error).toMatchObject({
      name: 'ApiError',
      message: '当前角色无权访问',
      code: 403,
      httpStatus: 403,
    })
  })

  it('returns a stable fallback for an unknown thrown value', () => {
    const error = toApiError(null, '网络连接失败')

    expect(error.message).toBe('网络连接失败')
    expect(error.code).toBe(-1)
    expect(error.originalCause).toBeNull()
  })
})
