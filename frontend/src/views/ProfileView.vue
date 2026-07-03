<template>
  <div class="max-w-3xl mx-auto px-4 py-8 space-y-6">

    <!-- Header -->
    <div class="flex items-center gap-4">
      <div class="w-16 h-16 rounded-2xl bg-medical-600 flex items-center justify-center
                  text-white text-2xl font-bold shadow-md">
        {{ initials }}
      </div>
      <div>
        <h1 class="text-xl font-bold text-slate-800">{{ fullName }}</h1>
        <p class="text-sm text-slate-400">{{ auth.patient?.email }}</p>
      </div>
      <div class="ml-auto flex items-center gap-2 px-4 py-2 bg-amber-50 rounded-xl border border-amber-100">
        <span class="text-amber-500 text-xl">⭐</span>
        <div>
          <p class="text-xs text-amber-600 font-medium leading-none">Loyalty Points</p>
          <p class="text-lg font-bold text-amber-700 leading-tight">{{ loyaltyPoints }}</p>
        </div>
      </div>
    </div>

    <!-- Loyalty offers -->
    <div v-if="offers.length" class="card">
      <h2 class="text-sm font-semibold text-slate-700 mb-3">🎁 Available Offers</h2>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div
          v-for="offer in offers"
          :key="offer.offer_id"
          class="p-3 rounded-xl border border-amber-100 bg-amber-50 flex items-center justify-between"
        >
          <div>
            <p class="text-sm font-medium text-amber-800">{{ offer.name }}</p>
            <p class="text-xs text-amber-600">{{ offer.required_points }} pts · {{ offer.discount_percent }}% off</p>
          </div>
          <button
            @click="redeem(offer)"
            :disabled="loyaltyPoints < offer.required_points"
            class="text-xs font-semibold px-3 py-1.5 rounded-lg bg-amber-500 text-white
                   hover:bg-amber-600 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
          >
            Redeem
          </button>
        </div>
      </div>
    </div>

    <!-- Medical history editor -->
    <div class="card">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-sm font-semibold text-slate-700">🩺 Medical History</h2>
        <div class="flex gap-2">
          <button v-if="!editingHistory" @click="editingHistory = true" class="btn-ghost text-xs text-medical-600 px-2 py-1">
            Edit
          </button>
          <template v-else>
            <button @click="saveHistory" :disabled="saving" class="btn-primary text-xs px-3 py-1">
              {{ saving ? 'Saving…' : 'Save' }}
            </button>
            <button @click="cancelEdit" class="btn-ghost text-xs text-slate-400 px-2 py-1">Cancel</button>
          </template>
        </div>
      </div>

      <div class="space-y-4">
        <div>
          <label class="block text-xs font-semibold text-slate-500 mb-2">Chronic Conditions</label>
          <div v-if="!editingHistory" class="flex flex-wrap gap-2">
            <span
              v-for="c in historyForm.chronic_conditions" :key="c"
              class="badge bg-red-50 text-red-700"
            >{{ c }}</span>
            <span v-if="!historyForm.chronic_conditions.length" class="text-sm text-slate-300">None recorded</span>
          </div>
          <div v-else>
            <input
              v-model="conditionsInput"
              class="input text-sm"
              placeholder="e.g. diabetes, hypertension (comma-separated)"
            />
            <p class="text-xs text-slate-400 mt-1">Separate with commas</p>
          </div>
        </div>

        <div>
          <label class="block text-xs font-semibold text-slate-500 mb-2">Allergies</label>
          <div v-if="!editingHistory" class="flex flex-wrap gap-2">
            <span
              v-for="a in historyForm.allergies" :key="a"
              class="badge bg-orange-50 text-orange-700"
            >{{ a }}</span>
            <span v-if="!historyForm.allergies.length" class="text-sm text-slate-300">None recorded</span>
          </div>
          <div v-else>
            <input
              v-model="allergiesInput"
              class="input text-sm"
              placeholder="e.g. penicillin, shellfish (comma-separated)"
            />
          </div>
        </div>

        <div>
          <label class="block text-xs font-semibold text-slate-500 mb-2">Current Medications</label>
          <div v-if="!editingHistory" class="flex flex-wrap gap-2">
            <span
              v-for="m in historyForm.current_medications" :key="m"
              class="badge bg-blue-50 text-blue-700"
            >{{ m }}</span>
            <span v-if="!historyForm.current_medications.length" class="text-sm text-slate-300">None recorded</span>
          </div>
          <div v-else>
            <input
              v-model="medicationsInput"
              class="input text-sm"
              placeholder="e.g. metformin 500mg, aspirin 75mg (comma-separated)"
            />
          </div>
        </div>
      </div>

      <div v-if="historySuccess" class="mt-3 text-xs text-green-600 font-medium">✓ Medical history updated</div>
      <div v-if="historyError" class="mt-3 text-xs text-red-600">⚠️ {{ historyError }}</div>
    </div>

    <!-- Telegram notifications -->
    <div class="card">
      <h2 class="text-sm font-semibold text-slate-700 mb-4">📱 Telegram Notifications</h2>
      <p class="text-xs text-slate-400 mb-3">
        Receive medication reminders, appointment confirmations, and emergency alerts via Telegram.
        Start a chat with our bot and paste your Chat ID below.
      </p>
      <div class="flex gap-2">
        <input
          v-model="telegramId"
          class="input flex-1 text-sm"
          placeholder="e.g. 123456789"
          type="number"
        />
        <button
          @click="saveTelegram"
          :disabled="savingTelegram || !telegramId"
          class="btn-primary text-sm px-4 whitespace-nowrap"
        >
          {{ savingTelegram ? 'Saving…' : 'Save' }}
        </button>
      </div>
      <div v-if="telegramSuccess" class="mt-2 text-xs text-green-600 font-medium">✓ Telegram ID saved</div>
      <div v-if="telegramError" class="mt-2 text-xs text-red-600">⚠️ {{ telegramError }}</div>
    </div>

    <!-- Recent diagnoses -->
    <div class="card">
      <h2 class="text-sm font-semibold text-slate-700 mb-4">🔬 Recent Diagnoses</h2>
      <div v-if="loadingDiagnoses" class="flex items-center gap-2 text-sm text-slate-400">
        <div class="w-4 h-4 border-2 border-medical-300 border-t-medical-600 rounded-full animate-spin" />
        Loading…
      </div>
      <div v-else-if="diagnoses.length === 0" class="text-sm text-slate-300 text-center py-4">
        No diagnoses yet
      </div>
      <div v-else class="space-y-3">
        <div
          v-for="d in diagnoses.slice(0, 5)"
          :key="d.diagnosis_id"
          class="flex items-start gap-3 p-3 rounded-xl bg-slate-50"
        >
          <div class="mt-0.5 w-2 h-2 rounded-full flex-shrink-0"
            :class="d.urgency_score >= 0.85 ? 'bg-red-500' : d.urgency_score >= 0.6 ? 'bg-orange-400' : 'bg-green-500'"
          />
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-slate-700 truncate">{{ d.raw_complaint }}</p>
            <p class="text-xs text-slate-400 mt-0.5">
              {{ d.department }} · {{ pct(d.confidence_score) }} confidence
            </p>
          </div>
          <span class="text-xs text-slate-400 whitespace-nowrap">{{ formatDate(d.created_at) }}</span>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { patientApi } from '../api/client'

