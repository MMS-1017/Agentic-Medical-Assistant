<template>
  <div class="flex flex-col h-[calc(100vh-4rem)]">

    <!-- Header banner -->
    <div class="bg-white border-b border-slate-100 px-4 py-3 flex items-center gap-3">
      <div class="w-10 h-10 rounded-xl bg-medical-50 border border-medical-100
                  flex items-center justify-center text-xl">🤖</div>
      <div>
        <p class="font-semibold text-slate-800 text-sm">MediAssist AI</p>
        <p class="text-xs text-green-500 font-medium">● Online · ready to help</p>
      </div>
      <button @click="clearChat" class="ml-auto btn-ghost text-slate-400 text-xs px-2 py-1">
        Clear chat
      </button>
    </div>

    <!-- Messages area -->
    <div ref="scrollEl" class="flex-1 overflow-y-auto px-4 py-6 space-y-5 max-w-3xl mx-auto w-full">

      <!-- Welcome message -->
      <div v-if="messages.length === 0" class="flex flex-col items-center justify-center h-full gap-6 pb-10">
        <div class="text-6xl">👋</div>
        <div class="text-center">
          <h2 class="text-xl font-bold text-slate-700">Hello, {{ auth.patient?.first_name || 'there' }}!</h2>
          <p class="text-slate-400 text-sm mt-1">How can I help you today?</p>
        </div>
        <div class="grid grid-cols-2 gap-3 w-full max-w-sm">
          <button
            v-for="s in suggestions" :key="s.text"
            @click="sendSuggestion(s.text)"
            class="p-3 text-left rounded-xl border border-slate-200 bg-white
                   hover:border-medical-300 hover:bg-medical-50 transition-all group"
          >
            <span class="text-xl">{{ s.icon }}</span>
            <p class="text-xs font-medium text-slate-700 mt-1 group-hover:text-medical-700">{{ s.text }}</p>
          </button>
        </div>
      </div>

      <!-- Chat messages -->
      <ChatMessage
        v-for="(msg, i) in messages"
        :key="i"
        :msg="msg"
        :initials="initials"
      />

      <!-- Typing indicator -->
      <div v-if="loading" class="flex gap-3 items-end">
        <div class="w-8 h-8 rounded-full bg-white border-2 border-medical-200
                    flex items-center justify-center text-lg">🏥</div>
        <div class="bg-white border border-slate-100 rounded-2xl rounded-bl-sm px-4 py-3 shadow-sm">
          <div class="flex gap-1.5 items-center h-5">
            <span v-for="n in 3" :key="n"
              class="w-2 h-2 rounded-full bg-slate-300 animate-bounce"
              :style="{ animationDelay: `${(n-1)*0.15}s` }" />
          </div>
        </div>
      </div>
    </div>

    <!-- Input area -->
    <div class="bg-white border-t border-slate-100 px-4 py-4">
      <div class="max-w-3xl mx-auto">

        <!-- File preview bar -->
        <div v-if="pendingFile" class="mb-3 flex items-center gap-2 px-3 py-2
                                        bg-medical-50 rounded-xl border border-medical-100">
          <span class="text-lg">{{ pendingFile.type.startsWith('audio') ? '🎙️' : '🖼️' }}</span>
          <span class="text-sm text-medical-700 font-medium flex-1 truncate">{{ pendingFile.name }}</span>
          <button @click="pendingFile = null" class="text-slate-400 hover:text-red-500 transition-colors">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>

        <!-- Input row -->
        <div class="flex gap-2 items-end">

          <!-- Attach image -->
          <label class="flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center
                         border border-slate-200 text-slate-500 cursor-pointer
                         hover:bg-slate-50 hover:border-medical-300 hover:text-medical-600 transition-all">
            <input type="file" accept="image/*" class="hidden" @change="pickImage" />
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14M14 8h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/>
            </svg>
          </label>

          <!-- Voice record -->
          <button
            @click="toggleRecord"
            class="flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center
                   border transition-all"
            :class="recording
              ? 'bg-red-50 border-red-300 text-red-500 animate-pulse'
              : 'border-slate-200 text-slate-500 hover:bg-slate-50 hover:border-medical-300 hover:text-medical-600'"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"/>
            </svg>
          </button>

          <!-- Text input -->
          <textarea
            v-model="inputText"
            rows="1"
            :placeholder="pendingFile ? 'Add a complaint (optional)…' : 'Describe your symptoms or ask anything…'"
            class="input flex-1 resize-none leading-relaxed max-h-32 py-2.5"
            @keydown.enter.exact.prevent="send"
            @input="autoGrow"
            ref="textEl"
          />

          <!-- Send -->
          <button
            @click="send"
            :disabled="loading || (!inputText.trim() && !pendingFile)"
            class="flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center
                   bg-medical-600 text-white transition-all
                   hover:bg-medical-700 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <svg class="w-5 h-5 rotate-90" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/>
            </svg>
          </button>
        </div>

        <p class="text-center text-xs text-slate-300 mt-2">
          Press Enter to send · Shift+Enter for new line
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, computed } from 'vue'
import { chatApi } from '../api/client'
import { useAuthStore } from '../stores/auth'
import ChatMessage from '../components/ChatMessage.vue'

