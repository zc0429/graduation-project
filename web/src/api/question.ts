import request, { requestAuthenticatedFile, saveDownloadedFile } from '@/utils/request'
import type { PageData, Question, QuestionPayload } from '@/types/api'

function buildExportUrl(subjectId?: number, knowledgePointId?: number) {
  const params = new URLSearchParams()
  if (subjectId !== undefined) params.set('subjectId', String(subjectId))
  if (knowledgePointId !== undefined) params.set('knowledgePointId', String(knowledgePointId))
  const query = params.toString()
  return `/api/question/export${query ? `?${query}` : ''}`
}

export const questionApi = {
  create: (data: QuestionPayload) => request.post<unknown, number>('/question', data),
  page: (params: { pageNum: number; pageSize: number; subjectId?: number; knowledgePointId?: number }) =>
    request.get<unknown, PageData<Question>>('/question/page', { params }),
  detail: (id: number) => request.get<unknown, Question>(`/question/${id}`),
  update: (id: number, data: QuestionPayload) => request.put<unknown, void>(`/question/${id}`, data),
  remove: (id: number) => request.delete<unknown, void>(`/question/${id}`),
  exportUrl: buildExportUrl,
  download: async (subjectId?: number, knowledgePointId?: number) => {
    const file = await requestAuthenticatedFile(buildExportUrl(subjectId, knowledgePointId), '错题本.xlsx')
    saveDownloadedFile(file)
    return file.fileName
  },
}
