import axios from 'axios'

const http = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  timeout: 120000,
})

// 统一注入 Token
http.interceptors.request.use((config) => {
  const token = localStorage.getItem('fc_token')
  if (token) config.headers['Authorization'] = `Bearer ${token}`
  return config
})

http.interceptors.response.use(
  (res) => res.data,
  (err) => {
    const msg = err.response?.data?.detail || err.response?.data?.message || '请求失败，请稍后重试'
    return Promise.reject(new Error(msg))
  }
)

export const authApi = {
  register: (data) => http.post('/auth/register', data),
  login: (data) => http.post('/auth/login', data),
  me: () => http.get('/auth/me'),
  upgrade: (data) => http.post('/auth/upgrade', data),
  tiers: () => http.get('/auth/tiers'),
}

export const painPointApi = {
  analyze: (data) => http.post('/pain-point/analyze', data),
  getCategories: () => http.get('/pain-point/categories'),
}

export const listingApi = {
  generate: (data) => http.post('/listing/generate', data),
  complianceCheck: (data) => http.post('/listing/compliance-check', data),
  getPlatforms: () => http.get('/listing/platforms'),
}

export const contentPackApi = {
  generate: (data) => http.post('/content-pack/generate', data),
  getSeason: () => http.get('/content-pack/season'),
  getLiveModules: () => http.get('/content-pack/live-modules'),
}

export const pipelineApi = {
  run: (data) => http.post('/pipeline/run', data),
}

export const liveReviewApi = {
  analyze: (data) => http.post('/live-review/analyze', data),
}

export const replyApi = {
  generate: (data) => http.post('/reply/generate', data),
  batch: (data) => http.post('/reply/batch', data),
}

export const adApi = {
  optimize: (data) => http.post('/ad/optimize', data),
}

export const dashboardApi = {
  getStats: () => http.get('/dashboard/stats'),
  getKbStats: () => http.get('/dashboard/knowledge-base/stats'),
  getHistory: (days = 30) => http.get(`/dashboard/history?days=${days}`),
  getHistoryDetail: (type, id) => http.get(`/dashboard/history/detail?record_type=${type}&record_id=${id}`),
}

export const feedbackApi = {
  submit: (data) => http.post('/feedback/submit', data),
  stats: () => http.get('/feedback/stats'),
}

export const sampleApi = {
  stats: () => http.get('/samples/stats'),
  list: (params) => http.get('/samples/list', { params }),
  categories: () => http.get('/samples/categories'),
  add: (data) => http.post('/samples/add', data),
  importFile: (formData) => http.post('/samples/import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  validate: (data) => http.post('/samples/validate', data),
}

export default http
