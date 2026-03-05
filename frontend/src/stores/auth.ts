import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { User } from '@/types'
import { authApi } from '@/api/modules'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('access_token'))

  const login = async (username: string, password: string) => {
    const res: any = await authApi.login(username, password)
    token.value = res.access_token
    user.value = res.user
    localStorage.setItem('access_token', res.access_token)
    localStorage.setItem('user_info', JSON.stringify(res.user))
  }

  const logout = () => {
    token.value = null
    user.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('user_info')
  }

  const loadUserFromStorage = () => {
    const stored = localStorage.getItem('user_info')
    if (stored) {
      try { user.value = JSON.parse(stored) } catch {}
    }
  }

  return { user, token, login, logout, loadUserFromStorage }
})
