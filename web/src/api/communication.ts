import request from '@/utils/request'
import type { Announcement, AnnouncementPayload, Message, PageData } from '@/types/api'

export const messageApi = {
  page: (params: { pageNum: number; pageSize: number; isRead?: number }) =>
    request.get<unknown, PageData<Message>>('/message/page', { params }),
  markRead: (id: number) => request.put<unknown, void>(`/message/${id}/read`),
  unreadCount: () => request.get<unknown, number>('/message/unread-count'),
}

export const announcementApi = {
  list: () => request.get<unknown, Announcement[]>('/announcement/list'),
  publish: (data: AnnouncementPayload) => request.post<unknown, number>('/announcement', data),
}
