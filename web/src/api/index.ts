import request from '@/utils/request'

/* ============ 类型定义（与后端实体/VO 对应） ============ */

export interface Subject {
  id: number
  name: string
  code?: string
  sort: number
}

export interface KpNode {
  id: number
  subjectId: number
  name: string
  children: KpNode[]
}

export interface Question {
  id: number
  userId: number
  subjectId: number
  knowledgePointId?: number
  stem: string
  answer?: string
  source?: string
  imageUrl?: string
  difficulty?: number
  mastery: number
  createTime: string
  updateTime: string
}

export interface AiAnalysis {
  id: number
  questionId: number
  knowledgePointId?: number
  errorCause?: string
  analysis?: string
  referenceIds?: string
  llmModel?: string
  status: number // 0 生成中 1 成功 2 失败
  createTime: string
}

export interface VariantQuestion {
  id: number
  questionId: number
  stem: string
  answer?: string
  difficulty?: number
}

export interface ReviewPlanItem {
  id: number
  questionId: number
  reviewStage: number
  planDate: string
  status: number // 0 待复习 1 已完成 2 已过期
  subjectId?: number
  stemSummary?: string
  mastery?: number
}

export interface PracticeRecord {
  id: number
  questionId?: number
  variantId?: number
  userAnswer?: string
  isCorrect: number
  duration?: number
  createTime: string
}

export interface Message {
  id: number
  type: string
  title: string
  content?: string
  isRead: number
  createTime: string
}

export interface Announcement {
  id: number
  title: string
  content?: string
  createTime: string
}

export interface PageData<T> {
  records: T[]
  total: number
  current: number
  size: number
}

export interface WeeklyReport {
  weekStart: string
  newQuestionCount: number
  totalQuestionCount: number
  reviewFinishedCount: number
  reviewTotalCount: number
  masteryAvg: number
  knowledgeMastery: { knowledgePointId: number; name: string; mastery: number; questionCount: number }[]
  weakPoints: { knowledgePointId: number; name: string; mastery: number; questionCount: number }[]
  dailyNewQuestions: { date: string; count: number }[]
  dailyPractices: { date: string; count: number }[]
}

/* ============ 认证与用户 ============ */

export const authApi = {
  register: (data: { username: string; password: string; nickname?: string }) =>
    request.post<unknown, number>('/auth/register', data),
  login: (data: { username: string; password: string }) =>
    request.post<unknown, { token: string; user: import('@/store/user').UserInfo }>('/auth/login', data),
}

export const userApi = {
  profile: () => request.get<unknown, import('@/store/user').UserInfo>('/user/profile'),
  updateProfile: (data: { nickname?: string; email?: string; className?: string }) =>
    request.put<unknown, void>('/user/profile', data),
  page: (params: { pageNum: number; pageSize: number; role?: string; keyword?: string }) =>
    request.get<unknown, PageData<import('@/store/user').UserInfo & { createTime: string }>>('/user/page', { params }),
  remove: (id: number) => request.delete<unknown, void>(`/user/${id}`),
}

/* ============ 科目与知识点 ============ */

export const subjectApi = {
  list: () => request.get<unknown, Subject[]>('/subject/list'),
  add: (data: { name: string; code?: string; sort?: number }) => request.post<unknown, number>('/subject', data),
  update: (id: number, data: { name: string; code?: string; sort?: number }) =>
    request.put<unknown, void>(`/subject/${id}`, data),
}

export const kpApi = {
  tree: (subjectId?: number) =>
    request.get<unknown, KpNode[]>('/knowledge-point/tree', { params: { subjectId } }),
  add: (data: { subjectId: number; parentId: number; name: string; sort?: number }) =>
    request.post<unknown, number>('/knowledge-point', data),
  remove: (id: number) => request.delete<unknown, void>(`/knowledge-point/${id}`),
}

/* ============ 错题 ============ */

export interface QuestionPayload {
  subjectId: number
  stem: string
  answer?: string
  source?: string
  imageBase64?: string
}

export const questionApi = {
  create: (data: QuestionPayload) => request.post<unknown, number>('/question', data),
  page: (params: { pageNum: number; pageSize: number; subjectId?: number; knowledgePointId?: number }) =>
    request.get<unknown, PageData<Question>>('/question/page', { params }),
  detail: (id: number) => request.get<unknown, Question>(`/question/${id}`),
  update: (id: number, data: QuestionPayload) => request.put<unknown, void>(`/question/${id}`, data),
  remove: (id: number) => request.delete<unknown, void>(`/question/${id}`),
  exportUrl: (subjectId?: number, knowledgePointId?: number) => {
    const params = new URLSearchParams()
    if (subjectId) params.set('subjectId', String(subjectId))
    if (knowledgePointId) params.set('knowledgePointId', String(knowledgePointId))
    return `/api/question/export?${params.toString()}`
  },
}

/* ============ AI 能力 ============ */

export const aiApi = {
  analyze: (questionId: number) => request.post<unknown, void>(`/ai/analyze/${questionId}`),
  analysis: (questionId: number) => request.get<unknown, AiAnalysis | null>(`/ai/analysis/${questionId}`),
}

export const recommendApi = {
  similar: (questionId: number) => request.get<unknown, Question[]>('/recommend/similar', { params: { questionId } }),
}

export const variantApi = {
  generate: (questionId: number) => request.post<unknown, VariantQuestion[]>(`/variant/generate/${questionId}`),
  list: (questionId: number) => request.get<unknown, VariantQuestion[]>('/variant/list', { params: { questionId } }),
}

/* ============ 学习闭环 ============ */

export const reviewPlanApi = {
  today: () => request.get<unknown, ReviewPlanItem[]>('/review-plan/today'),
  finish: (id: number) => request.put<unknown, void>(`/review-plan/${id}/finish`),
}

export const practiceApi = {
  submit: (data: { questionId?: number; variantId?: number; userAnswer?: string; isCorrect: number; duration?: number }) =>
    request.post<unknown, number>('/practice', data),
  page: (params: { pageNum: number; pageSize: number }) =>
    request.get<unknown, PageData<PracticeRecord>>('/practice/page', { params }),
}

export const reportApi = {
  weekly: () => request.get<unknown, WeeklyReport>('/report/weekly'),
  generate: () => request.post<unknown, WeeklyReport>('/report/generate'),
}

export const messageApi = {
  page: (params: { pageNum: number; pageSize: number; isRead?: number }) =>
    request.get<unknown, PageData<Message>>('/message/page', { params }),
  markRead: (id: number) => request.put<unknown, void>(`/message/${id}/read`),
  unreadCount: () => request.get<unknown, number>('/message/unread-count'),
}

export const announcementApi = {
  list: () => request.get<unknown, Announcement[]>('/announcement/list'),
  publish: (data: { title: string; content?: string }) => request.post<unknown, number>('/announcement', data),
}
