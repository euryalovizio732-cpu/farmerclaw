import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

const http = axios.create({ baseURL: '/api', timeout: 30000 })

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('fc_token') || '')
  const user = ref(JSON.parse(localStorage.getItem('fc_user') || 'null'))

  const isLoggedIn = computed(() => !!token.value && !!user.value)
  const tierLabel = computed(() => user.value?.tier_label || '未登录')
  const tier = computed(() => user.value?.tier || 'free')

  function setAuth(t, u) {
    token.value = t
    user.value = u
    localStorage.setItem('fc_token', t)
    localStorage.setItem('fc_user', JSON.stringify(u))
    http.defaults.headers.common['Authorization'] = `Bearer ${t}`
  }

  function clearAuth() {
    token.value = ''
    user.value = null
    localStorage.removeItem('fc_token')
    localStorage.removeItem('fc_user')
    delete http.defaults.headers.common['Authorization']
  }

  async function register(email, password, name) {
    const res = await http.post('/auth/register', { email, password, name })
    if (res.data.code === 0) {
      setAuth(res.data.data.token, res.data.data.user)
      return { ok: true }
    }
    return { ok: false, error: res.data.message }
  }

  async function login(email, password) {
    const res = await http.post('/auth/login', { email, password })
    if (res.data.code === 0) {
      setAuth(res.data.data.token, res.data.data.user)
      return { ok: true }
    }
    return { ok: false, error: res.data.message }
  }

  async function fetchMe() {
    if (!token.value) return
    try {
      http.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
      const res = await http.get('/auth/me')
      if (res.data.code === 0) {
        user.value = res.data.data
        localStorage.setItem('fc_user', JSON.stringify(res.data.data))
      }
    } catch {
      clearAuth()
    }
  }

  function logout() {
    clearAuth()
  }

  // 初始化时恢复 token header
  if (token.value) {
    http.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
  }

  return { token, user, isLoggedIn, tierLabel, tier, login, register, logout, fetchMe }
})
