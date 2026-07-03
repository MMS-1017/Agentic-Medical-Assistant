<template>
  <div class="max-w-3xl mx-auto px-4 py-8">

    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-xl font-bold text-slate-800">📅 Appointments</h1>
      <div class="flex gap-2">
        <button
          v-for="tab in ['Upcoming', 'Past']"
          :key="tab"
          @click="activeTab = tab"
          class="px-4 py-1.5 text-sm font-medium rounded-lg transition-all"
          :class="activeTab === tab
            ? 'bg-medical-600 text-white shadow-sm'
            : 'text-slate-500 hover:bg-slate-100'"
        >
          {{ tab }}
        </button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex flex-col items-center justify-center py-20 gap-3">
      <div class="w-8 h-8 border-2 border-medical-300 border-t-medical-600 rounded-full animate-spin" />
      <p class="text-sm text-slate-400">Loading appointments…</p>
    </div>

    <!-- Empty -->
    <div v-else-if="filtered.length === 0" class="flex flex-col items-center justify-center py-20 gap-4">
      <div class="text-5xl">📋</div>
      <p class="text-slate-400 text-sm">No {{ activeTab.toLowerCase() }} appointments</p>
      <p class="text-xs text-slate-300 text-center max-w-xs">
        Chat with MediAssist AI to book an appointment — just describe your symptoms!
      </p>
    </div>

    <!-- List -->
    <div v-else class="space-y-4">
      <div
        v-for="appt in filtered"
        :key="appt.appointment_id"
        class="card hover:shadow-md transition-shadow"
      >
        <div class="flex items-start gap-4">
          <!-- Date block -->
          <div class="flex-shrink-0 w-14 h-14 rounded-xl flex flex-col items-center justify-center
                      text-center border"
            :class="statusColor(appt.status).bg"
          >
            <p class="text-lg font-bold leading-none" :class="statusColor(appt.status).text">
              {{ dayNum(appt.appointment_date) }}
            </p>
            <p class="text-xs font-medium uppercase tracking-wide mt-0.5" :class="statusColor(appt.status).text">
              {{ monthAbbr(appt.appointment_date) }}
            </p>
          </div>

          <!-- Info -->
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 flex-wrap">
              <p class="font-semibold text-slate-800 text-sm">{{ appt.department || appt.doctor_name || 'Appointment' }}</p>
              <span class="badge text-xs" :class="statusBadge(appt.status)">{{ appt.status }}</span>
            </div>
            <p v-if="appt.doctor_name" class="text-xs text-slate-500 mt-0.5">
              Dr. {{ appt.doctor_name }}
              <span v-if="appt.clinic_name"> · {{ appt.clinic_name }}</span>
            </p>
            <p class="text-xs text-slate-400 mt-1">
              <span>🕐 {{ formatTime(appt.appointment_date) }}</span>
              <span v-if="appt.location" class="ml-3">📍 {{ appt.location }}</span>
            </p>
          </div>

          <!-- Actions -->
          <div v-if="isUpcoming(appt)" class="flex-shrink-0 flex flex-col gap-1">
            <span class="text-xs text-slate-400 text-right">{{ daysUntil(appt.appointment_date) }}</span>
          </div>
        </div>

        <!-- Feedback badge -->
        <div
          v-if="appt.feedback_submitted"
          class="mt-3 pt-3 border-t border-slate-50 flex items-center gap-2 text-xs text-green-600"
        >
          <span>✓</span> Feedback submitted
        </div>
      </div>
    </div>

    <!-- Summary stats (past tab) -->
    <div v-if="activeTab === 'Past' && !loading && allAppointments.length" class="mt-6 grid grid-cols-3 gap-4">
      <div class="card text-center">
        <p class="text-2xl font-bold text-medical-600">{{ stats.total }}</p>
        <p class="text-xs text-slate-400 mt-1">Total visits</p>
      </div>
      <div class="card text-center">
        <p class="text-2xl font-bold text-green-600">{{ stats.completed }}</p>
        <p class="text-xs text-slate-400 mt-1">Completed</p>
      </div>
      <div class="card text-center">
        <p class="text-2xl font-bold text-amber-500">{{ stats.departments }}</p>
        <p class="text-xs text-slate-400 mt-1">Departments</p>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { patientApi } from '../api/client'

const loading = ref(true)
const allAppointments = ref([])
const activeTab = ref('Upcoming')

const now = new Date()

function isUpcoming(a) {
  return new Date(a.appointment_date) >= now && a.status !== 'cancelled'
}

const filtered = computed(() =>
  allAppointments.value.filter(a =>
    activeTab.value === 'Upcoming' ? isUpcoming(a) : !isUpcoming(a)
  ).sort((a, b) =>
    activeTab.value === 'Upcoming'
      ? new Date(a.appointment_date) - new Date(b.appointment_date)
      : new Date(b.appointment_date) - new Date(a.appointment_date)
  )
)

const stats = computed(() => {
  const past = allAppointments.value.filter(a => !isUpcoming(a))
  return {
    total: past.length,
    completed: past.filter(a => a.status === 'completed').length,
    departments: new Set(past.map(a => a.department).filter(Boolean)).size,
  }
})

function dayNum(d)    { return new Date(d).getDate() }
function monthAbbr(d) { return new Date(d).toLocaleString('en', { month: 'short' }) }
function formatTime(d) {
  return new Date(d).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}
function daysUntil(d) {
  const diff = Math.ceil((new Date(d) - now) / 86400000)
  if (diff === 0) return 'Today'
  if (diff === 1) return 'Tomorrow'
  return `In ${diff} days`
}

function statusColor(s) {
  const map = {
    scheduled:  { bg: 'bg-medical-50 border-medical-200', text: 'text-medical-700' },
    completed:  { bg: 'bg-green-50 border-green-200',     text: 'text-green-700'   },
    cancelled:  { bg: 'bg-slate-50 border-slate-200',     text: 'text-slate-500'   },
    no_show:    { bg: 'bg-orange-50 border-orange-200',   text: 'text-orange-700'  },
  }
  return map[s] || map.scheduled
}

function statusBadge(s) {
  const map = {
    scheduled: 'bg-medical-50 text-medical-700',
    completed: 'bg-green-50 text-green-700',
    cancelled: 'bg-slate-100 text-slate-500',
    no_show:   'bg-orange-50 text-orange-700',
  }
  return map[s] || 'bg-slate-100 text-slate-600'
}

onMounted(async () => {
  try {
    const res = await patientApi.appointments()
    allAppointments.value = res.data || []
    // Switch to Past tab if no upcoming
    const hasUpcoming = allAppointments.value.some(isUpcoming)
    if (!hasUpcoming && allAppointments.value.length) activeTab.value = 'Past'
  } catch {
    /* handled by empty state */
  } finally {
    loading.value = false
  }
})
</script>
