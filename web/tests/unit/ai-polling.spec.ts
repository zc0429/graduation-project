import { effectScope, nextTick, type EffectScope } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { AiAnalysis } from '@/types/api'
import { ApiError } from '@/utils/api-error'

const aiMocks = vi.hoisted(() => ({
  analyze: vi.fn(),
  analysis: vi.fn(),
}))

vi.mock('@/api/ai', () => ({ aiApi: aiMocks }))

import { useAiAnalysisPolling } from '@/composables/useAiAnalysisPolling'

const pending: AiAnalysis = {
  id: 1,
  questionId: 201,
  status: 0,
  createTime: '2026-08-23 12:00:00',
}

const success: AiAnalysis = {
  ...pending,
  status: 1,
  analysis: '解析完成',
  errorCause: '遗漏约束',
      llmModel: 'mock-model',
}

let scope: EffectScope | undefined

function createPolling(options: Parameters<typeof useAiAnalysisPolling>[1] = {}) {
  scope = effectScope()
  return scope.run(() => useAiAnalysisPolling(201, options))!
}

describe('useAiAnalysisPolling', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    aiMocks.analyze.mockReset()
    aiMocks.analysis.mockReset()
  })

  afterEach(() => {
    scope?.stop()
    scope = undefined
    vi.useRealTimers()
  })

  it('syncs an already completed analysis without scheduling another request', async () => {
    aiMocks.analysis.mockResolvedValue(success)
    const polling = createPolling()

    await polling.sync()

    expect(polling.state.value).toBe('success')
    expect(polling.analysis.value).toEqual(success)
    expect(aiMocks.analysis).toHaveBeenCalledTimes(1)
  })

  it('triggers, polls without overlap, and settles on success', async () => {
    aiMocks.analyze.mockResolvedValue(undefined)
    aiMocks.analysis.mockResolvedValueOnce(pending).mockResolvedValueOnce(success)
    const onSuccess = vi.fn()
    const polling = createPolling({ intervalMs: 500, timeoutMs: 2_000, onSuccess })

    await polling.trigger()
    await nextTick()
    expect(polling.state.value).toBe('polling')
    expect(aiMocks.analysis).toHaveBeenCalledTimes(1)

    await vi.advanceTimersByTimeAsync(500)

    expect(polling.state.value).toBe('success')
    expect(polling.analysis.value).toEqual(success)
    expect(onSuccess).toHaveBeenCalledWith(success)
    expect(aiMocks.analysis).toHaveBeenCalledTimes(2)
  })

  it('stops after the configured consecutive retry limit', async () => {
    aiMocks.analysis.mockRejectedValue(new ApiError('模型服务暂不可用', { code: 503 }))
    const polling = createPolling({ intervalMs: 500, timeoutMs: 5_000, maxConsecutiveErrors: 2 })

    polling.start()
    await nextTick()
    expect(polling.state.value).toBe('polling')

    await vi.advanceTimersByTimeAsync(500)

    expect(polling.state.value).toBe('error')
    expect(polling.consecutiveErrors.value).toBe(2)
    expect(polling.error.value?.message).toBe('模型服务暂不可用')
  })

  it('exposes a bounded timeout for a perpetually pending analysis', async () => {
    aiMocks.analysis.mockResolvedValue(pending)
    const polling = createPolling({ intervalMs: 500, timeoutMs: 1_000 })

    polling.start()
    await nextTick()
    await vi.advanceTimersByTimeAsync(1_000)

    expect(polling.state.value).toBe('timeout')
    expect(polling.error.value?.message).toContain('等待超时')
  })
})
