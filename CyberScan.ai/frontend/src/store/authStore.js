import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import api from '../utils/api'

const useAuthStore = create(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isLoading: false,

      setAuth: (user, token) => set({ user, token }),

      login: async (email, password) => {
        set({ isLoading: true })
        try {
          const form = new FormData()
          form.append('username', email)
          form.append('password', password)
          const { data } = await api.post('/auth/login', form, {
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          })
          set({ user: data.user, token: data.access_token, isLoading: false })
          return { success: true }
        } catch (err) {
          set({ isLoading: false })
          return { success: false, error: err.response?.data?.detail || 'Login failed' }
        }
      },

      register: async (email, password, fullName) => {
        set({ isLoading: true })
        try {
          const { data } = await api.post('/auth/register', {
            email, password, full_name: fullName,
          })
          set({ user: data.user, token: data.access_token, isLoading: false })
          return { success: true }
        } catch (err) {
          set({ isLoading: false })
          return { success: false, error: err.response?.data?.detail || 'Registration failed' }
        }
      },

      logout: () => set({ user: null, token: null }),

      refreshUser: async () => {
        try {
          const { data } = await api.get('/auth/me')
          set({ user: data })
        } catch {
          set({ user: null, token: null })
        }
      },

      updateUser: (updates) => set(state => ({ user: { ...state.user, ...updates } })),
    }),
    {
      name: 'securescout-auth',
      partialize: (state) => ({ user: state.user, token: state.token }),
    }
  )
)

export default useAuthStore
