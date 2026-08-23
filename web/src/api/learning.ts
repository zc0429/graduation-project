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
