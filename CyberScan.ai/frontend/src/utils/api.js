import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 90000, // 90s — accounts for Render cold start + scan time
  headers: { 'Content-Type': 'application/json' },
})

// Request interceptor — attach JWT token
api.interceptors.request.use(
  (config) => {
    try {
      const stored = localStorage.getItem('securescout-auth')
      if (stored) {
        const { state } = JSON.parse(stored)
        if (state?.token) {
          config.headers.Authorization = `Bearer ${state.token}`
        }
      }
    } catch {}
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor — handle 401 globally
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear auth and redirect to login
      localStorage.removeItem('securescout-auth')
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export default api

// ── Scan API ──────────────────────────────────────────────────────────────────
export const scanAPI = {
  startScan:   (url)     => api.post('/scan/', { url }),
  getHistory:  (limit=20, offset=0) => api.get(`/scan/history?limit=${limit}&offset=${offset}`),
  getScan:     (id)      => api.get(`/scan/${id}`),
  deleteScan:  (id)      => api.delete(`/scan/${id}`),
  downloadPDF: (id)      => api.get(`/scan/${id}/pdf`, { responseType: 'blob' }),
}

// ── User API ──────────────────────────────────────────────────────────────────
export const userAPI = {
  getStats:      ()    => api.get('/user/stats'),
  updateProfile: (data) => api.patch('/user/profile', data),
}
