import http from './http'
import type { TestCase, GenerateRequest, PageResult } from './types'

export const caseApi = {
  list: (params: any) => http.get<any, PageResult<TestCase>>('/cases', { params }),

  get: (id: number) => http.get<any, TestCase>(`/cases/${id}`),

  create: (data: any) => http.post<any, TestCase>('/cases', data),

  update: (id: number, data: any) => http.put<any, TestCase>(`/cases/${id}`, data),

  remove: (id: number) => http.delete(`/cases/${id}`),

  batchDelete: (ids: number[]) => http.delete('/cases', { data: ids }),

  generate: (data: GenerateRequest) => http.post('/cases/generate', data),

  rate: (id: number, data: { rating: number; feedback?: string }) =>
    http.post(`/cases/${id}/rating`, data),

  export: (data: { project_id: number; case_ids?: number[]; format: string; requirement_id?: number }) =>
    http.post('/cases/export', data, { responseType: 'blob' }),

  stats: (project_id: number) =>
    http.get<any, any>('/cases/stats/summary', { params: { project_id } }),
}
