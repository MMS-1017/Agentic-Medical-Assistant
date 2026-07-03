import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  timeout: 120_000,
})

// Attach JWT on every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// ── Auth ──────────────────────────────────────────────────────────────────────
export const authApi = {
  register: (data) => api.post('/auth/register', data),
  login: (email, password) => {
    const form = new FormData()
    form.append('username', email)
    form.append('password', password)
    return api.post('/auth/token', form)
  },
}

// ── Chat ──────────────────────────────────────────────────────────────────────
export const chatApi = {
  text: (query) => api.post('/chat/text', { query }),
  voice: (audioFile) => {
    const form = new FormData()
    form.append('audio', audioFile)
    return api.post('/chat/voice', form)
  },
  image: (imageFile, complaint = '') => {
    const form = new FormData()
    form.append('image', imageFile)
    form.append('complaint', complaint)
    return api.post('/chat/image', form)
  },
}

// ── Patient ───────────────────────────────────────────────────────────────────
export const patientApi = {
  me: () => api.get('/patients/me'),
  updateHistory: (data) => api.put('/patients/me/history', data),
  updateTelegram: (id) => api.patch('/patients/me/telegram', { telegram_chat_id: id }),
  diagnoses: () => api.get('/patients/me/diagnoses'),
  appointments: () => api.get('/patients/me/appointments'),
  loyalty: () => api.get('/patients/me/loyalty'),
}

// ── Prescriptions ─────────────────────────────────────────────────────────────
export const prescriptionApi = {
  list: () => api.get('/prescriptions/me'),
}

// ── Admin ─────────────────────────────────────────────────────────────────────
export const adminApi = {
  hitlCases: () => api.get('/admin/hitl/cases'),
  resolveCase: (caseId, doctorId, notes) =>
    api.post(`/admin/hitl/cases/${caseId}/resolve`, { doctor_id: doctorId, notes }),
}

export default api
