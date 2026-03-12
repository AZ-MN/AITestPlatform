import http from './http'
import type { Project } from './types'

export const projectApi = {
  list: () => http.get<any, Project[]>('/projects'),
  get: (id: number) => http.get<any, Project>(`/projects/${id}`),
  create: (data: { name: string; description?: string; icon?: string }) =>
    http.post<any, Project>('/projects', data),
  update: (id: number, data: any) => http.put<any, Project>(`/projects/${id}`, data),
  remove: (id: number) => http.delete(`/projects/${id}`),
  archive: (id: number) => http.patch(`/projects/${id}/archive`),
  unarchive: (id: number) => http.patch(`/projects/${id}/unarchive`),
  members: (id: number) => http.get<any, any[]>(`/projects/${id}/members`),
  addMember: (id: number, data: { user_id: number; role: string }) =>
    http.post(`/projects/${id}/members`, data),
}
