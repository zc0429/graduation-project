import request from '@/utils/request'
import type { PageData, PracticePayload, PracticeRecord, ReviewPlanItem, WeeklyReport } from '@/types/api'

export const reviewPlanApi = {
  today: () => request.get<unknown, ReviewPlanItem[]>('/review-plan/today'),
  finish: (id: number) => request.put<unknown, void>(`/review-plan/${id}/finish`),
}

export const practiceApi = {
  submit: (data: PracticePayload) => request.post<unknown, number>('/practice', data),
  page: (params: { pageNum: number; pageSize: number }) =>
    request.get<unknown, PageData<PracticeRecord>>('/practice/page', { params }),
}

export const reportApi = {
  weekly: () => request.get<unknown, WeeklyReport>('/report/weekly'),
  generate: () => request.post<unknown, WeeklyReport>('/report/generate'),
}

export interface KnowledgeResource {
  id: number
  questionId: number
  knowledgePointId?: number
  content: string
  reused: boolean
}
export interface PracticeResource {
  questionId: number | null
  variantId: number | null
  stem: string
  answer?: string
  difficulty?: number
  source: 'original' | 'existing' | 'generated'
}
export const learningApi = {
  knowledge: (questionId: number) => request.post<unknown, KnowledgeResource>(`/learning/knowledge/${questionId}`, undefined, { timeout: 180_000, silent: true }),
  next: (questionId: number) => request.post<unknown, PracticeResource>(`/learning/practice/next/${questionId}`, undefined, { timeout: 180_000, silent: true }),
  progress: (questionId: number) => request.get<unknown, { originalPracticed: boolean; practicedVariantIds: number[] }>(`/learning/practice/progress/${questionId}`),
}
