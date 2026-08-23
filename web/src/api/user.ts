import request from '@/utils/request'
import type { ApiCallOptions, PageData, ProfileUpdatePayload, UserInfo, UserRecord } from '@/types/api'

export const userApi = {
  profile: (options: ApiCallOptions = {}) =>
    request.get<unknown, UserInfo>('/user/profile', { silent: options.silent }),
  updateProfile: (data: ProfileUpdatePayload) => request.put<unknown, void>('/user/profile', data),
  page: (params: { pageNum: number; pageSize: number; role?: string; keyword?: string }) =>
    request.get<unknown, PageData<UserRecord>>('/user/page', { params }),
  remove: (id: number) => request.delete<unknown, void>(`/user/${id}`),
}
