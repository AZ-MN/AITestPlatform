import http from './http'
import type { AIModelConfig } from './types'

export const modelApi = {
  providers: () => http.get<any, any[]>('/models/providers'),
  list: () => http.get<any, AIModelConfig[]>('/models'),
  add: (data: any) => http.post<any, AIModelConfig>('/models', data),
  update: (id: number, data: any) => http.put<any, AIModelConfig>(`/models/${id}`, data),
  remove: (id: number) => http.delete(`/models/${id}`),
  test: (id: number) => http.post<any, { ok: boolean; reply?: string; error?: string }>(`/models/${id}/test`),
}
