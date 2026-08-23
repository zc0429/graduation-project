import request from '@/utils/request'
import type { AiAnalysis, ApiCallOptions, Question, VariantQuestion } from '@/types/api'

const VARIANT_GENERATION_TIMEOUT_MS = 60_000

export const aiApi = {
  analyze: (questionId: number) => request.post<unknown, void>(`/ai/analyze/${questionId}`),
  analysis: (questionId: number, options: ApiCallOptions = {}) =>
    request.get<unknown, AiAnalysis | null>(`/ai/analysis/${questionId}`, { silent: options.silent }),
}

export const recommendApi = {
  similar: (questionId: number) =>
    request.get<unknown, Question[]>('/recommend/similar', { params: { questionId } }),
}

export const variantApi = {
  generate: (questionId: number) =>
    request.post<unknown, VariantQuestion[]>(`/variant/generate/${questionId}`, undefined, {
      timeout: VARIANT_GENERATION_TIMEOUT_MS,
    }),
  list: (questionId: number) =>
    request.get<unknown, VariantQuestion[]>('/variant/list', { params: { questionId } }),
}
