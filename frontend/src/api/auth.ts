import http from './http'
import type { User } from './types'

export const authApi = {
  login: (data: { username: string; password: string }) =>
    http.post<any, { access_token: string; user: User }>('/auth/login', data),

  register: (data: { username: string; email: string; password: string; full_name?: string }) =>
    http.post<any, User>('/auth/register', data),

  me: () => http.get<any, User>('/auth/me'),

  updateMe: (data: any) => http.put<any, User>('/auth/me', data),

  listUsers: () => http.get<any, User[]>('/auth/users'),
}
