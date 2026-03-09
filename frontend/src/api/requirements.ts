import http from './http'
import type { Requirement } from './types'

export const requirementApi = {
  list: (project_id: number) =>
    http.get<any, Requirement[]>('/requirements', { params: { project_id } }),

  get: (id: number) => http.get<any, Requirement>(`/requirements/${id}`),

  createText: (data: { project_id: number; title: string; content: string }, useAi = true, provider?: string) =>
    http.post<any, Requirement>(`/requirements/text?use_ai=${useAi}${provider ? `&ai_provider=${provider}` : ''}`, data),

  upload: (formData: FormData) =>
    http.post<any, Requirement>('/requirements/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }),

  update: (id: number, data: any) => http.put<any, Requirement>(`/requirements/${id}`, data),

  remove: (id: number) => http.delete(`/requirements/${id}`),
}
