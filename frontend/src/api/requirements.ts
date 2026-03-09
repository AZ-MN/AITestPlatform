import http from './http'
import type { Requirement } from './types'

export const requirementApi = {
  list: (project_id: number) =>
    http.get<any, Requirement[]>('/requirements', { params: { project_id } }),

  get: (id: number) => http.get<any, Requirement>(`/requirements/${id}`),

  createText: (
    data: { project_id: number; title: string; content: string },
    useAi = true,
    provider?: string,
    parsePrompt?: string
  ) =>
    http.post<any, Requirement>(
      `/requirements/text?use_ai=${useAi}${provider ? `&ai_provider=${provider}` : ''}${parsePrompt ? `&parse_prompt=${encodeURIComponent(parsePrompt)}` : ''}`,
      data
    ),

  upload: (formData: FormData) =>
    http.post<any, Requirement>('/requirements/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }),

  update: (id: number, data: any) => http.put<any, Requirement>(`/requirements/${id}`, data),

  reparse: (id: number, payload: { use_ai: boolean; ai_provider?: string; parse_prompt?: string }) =>
    http.post<any, Requirement>(
      `/requirements/${id}/reparse?use_ai=${payload.use_ai}${payload.ai_provider ? `&ai_provider=${payload.ai_provider}` : ''}${payload.parse_prompt ? `&parse_prompt=${encodeURIComponent(payload.parse_prompt)}` : ''}`
    ),

  remove: (id: number) => http.delete(`/requirements/${id}`),
}
