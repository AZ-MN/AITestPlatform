import http from './http'
import type { Project, ProjectMember } from './types'

export const projectApi = {
  list: () => http.get<any, Project[]>('/projects'),
  get: (id: number) => http.get<any, Project>(`/projects/${id}`),
  create: (data: { name: string; description?: string; icon?: string }) =>
    http.post<any, Project>('/projects', data),
  update: (id: number, data: any) => http.put<any, Project>(`/projects/${id}`, data),
  purge: (id: number) => http.post(`/projects/${id}/purge`),
  remove: (id: number) => http.delete(`/projects/${id}`),
  setStatus: (id: number, status: 'active' | 'archived') =>
    http.put<any, Project>(`/projects/${id}`, { status }),
  archive: (id: number) => http.patch(`/projects/${id}/archive`),
  unarchive: (id: number) => http.patch(`/projects/${id}/unarchive`),
  members: (id: number) => http.get<any, ProjectMember[]>(`/projects/${id}/members`),
  addMember: (id: number, data: { user_id: number; role: string }) =>
    http.post(`/projects/${id}/members`, data),
  removeMember: (id: number, memberId: number) => http.delete(`/projects/${id}/members/${memberId}`),
}
