import request from '@/utils/request'
import type { KnowledgePointPayload, KpNode, Subject, SubjectPayload } from '@/types/api'

export const subjectApi = {
  list: () => request.get<unknown, Subject[]>('/subject/list'),
  add: (data: SubjectPayload) => request.post<unknown, number>('/subject', data),
  update: (id: number, data: SubjectPayload) => request.put<unknown, void>(`/subject/${id}`, data),
  remove: (id: number) => request.delete<unknown, void>(`/subject/${id}`),
}

export const kpApi = {
  tree: (subjectId?: number) =>
    request.get<unknown, KpNode[]>('/knowledge-point/tree', {
      params: subjectId === undefined ? undefined : { subjectId },
    }),
  add: (data: KnowledgePointPayload) => request.post<unknown, number>('/knowledge-point', data),
  remove: (id: number) => request.delete<unknown, void>(`/knowledge-point/${id}`),
}
