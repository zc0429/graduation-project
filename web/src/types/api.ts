export type UserRole = 'student' | 'teacher' | 'admin'

export interface UserInfo {
  id: number
  username: string
  nickname: string
  role: UserRole | string
  className?: string
  email?: string
}

export interface UserRecord extends UserInfo {
  createTime: string
  updateTime?: string
}

export interface Subject {
  id: number
  name: string
  code?: string
  sort: number
  createTime?: string
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
  status: 0 | 1 | 2
  createTime: string
}

export interface VariantQuestion {
  id: number
  questionId: number
  stem: string
  answer?: string
  difficulty?: number
  createTime?: string
}

export interface ReviewPlanItem {
  id: number
  questionId: number
  reviewStage: number
  planDate: string
  status: 0 | 1 | 2
  subjectId?: number
  stemSummary?: string
  mastery?: number
}

export interface PracticeRecord {
  id: number
  questionId?: number
  variantId?: number
  userAnswer?: string
  isCorrect: 0 | 1
  duration?: number
  createTime: string
}

export interface Message {
  id: number
  type: 'review_remind' | 'report' | 'system' | string
  title: string
  content?: string
  isRead: 0 | 1
  createTime: string
}

export interface Announcement {
  id: number
  title: string
  content?: string
  publisherId?: number
  createTime: string
}

export interface PageData<T> {
  records: T[]
  total: number
  current: number
  size: number
  pages?: number
}

export interface RestResponse<T = unknown> {
  code: number
  message: string
  data: T
}

export interface KnowledgeMastery {
  knowledgePointId: number
  name: string
  mastery: number
  questionCount: number
}

export interface DateCount {
  date: string
  count: number
}

export interface WeeklyReport {
  weekStart: string
  newQuestionCount: number
  totalQuestionCount: number
  reviewFinishedCount: number
  reviewTotalCount: number
  masteryAvg: number
  knowledgeMastery: KnowledgeMastery[]
  weakPoints: KnowledgeMastery[]
  dailyNewQuestions: DateCount[]
  dailyPractices: DateCount[]
}

export interface RegisterPayload {
  username: string
  password: string
  nickname?: string
}

export interface LoginPayload {
  username: string
  password: string
}

export interface LoginResult {
  token: string
  user: UserInfo
}

export interface ProfileUpdatePayload {
  nickname?: string
  email?: string
  className?: string
}

export interface SubjectPayload {
  name: string
  code?: string
  sort?: number
}

export interface KnowledgePointPayload {
  subjectId: number
  parentId: number
  name: string
  sort?: number
}

export interface QuestionPayload {
  subjectId: number
  stem: string
  answer?: string
  source?: string
  imageBase64?: string
}

export interface QuestionRecognitionResult {
  subjectId?: number | null
  subjectName?: string | null
  stem: string
  studentAnswer?: string | null
  source?: string | null
}

export type PracticeTarget =
  | { questionId: number; variantId?: never }
  | { questionId?: never; variantId: number }

/**
 * The backend DTO accepts optional IDs and performs ownership validation at
 * runtime. New forms should construct a `PracticeTarget` before submission.
 */
export interface PracticePayload {
  questionId?: number
  variantId?: number
  userAnswer?: string
  /** Backend validates that the numeric value is exactly 0 or 1. */
  isCorrect: number
  duration?: number
}

export interface AnnouncementPayload {
  title: string
  content?: string
}

export interface ApiCallOptions {
  silent?: boolean
}
