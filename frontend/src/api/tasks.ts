import http from './http'
import type { GenerateRequest, TaskJob } from './types'

export const taskApi = {
  list: (params?: { project_id?: number; status?: string }) =>
    http.get<any, TaskJob[]>('/tasks', { params }),

  createGenerate: (payload: GenerateRequest) =>
    http.post<any, TaskJob>('/tasks/generate', { payload }),

  createReparse: (data: { requirement_id: number; use_ai: boolean; ai_provider?: string; parse_prompt?: string }) =>
    http.post<any, TaskJob>('/tasks/reparse', data),

  stop: (id: number) => http.post(`/tasks/${id}/stop`),
  retry: (id: number) => http.post<any, TaskJob>(`/tasks/${id}/retry`),
}
