import request from './index'

export const authApi = {
  login: (username: string, password: string) =>
    request.post('/auth/login', { username, password }),
  getMe: () => request.get('/auth/me'),
}

export const userApi = {
  list: (params?: any) => request.get('/users/', { params }),
  create: (data: any) => request.post('/users/', data),
  update: (id: number, data: any) => request.put(`/users/${id}`, data),
  delete: (id: number) => request.delete(`/users/${id}`),
  resetPassword: (id: number, newPassword: string) =>
    request.post(`/users/${id}/reset-password`, null, { params: { new_password: newPassword } }),
  listRoles: () => request.get('/users/roles/'),
  createRole: (data: any) => request.post('/users/roles/', data),
}

export const projectApi = {
  list: (params?: any) => request.get('/projects/', { params }),
  create: (data: any) => request.post('/projects/', data),
  get: (id: number) => request.get(`/projects/${id}`),
  update: (id: number, data: any) => request.put(`/projects/${id}`, data),
  delete: (id: number) => request.delete(`/projects/${id}`),
  listIterations: (projectId: number) => request.get(`/projects/${projectId}/iterations`),
  createIteration: (projectId: number, data: any) => request.post(`/projects/${projectId}/iterations`, data),
}

export const requirementApi = {
  list: (params: any) => request.get('/requirements/', { params }),
  create: (data: any) => request.post('/requirements/', data),
  get: (id: number) => request.get(`/requirements/${id}`),
  aiParse: (id: number) => request.post(`/requirements/${id}/ai-parse`),
  upload: (projectId: number, file: File) => {
    const form = new FormData()
    form.append('file', file)
    return request.post('/requirements/upload', form, { params: { project_id: projectId } })
  },
}

export const testcaseApi = {
  list: (params: any) => request.get('/testcases/', { params }),
  create: (data: any) => request.post('/testcases/', data),
  update: (id: number, data: any) => request.put(`/testcases/${id}`, data),
  delete: (id: number) => request.delete(`/testcases/${id}`),
  aiGenerate: (data: any) => request.post('/testcases/ai-generate', data),
}

export const apitestApi = {
  listDefinitions: (params: any) => request.get('/apitest/definitions', { params }),
  createDefinition: (data: any) => request.post('/apitest/definitions', data),
  deleteDefinition: (id: number) => request.delete(`/apitest/definitions/${id}`),
  importSwagger: (data: any) => request.post('/apitest/import/swagger', data),
  listCases: (params: any) => request.get('/apitest/cases', { params }),
  createCase: (data: any) => request.post('/apitest/cases', data),
  aiGenerateCases: (data: any) => request.post('/apitest/cases/ai-generate', data),
  debug: (data: any) => request.post('/apitest/debug', data),
}

export const automationApi = {
  listScripts: (params: any) => request.get('/automation/scripts', { params }),
  createScript: (data: any) => request.post('/automation/scripts', data),
  updateScript: (id: number, data: any) => request.put(`/automation/scripts/${id}`, data),
  aiGenerateScript: (data: any) => request.post('/automation/scripts/ai-generate', data),
  listTasks: (params: any) => request.get('/automation/tasks', { params }),
  createTask: (data: any) => request.post('/automation/tasks', data),
}

export const defectApi = {
  list: (params: any) => request.get('/defects/', { params }),
  create: (data: any) => request.post('/defects/', data),
  get: (id: number) => request.get(`/defects/${id}`),
  update: (id: number, data: any) => request.put(`/defects/${id}`, data),
  changeStatus: (id: number, data: any) => request.post(`/defects/${id}/status`, data),
  aiAnalyze: (data: any) => request.post('/defects/ai-analyze', data),
}

export const reportApi = {
  getDashboard: (projectId: number) => request.get('/reports/dashboard', { params: { project_id: projectId } }),
  generateAiReport: (data: any) => request.post('/reports/ai-report', data),
}

export const testdataApi = {
  getTypes: () => request.get('/testdata/types'),
  generate: (data: any) => request.post('/testdata/generate', data),
  generateBusiness: (data: any) => request.post('/testdata/generate/business', data),
  mask: (data: any) => request.post('/testdata/mask', data),
}

export const llmConfigApi = {
  list: () => request.get('/llm-configs/'),
  create: (data: any) => request.post('/llm-configs/', data),
  test: (id: number) => request.post(`/llm-configs/${id}/test`),
  delete: (id: number) => request.delete(`/llm-configs/${id}`),
}