const auth = useAuthStore()

const initials = computed(() => {
  const p = auth.patient
  return p ? `${p.first_name?.[0] ?? ''}${p.last_name?.[0] ?? ''}`.toUpperCase() : 'P'
})
const fullName = computed(() => {
  const p = auth.patient
  return p ? `${p.first_name ?? ''} ${p.last_name ?? ''}`.trim() : '—'
})
const loyaltyPoints = computed(() => auth.loyaltyPoints)

const offers = ref([])
const diagnoses = ref([])
const loadingDiagnoses = ref(true)

const editingHistory = ref(false)
const saving = ref(false)
const historySuccess = ref(false)
const historyError = ref('')

const historyForm = ref({ chronic_conditions: [], allergies: [], current_medications: [] })
const conditionsInput = ref('')
const allergiesInput  = ref('')
const medicationsInput = ref('')

const telegramId = ref(auth.patient?.telegram_chat_id || '')
const savingTelegram  = ref(false)
const telegramSuccess = ref(false)
const telegramError   = ref('')

function pct(v) { return v != null ? `${Math.round(v * 100)}%` : '—' }
function formatDate(s) {
  if (!s) return ''
  return new Date(s).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })
}

function cancelEdit() {
  editingHistory.value = false
  historyError.value = ''
  historySuccess.value = false
  const h = historyForm.value
  conditionsInput.value  = h.chronic_conditions.join(', ')
  allergiesInput.value   = h.allergies.join(', ')
  medicationsInput.value = h.current_medications.join(', ')
}

function splitInput(s) {
  return s.split(',').map(x => x.trim()).filter(Boolean)
}

async function saveHistory() {
  saving.value = true
  historyError.value = ''
  historySuccess.value = false
  try {
    await patientApi.updateHistory({
      chronic_conditions:  splitInput(conditionsInput.value),
      allergies:           splitInput(allergiesInput.value),
      current_medications: splitInput(medicationsInput.value),
    })
    historyForm.value.chronic_conditions  = splitInput(conditionsInput.value)
    historyForm.value.allergies           = splitInput(allergiesInput.value)
    historyForm.value.current_medications = splitInput(medicationsInput.value)
    historySuccess.value = true
    editingHistory.value = false
    setTimeout(() => { historySuccess.value = false }, 3000)
  } catch (e) {
    historyError.value = e.response?.data?.detail || 'Failed to save'
  } finally {
    saving.value = false
  }
}

async function saveTelegram() {
  savingTelegram.value = true
  telegramError.value  = ''
  telegramSuccess.value = false
  try {
    await patientApi.updateTelegram(telegramId.value)
    telegramSuccess.value = true
    setTimeout(() => { telegramSuccess.value = false }, 3000)
  } catch (e) {
    telegramError.value = e.response?.data?.detail || 'Failed to save'
  } finally {
    savingTelegram.value = false
  }
}

async function redeem(offer) {
  // Placeholder — backend offer redemption endpoint not yet exposed in client
  alert(`Redeeming "${offer.name}" — feature coming soon!`)
}

onMounted(async () => {
  // Load history
  try {
    const res = await patientApi.me()
    const history = res.data.medical_history
    if (history) {
      historyForm.value = {
        chronic_conditions:  history.chronic_conditions  || [],
        allergies:           history.allergies           || [],
        current_medications: history.current_medications || [],
      }
      conditionsInput.value  = historyForm.value.chronic_conditions.join(', ')
      allergiesInput.value   = historyForm.value.allergies.join(', ')
      medicationsInput.value = historyForm.value.current_medications.join(', ')
    }
    if (res.data.telegram_chat_id) {
      telegramId.value = res.data.telegram_chat_id
    }
  } catch { /* already have auth.patient */ }

  // Load loyalty offers
  try {
    const res = await patientApi.loyalty()
    offers.value = res.data.offers || []
  } catch { /* non-critical */ }

  // Load diagnoses
  try {
    const res = await patientApi.diagnoses()
    diagnoses.value = res.data || []
  } catch { /* non-critical */ } finally {
    loadingDiagnoses.value = false
  }
})
</script>
