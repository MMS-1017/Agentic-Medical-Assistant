<template>
  <div class="max-w-3xl mx-auto px-4 py-8">

    <!-- Header -->
    <h1 class="text-xl font-bold text-slate-800 mb-6">💊 Prescriptions</h1>

    <!-- Loading -->
    <div v-if="loading" class="flex flex-col items-center justify-center py-20 gap-3">
      <div class="w-8 h-8 border-2 border-medical-300 border-t-medical-600 rounded-full animate-spin" />
      <p class="text-sm text-slate-400">Loading prescriptions…</p>
    </div>

    <!-- Empty -->
    <div v-else-if="prescriptions.length === 0" class="flex flex-col items-center justify-center py-20 gap-4">
      <div class="text-5xl">💊</div>
      <p class="text-slate-400 text-sm">No active prescriptions</p>
      <p class="text-xs text-slate-300 text-center max-w-xs">
        Your doctor will add prescriptions after your appointment. You'll receive
        Telegram reminders for each medication dose.
      </p>
    </div>

    <!-- Prescriptions -->
    <div v-else class="space-y-5">
      <div
        v-for="rx in prescriptions"
        :key="rx.prescription_id"
        class="card"
      >
        <!-- Rx header -->
        <div class="flex items-start justify-between mb-4">
          <div>
            <div class="flex items-center gap-2">
              <h2 class="font-semibold text-slate-800">{{ rx.diagnosis_summary || 'Prescription' }}</h2>
              <span class="badge"
                :class="rx.status === 'active' ? 'bg-green-50 text-green-700' : 'bg-slate-100 text-slate-500'"
              >
                {{ rx.status }}
              </span>
            </div>
            <p class="text-xs text-slate-400 mt-0.5">
              Issued {{ formatDate(rx.issued_date) }}
              <span v-if="rx.doctor_name"> · Dr. {{ rx.doctor_name }}</span>
            </p>
          </div>
          <div class="text-right text-xs text-slate-400">
            <p v-if="rx.valid_until">Valid until</p>
            <p v-if="rx.valid_until" class="font-medium text-slate-600">{{ formatDate(rx.valid_until) }}</p>
          </div>
        </div>

        <!-- Medications -->
        <div class="space-y-3">
          <div
            v-for="med in rx.medications"
            :key="med.medication_id"
            class="p-3 rounded-xl bg-slate-50 border border-slate-100"
          >
            <div class="flex items-start justify-between">
              <div>
                <p class="text-sm font-semibold text-slate-700">{{ med.name }}</p>
                <p class="text-xs text-slate-400 mt-0.5">
                  {{ med.dosage }}
                  <span v-if="med.frequency"> · {{ med.frequency }}</span>
                  <span v-if="med.duration_days"> · {{ med.duration_days }} days</span>
                </p>
              </div>
              <div class="flex gap-1 flex-wrap justify-end">
                <span
                  v-for="schedule in med.schedules"
                  :key="schedule.schedule_id"
                  class="badge bg-medical-50 text-medical-700"
                >
                  🕐 {{ schedule.medication_time }}
                </span>
              </div>
            </div>
            <p v-if="med.notes" class="text-xs text-slate-400 mt-2 italic">{{ med.notes }}</p>
          </div>
        </div>

        <!-- Reminder note -->
        <div class="mt-3 pt-3 border-t border-slate-50 flex items-center gap-2 text-xs text-slate-400">
          <span>📱</span>
          <span>Telegram reminders sent 30 minutes before each dose</span>
        </div>
      </div>
    </div>

    <!-- Adherence summary -->
    <div v-if="!loading && prescriptions.length" class="mt-6 grid grid-cols-2 gap-4">
      <div class="card text-center">
        <p class="text-2xl font-bold text-medical-600">{{ activeMedCount }}</p>
        <p class="text-xs text-slate-400 mt-1">Active medications</p>
      </div>
      <div class="card text-center">
        <p class="text-2xl font-bold text-amber-500">{{ dailyDoseCount }}</p>
        <p class="text-xs text-slate-400 mt-1">Daily doses</p>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { prescriptionApi } from '../api/client'

const loading = ref(true)
const prescriptions = ref([])

function formatDate(s) {
  if (!s) return ''
  return new Date(s).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
}

const activeMedCount = computed(() =>
  prescriptions.value
    .filter(rx => rx.status === 'active')
    .flatMap(rx => rx.medications || [])
    .length
)

const dailyDoseCount = computed(() =>
  prescriptions.value
    .filter(rx => rx.status === 'active')
    .flatMap(rx => rx.medications || [])
    .flatMap(m => m.schedules || [])
    .length
)

onMounted(async () => {
  try {
    const res = await prescriptionApi.list()
    prescriptions.value = res.data || []
  } catch {
    /* handled by empty state */
  } finally {
    loading.value = false
  }
})
</script>
