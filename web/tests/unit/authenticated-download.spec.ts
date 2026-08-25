import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const messages = vi.hoisted(() => ({
  show: vi.fn(),
}))

const axiosMock = vi.hoisted(() => ({
  get: vi.fn(),
  isAxiosError: vi.fn(() => false),
  create: vi.fn(() => ({
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
  })),
}))

vi.mock('element-plus', () => ({
  ElMessage: messages.show,
}))

vi.mock('axios', () => ({ default: axiosMock }))

import { ApiError, requestAuthenticatedFile, saveDownloadedFile } from '@/utils/request'

describe('authenticated file download', () => {
  beforeEach(() => {
    localStorage.clear()
    messages.show.mockReset()
    axiosMock.get.mockReset()
    axiosMock.isAxiosError.mockReset()
    axiosMock.isAxiosError.mockReturnValue(false)
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.unstubAllGlobals()
  })

  it('sends the JWT and decodes a safe UTF-8 filename', async () => {
    localStorage.setItem('token', 'jwt-for-download')
    axiosMock.get.mockResolvedValue({
      status: 200,
      data: new Blob(['xlsx-bytes'], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' }),
      headers: {
          'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
          'content-type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
          'content-disposition': "attachment; filename*=UTF-8''%E9%94%99%E9%A2%98%E6%9C%AC.xlsx",
      },
    })

    const file = await requestAuthenticatedFile('/api/question/export?subjectId=1', '错题本.xlsx')

    expect(file.fileName).toBe('错题本.xlsx')
    expect(await file.blob.text()).toBe('xlsx-bytes')
    const requestOptions = axiosMock.get.mock.calls[0]?.[1] as { headers: Record<string, string>; responseType: string; timeout: number }
    expect(requestOptions.headers.Authorization).toBe('Bearer jwt-for-download')
    expect(requestOptions.responseType).toBe('blob')
    expect(requestOptions.timeout).toBe(60_000)
  })

  it('turns a JSON error body into ApiError instead of a download', async () => {
    axiosMock.get.mockResolvedValue({
      status: 403,
      data: new Blob([JSON.stringify({ code: 403, message: '无权导出该错题本' })], { type: 'application/json' }),
      headers: { 'content-type': 'application/json' },
    })

    await expect(requestAuthenticatedFile('/api/question/export', '错题本.xlsx')).rejects.toMatchObject<ApiError>({
      name: 'ApiError',
      message: '无权导出该错题本',
      code: 403,
      httpStatus: 403,
    })
    expect(messages.show).toHaveBeenCalledOnce()
  })

  it('clicks a temporary link and releases its object URL', () => {
    vi.useFakeTimers()
    const createObjectURL = vi.fn(() => 'blob:ui-test')
    const revokeObjectURL = vi.fn()
    vi.stubGlobal('URL', { ...URL, createObjectURL, revokeObjectURL })
    const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => undefined)

    saveDownloadedFile({ blob: new Blob(['file']), fileName: '错题本.xlsx' })
    vi.runAllTimers()

    expect(createObjectURL).toHaveBeenCalledOnce()
    expect(click).toHaveBeenCalledOnce()
    expect(revokeObjectURL).toHaveBeenCalledWith('blob:ui-test')
    expect(document.querySelector('a[download]')).toBeNull()
  })
})
