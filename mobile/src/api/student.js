import { ApiError, logout, request, saveToken } from './request.js'

function assertStudent(user) {
  if (user?.role === 'student') return user
  logout()
  throw new ApiError('小程序仅支持学生账号，请在 PC 端使用教师或管理员账号', 403)
}

export async function login(username, password) {
  const session = await request('/auth/login', {
    method: 'POST',
    data: { username, password },
    authenticated: false,
  })
  const user = assertStudent(session.user)
  saveToken(session.token)
  return user
}

export async function profile() {
  return assertStudent(await request('/user/profile'))
}

export const listSubjects = () => request('/subject/list')
export const weeklyReport = () => request('/report/weekly')
export const questions = (pageNum, pageSize, subjectId) => request('/question/page', {
  data: { pageNum, pageSize, ...(subjectId == null ? {} : { subjectId }) },
})
export const question = (id) => request(`/question/${id}`)
export const saveQuestion = (data) => request('/question', { method: 'POST', data })
export const recognizeQuestion = (imageBase64) => request('/question-recognition/recognize', {
  method: 'POST',
  data: { imageBase64 },
  timeout: 120000,
})
export const readAnalysis = (id) => request(`/ai/analysis/${id}`)
export const startAnalysis = (id) => request(`/ai/analyze/${id}`, { method: 'POST' })
export const readKnowledge = (id) => request(`/learning/knowledge/${id}`, { method: 'POST', timeout: 180000 })
export const nextPractice = (id) => request(`/learning/practice/next/${id}`, { method: 'POST', timeout: 180000 })
export const savePractice = (data) => request('/practice', { method: 'POST', data })
export const dueReviews = () => request('/review-plan/today')
export const finishReview = (id) => request(`/review-plan/${id}/finish`, { method: 'PUT' })
