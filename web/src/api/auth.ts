import request from '@/utils/request'
import type { LoginPayload, LoginResult, RegisterPayload } from '@/types/api'

export const authApi = {
  register: (data: RegisterPayload) => request.post<unknown, number>('/auth/register', data),
  login: (data: LoginPayload) => request.post<unknown, LoginResult>('/auth/login', data),
}