const auth    = useAuthStore()
const messages = ref([])
const inputText = ref('')
const loading = ref(false)
const pendingFile = ref(null)
const recording = ref(false)
const scrollEl = ref(null)
const textEl   = ref(null)

let mediaRecorder = null
let audioChunks  = []

const initials = computed(() => {
  const p = auth.patient
  return p ? `${p.first_name?.[0] ?? ''}${p.last_name?.[0] ?? ''}`.toUpperCase() : 'P'
})

const suggestions = [
  { icon: '🤒', text: 'I have a headache and fever' },
  { icon: '💔', text: 'Chest pain radiating to my arm' },
  { icon: '📅', text: 'Book a cardiology appointment' },
  { icon: '👁️', text: 'My eye is red with discharge' },
]

function now() {
  return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function scrollToBottom() {
  nextTick(() => {
    if (scrollEl.value) scrollEl.value.scrollTop = scrollEl.value.scrollHeight
  })
}

function autoGrow(e) {
  e.target.style.height = 'auto'
  e.target.style.height = Math.min(e.target.scrollHeight, 128) + 'px'
}

function clearChat() {
  messages.value = []
  inputText.value = ''
  pendingFile.value = null
}

function sendSuggestion(text) {
  inputText.value = text
  send()
}

function pickImage(e) {
  pendingFile.value = e.target.files[0] || null
  e.target.value = ''
}

async function toggleRecord() {
  if (recording.value) {
    mediaRecorder?.stop()
    recording.value = false
    return
  }
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    audioChunks = []
    mediaRecorder = new MediaRecorder(stream)
    mediaRecorder.ondataavailable = (e) => audioChunks.push(e.data)
    mediaRecorder.onstop = () => {
      const blob = new Blob(audioChunks, { type: 'audio/wav' })
      pendingFile.value = new File([blob], 'recording.wav', { type: 'audio/wav' })
      stream.getTracks().forEach(t => t.stop())
    }
    mediaRecorder.start()
    recording.value = true
  } catch {
    alert('Microphone access denied.')
  }
}

async function send() {
  const text = inputText.value.trim()
  const file = pendingFile.value
  if (!text && !file) return
  if (loading.value) return

  const label = text || (file?.type.startsWith('audio') ? '🎙️ Voice message' : `🖼️ ${file.name}`)
  messages.value.push({ role: 'user', content: label, time: now(), file: file?.name })
  inputText.value = ''
  pendingFile.value = null
  if (textEl.value) textEl.value.style.height = 'auto'
  scrollToBottom()
  loading.value = true

  try {
    let res
    if (file?.type.startsWith('audio')) {
      res = await chatApi.voice(file)
    } else if (file?.type.startsWith('image')) {
      res = await chatApi.image(file, text)
    } else {
      res = await chatApi.text(text)
    }
    const d = res.data
    messages.value.push({
      role: 'assistant',
      content: d.response,
      time: now(),
      meta: {
        intent:               d.intent,
        department:           d.department,
        confidence_score:     d.confidence_score,
        urgency_score:        d.urgency_score,
        hitl_required:        d.hitl_required,
        emergency_dispatched: d.emergency_dispatched,
      },
    })
  } catch (err) {
    messages.value.push({
      role: 'assistant',
      content: '⚠️ ' + (err.response?.data?.detail || 'An error occurred. Please try again.'),
      time: now(),
    })
  } finally {
    loading.value = false
    scrollToBottom()
  }
}
</script>
