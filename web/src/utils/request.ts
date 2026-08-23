import axios, { type AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'
import type { RestResponse } from '@/types/api'
import { ApiError, toApiError } from '@/utils/api-error'

declare module 'axios' {
  interface AxiosRequestConfig<D = any, P = any> {
    /** Suppress the global toast while still normalizing and propagating errors. */
    silent?: boolean
  }
}

export type { RestResponse } from '@/types/api'
export { ApiError, toApiError } from '@/utils/api-error'

export const UNAUTHORIZED_EVENT = 'wrongbook:unauthorized'

export interface DownloadedFile {
  blob: Blob
  fileName: string
}

type UnauthorizedHandler = (error: ApiError) => void

export interface UnauthorizedEventDetail {
  code: number
  message: string
}

let unauthorizedHandler: UnauthorizedHandler | undefined

/** Register the auth-store cleanup without importing Pinia or the router here. */
export function setUnauthorizedHandler(handler?: UnauthorizedHandler) {
  unauthorizedHandler = handler
}

/** Subscribe without taking ownership of the auth-store cleanup callback. */
export function subscribeUnauthorized(listener: (detail: UnauthorizedEventDetail) => void) {
  if (typeof window === 'undefined') return () => undefined
  const eventListener: EventListener = (event) => {
    listener((event as CustomEvent<UnauthorizedEventDetail>).detail)
  }
  window.addEventListener(UNAUTHORIZED_EVENT, eventListener)
  return () => window.removeEventListener(UNAUTHORIZED_EVENT, eventListener)
}

const request = axios.create({
  baseURL: '/api',
  timeout: 15000,
})

// 请求拦截：携带 JWT
request.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截：统一解包 {code, message, data}，非 0 抛错并提示
request.interceptors.response.use(
  (response: AxiosResponse<RestResponse<unknown>>) => {
    const body = response.data
    if (body.code === 0) {
      return body.data as never
    }
    const error = new ApiError(body.message || '请求失败', {
      code: body.code,
      httpStatus: response.status,
      details: body,
    })
    handleError(error, response.config.silent)
    return Promise.reject(error)
  },
  (error: unknown) => {
    const normalized = toApiError(error, '网络异常')
    const silent = typeof error === 'object' && error !== null && 'config' in error
      ? Boolean((error as { config?: { silent?: boolean } }).config?.silent)
      : false
    handleError(normalized, silent)
    return Promise.reject(normalized)
  },
)

function handleError(error: ApiError, silent = false) {
  if (error.isUnauthorized) {
    unauthorizedHandler?.(error)
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent(UNAUTHORIZED_EVENT, {
        detail: { code: error.code, message: error.message },
      }))
    }
  }
  if (!silent) {
    ElMessage({ type: 'error', message: error.message, grouping: true })
  }
}

function parseContentDispositionFilename(header: string | null, fallback: string) {
  if (!header) return fallback
  const utf8Match = header.match(/filename\*\s*=\s*UTF-8''([^;]+)/i)
  const plainMatch = header.match(/filename\s*=\s*"?([^";]+)"?/i)
  const encoded = utf8Match?.[1]?.trim()
  const plain = plainMatch?.[1]?.trim()
  let candidate = fallback
  try {
    candidate = encoded ? decodeURIComponent(encoded) : plain || fallback
  } catch {
    candidate = plain || fallback
  }
  return candidate.split(/[\\/]/).pop()?.replace(/[\u0000-\u001f\u007f]/g, '') || fallback
}

async function parseJsonError(response: Response): Promise<ApiError> {
  let payload: Partial<RestResponse<unknown>> | undefined
  try {
    payload = await response.json() as Partial<RestResponse<unknown>>
  } catch {
    // A malformed JSON error should still become a stable ApiError.
  }
  const message = payload?.code === 0
    ? '服务器未返回可下载的文件'
    : payload?.message || `下载失败（${response.status}）`
  return new ApiError(message, {
    code: payload?.code === 0 ? -1 : typeof payload?.code === 'number' ? payload.code : response.status,
    httpStatus: response.status,
    details: payload,
  })
}

/** Fetch an authenticated binary response without passing it through the JSON interceptor. */
export async function requestAuthenticatedFile(url: string, fallbackFileName: string): Promise<DownloadedFile> {
  const headers = new Headers()
  const token = localStorage.getItem('token')
  if (token) headers.set('Authorization', `Bearer ${token}`)

  let response: Response
  try {
    response = await fetch(url, { headers })
  } catch (cause) {
    const error = toApiError(cause, '下载失败，请检查网络连接')
    handleError(error)
    throw error
  }

  const contentType = response.headers.get('Content-Type')?.toLowerCase() || ''
  if (!response.ok || contentType.includes('json')) {
    const error = await parseJsonError(response)
    handleError(error)
    throw error
  }

  return {
    blob: await response.blob(),
    fileName: parseContentDispositionFilename(response.headers.get('Content-Disposition'), fallbackFileName),
  }
}

/** Trigger a browser download and release the temporary object URL. */
export function saveDownloadedFile(file: DownloadedFile) {
  const objectUrl = URL.createObjectURL(file.blob)
  const anchor = document.createElement('a')
  anchor.href = objectUrl
  anchor.download = file.fileName
  anchor.style.display = 'none'
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  window.setTimeout(() => URL.revokeObjectURL(objectUrl), 0)
}

export default request
