import { defineStore } from 'pinia'
import { authApi, patientApi } from '../api/client'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || null,
    patient: null,
    loading: false,
    error: null,
  }),

  getters: {
    isLoggedIn: (state) => !!state.token,
    fullName: (state) =>
      state.patient ? `${state.patient.first_name} ${state.patient.last_name}` : '',
    loyaltyPoints: (state) => state.patient?.loyalty_points ?? 0,
  },

  actions: {
    async login(email, password) {
      this.loading = true
      this.error = null
      try {
        const { data } = await authApi.login(email, password)
        this.token = data.access_token
        localStorage.setItem('token', data.access_token)
        await this.fetchProfile()
        return true
      } catch (err) {
        this.error = err.response?.data?.detail || 'Login failed'
        return false
      } finally {
        this.loading = false
      }
    },

    async register(payload) {
      this.loading = true
      this.error = null
      try {
        await authApi.register(payload)
        return await this.login(payload.email, payload.password)
      } catch (err) {
        this.error = err.response?.data?.detail || 'Registration failed'
        return false
      } finally {
        this.loading = false
      }
    },

    async fetchProfile() {
      try {
        const { data } = await patientApi.me()
        this.patient = data
      } catch {
        // token may have expired
        this.logout()
      }
    },

    logout() {
      this.token = null
      this.patient = null
      localStorage.removeItem('token')
    },
  },
})
