export interface ApiErrorOptions {
  code?: number
  httpStatus?: number
  details?: unknown
  cause?: unknown
}

/** A stable error shape for business, authentication, HTTP, and network errors. */
export class ApiError extends Error {
  readonly code: number
  readonly httpStatus?: number
  readonly details?: unknown
  readonly originalCause?: unknown

  constructor(message: string, options: ApiErrorOptions = {}) {
    super(message)
    this.name = 'ApiError'
    this.code = options.code ?? -1
    this.httpStatus = options.httpStatus
    this.details = options.details
    this.originalCause = options.cause
  }

  get isUnauthorized() {
    return this.code === 401 || this.httpStatus === 401
  }
}

interface ErrorLike {
  message?: unknown
  code?: unknown
  response?: {
    status?: unknown
    data?: unknown
  }
}

interface ErrorPayload {
  code?: unknown
  message?: unknown
}

function asPayload(value: unknown): ErrorPayload | undefined {
  return typeof value === 'object' && value !== null ? (value as ErrorPayload) : undefined
}

/** Convert unknown thrown values into the one error type consumed by the UI. */
export function toApiError(error: unknown, fallbackMessage = '请求失败'): ApiError {
  if (error instanceof ApiError) return error

  const source = typeof error === 'object' && error !== null ? (error as ErrorLike) : undefined
  const payload = asPayload(source?.response?.data)
  const httpStatus = typeof source?.response?.status === 'number' ? source.response.status : undefined
  const payloadCode = typeof payload?.code === 'number' ? payload.code : undefined
  const sourceCode = typeof source?.code === 'number' ? source.code : undefined
  const message = typeof payload?.message === 'string'
    ? payload.message
    : typeof source?.message === 'string'
      ? source.message
      : fallbackMessage

  return new ApiError(message, {
    code: payloadCode ?? sourceCode ?? httpStatus ?? -1,
    httpStatus,
    details: payload,
    cause: error,
  })
}
