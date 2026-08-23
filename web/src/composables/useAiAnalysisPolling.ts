import {
  computed,
  onScopeDispose,
  ref,
  shallowRef,
  toValue,
  type MaybeRefOrGetter,
} from 'vue'
import { aiApi } from '@/api/ai'
import type { AiAnalysis } from '@/types/api'
import { ApiError, toApiError } from '@/utils/api-error'

export type AiPollingState = 'idle' | 'triggering' | 'polling' | 'success' | 'failed' | 'timeout' | 'error'

export interface AiPollingOptions {
  intervalMs?: number
  timeoutMs?: number
  maxConsecutiveErrors?: number
  onSuccess?: (analysis: AiAnalysis) => void | Promise<void>
  onFailure?: (analysis: AiAnalysis) => void | Promise<void>
}

const DEFAULT_INTERVAL_MS = 2_000
const DEFAULT_TIMEOUT_MS = 90_000
const DEFAULT_MAX_CONSECUTIVE_ERRORS = 3

/**
 * Non-overlapping AI status polling with bounded retries and lifecycle cleanup.
 * Call `sync()` for an existing analysis, or `trigger()` to start a new one.
 */
export function useAiAnalysisPolling(
  questionId: MaybeRefOrGetter<number>,
  options: AiPollingOptions = {},
) {
  const analysis = shallowRef<AiAnalysis | null>(null)
  const state = ref<AiPollingState>('idle')
  const error = shallowRef<ApiError | null>(null)
  const consecutiveErrors = ref(0)
  const startedAt = ref<number>()

  const intervalMs = Math.max(500, options.intervalMs ?? DEFAULT_INTERVAL_MS)
  const timeoutMs = Math.max(intervalMs, options.timeoutMs ?? DEFAULT_TIMEOUT_MS)
  const maxConsecutiveErrors = Math.max(1, options.maxConsecutiveErrors ?? DEFAULT_MAX_CONSECUTIVE_ERRORS)

  let timer: ReturnType<typeof setTimeout> | undefined
  let runVersion = 0

  const isPolling = computed(() => state.value === 'triggering' || state.value === 'polling')

  function resolveQuestionId() {
    const id = Number(toValue(questionId))
    if (!Number.isSafeInteger(id) || id <= 0) {
      throw new ApiError('错题编号无效', { code: 400 })
    }
    return id
  }

  function clearTimer() {
    if (timer !== undefined) clearTimeout(timer)
    timer = undefined
  }

  function settle(version: number, nextState: AiPollingState) {
    if (version !== runVersion) return false
    clearTimer()
    state.value = nextState
    runVersion += 1
    return true
  }

  function schedule(version: number, delay = intervalMs) {
    if (version !== runVersion) return
    clearTimer()
    timer = setTimeout(() => void poll(version), delay)
  }

  function hasTimedOut() {
    return startedAt.value !== undefined && Date.now() - startedAt.value >= timeoutMs
  }

  function invokeCallback(callback: AiPollingOptions['onSuccess'] | AiPollingOptions['onFailure'], result: AiAnalysis) {
    if (!callback) return
    void Promise.resolve(callback(result)).catch(() => undefined)
  }

  async function poll(version: number) {
    if (version !== runVersion) return
    if (hasTimedOut()) {
      error.value = new ApiError('AI 解析等待超时，可稍后重新查询', { code: -1 })
      settle(version, 'timeout')
      return
    }

    try {
      const result = await aiApi.analysis(resolveQuestionId(), { silent: true })
      if (version !== runVersion) return
      analysis.value = result
      consecutiveErrors.value = 0

      if (!result || result.status === 0) {
        schedule(version)
        return
      }
      if (result.status === 1) {
        if (settle(version, 'success')) invokeCallback(options.onSuccess, result)
        return
      }
      if (settle(version, 'failed')) invokeCallback(options.onFailure, result)
    } catch (cause) {
      if (version !== runVersion) return
      const normalized = toApiError(cause, 'AI 解析状态查询失败')
      error.value = normalized
      consecutiveErrors.value += 1
      const retryable = normalized.code === -1 || normalized.code >= 500
      if (!retryable || normalized.isUnauthorized || consecutiveErrors.value >= maxConsecutiveErrors) {
        settle(version, 'error')
        return
      }
      const retryDelay = Math.min(intervalMs * 2 ** (consecutiveErrors.value - 1), 8_000)
      schedule(version, retryDelay)
    }
  }

  function start() {
    runVersion += 1
    clearTimer()
    error.value = null
    consecutiveErrors.value = 0
    startedAt.value = Date.now()
    state.value = 'polling'
    const version = runVersion
    void poll(version)
  }

  function stop() {
    runVersion += 1
    clearTimer()
    state.value = 'idle'
    startedAt.value = undefined
    consecutiveErrors.value = 0
  }

  async function trigger() {
    stop()
    state.value = 'triggering'
    error.value = null
    try {
      await aiApi.analyze(resolveQuestionId())
      analysis.value = null
      start()
    } catch (cause) {
      const normalized = toApiError(cause, 'AI 解析触发失败')
      error.value = normalized
      state.value = 'error'
      throw normalized
    }
  }

  async function sync() {
    stop()
    error.value = null
    try {
      const result = await aiApi.analysis(resolveQuestionId(), { silent: true })
      analysis.value = result
      if (result?.status === 0) start()
      else if (result?.status === 1) state.value = 'success'
      else if (result?.status === 2) state.value = 'failed'
      return result
    } catch (cause) {
      const normalized = toApiError(cause, 'AI 解析状态查询失败')
      error.value = normalized
      state.value = 'error'
      throw normalized
    }
  }

  onScopeDispose(stop)

  return {
    analysis,
    state,
    error,
    consecutiveErrors,
    isPolling,
    start,
    stop,
    trigger,
    sync,
  }
}
