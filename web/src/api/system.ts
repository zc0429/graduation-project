import request from '@/utils/request'
import type { PageData } from '@/types/api'

/** RBAC 权限管理接口（Sa-Token + role / permission / user_role / role_permission 四表） */

export interface RoleRecord {
  id: number
  roleName: string
  roleKey: string
  sort?: number
  status: number
  remark?: string
  createTime?: string
  updateTime?: string
}

export interface RolePayload {
  roleName: string
  roleKey: string
  sort?: number
  status?: number
  remark?: string
}

export interface PermissionRecord {
  id: number
  parentId: number
  name: string
  permissionKey: string
  type: string
  path?: string
  sort?: number
  status: number
  createTime?: string
  updateTime?: string
}

export interface PermissionPayload {
  parentId?: number
  name: string
  permissionKey: string
  type: string
  path?: string
  sort?: number
  status?: number
}

export const roleApi = {
  page: (params: { pageNum: number; pageSize: number; keyword?: string }) =>
    request.get<unknown, PageData<RoleRecord>>('/system/role/page', { params }),
  list: () =>
    request
      .get<unknown, PageData<RoleRecord>>('/system/role/page', { params: { pageNum: 1, pageSize: 100 } })
      .then((data) => data.records),
  get: (id: number) => request.get<unknown, RoleRecord>(`/system/role/${id}`),
  create: (data: RolePayload) => request.post<unknown, number>('/system/role', data),
  update: (id: number, data: RolePayload) => request.put<unknown, void>(`/system/role/${id}`, data),
  remove: (id: number) => request.delete<unknown, void>(`/system/role/${id}`),
  permissionIds: (id: number) => request.get<unknown, number[]>(`/system/role/${id}/permission-ids`),
  assignPermissions: (id: number, ids: number[]) =>
    request.put<unknown, void>(`/system/role/${id}/permissions`, { ids }),
}

export const permissionApi = {
  list: () => request.get<unknown, PermissionRecord[]>('/system/permission/list'),
  get: (id: number) => request.get<unknown, PermissionRecord>(`/system/permission/${id}`),
  create: (data: PermissionPayload) => request.post<unknown, number>('/system/permission', data),
  update: (id: number, data: PermissionPayload) => request.put<unknown, void>(`/system/permission/${id}`, data),
  remove: (id: number) => request.delete<unknown, void>(`/system/permission/${id}`),
}

export const userRoleApi = {
  roleIdsOfUser: (userId: number) => request.get<unknown, number[]>(`/system/user-role/user/${userId}`),
  assignRoles: (userId: number, ids: number[]) =>
    request.put<unknown, void>(`/system/user-role/user/${userId}`, { ids }),
}
