<template>
  <!-- Patient message (right) -->
  <div v-if="msg.role === 'user'" class="flex justify-end gap-3 items-end">
    <div class="max-w-[78%]">
      <!-- File preview -->
      <div v-if="msg.file" class="mb-1.5 flex justify-end">
        <span class="text-xs text-slate-400 italic">{{ msg.file }}</span>
      </div>
      <div class="bg-medical-600 text-white rounded-2xl rounded-br-sm px-4 py-3 text-sm leading-relaxed shadow-sm">
        {{ msg.content }}
      </div>
      <p class="text-right text-xs text-slate-400 mt-1">{{ msg.time }}</p>
    </div>
    <div class="w-8 h-8 rounded-full bg-medical-500 flex-shrink-0 flex items-center
                justify-center text-white text-xs font-bold mb-5">
      {{ initials }}
    </div>
  </div>

  <!-- AI message (left) -->
  <div v-else class="flex gap-3 items-end">
    <div class="w-8 h-8 rounded-full bg-white border-2 border-medical-200 flex-shrink-0
                flex items-center justify-center text-lg mb-5">
      🏥
    </div>
    <div class="max-w-[78%]">
      <div class="bg-white border border-slate-100 rounded-2xl rounded-bl-sm
                  px-4 py-3 text-sm leading-relaxed text-slate-800 shadow-sm">
        {{ msg.content }}
      </div>

      <!-- Metadata badges -->
      <div v-if="msg.meta" class="flex flex-wrap gap-1.5 mt-2">
        <span v-if="msg.meta.intent" class="badge bg-slate-100 text-slate-600">
          {{ intentIcon(msg.meta.intent) }} {{ msg.meta.intent }}
        </span>
        <span v-if="msg.meta.department" class="badge bg-medical-50 text-medical-700">
          🏨 {{ msg.meta.department }}
        </span>
        <span v-if="msg.meta.confidence_score != null" :class="confidenceBadge(msg.meta.confidence_score)">
          🎯 {{ pct(msg.meta.confidence_score) }} confidence
        </span>
        <span v-if="msg.meta.urgency_score != null" :class="urgencyBadge(msg.meta.urgency_score)">
          {{ urgencyIcon(msg.meta.urgency_score) }} {{ pct(msg.meta.urgency_score) }} urgency
        </span>
        <span v-if="msg.meta.hitl_required" class="badge bg-yellow-50 text-yellow-700">
          👨‍⚕️ Doctor review requested
        </span>
        <span v-if="msg.meta.emergency_dispatched" class="badge bg-red-50 text-red-700 animate-pulse">
          🚨 Emergency dispatched
        </span>
      </div>

      <p class="text-xs text-slate-400 mt-1">{{ msg.time }}</p>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  msg: Object,
  initials: { type: String, default: 'P' },
})
const pct = (v) => `${Math.round(v * 100)}%`
const intentIcon = (i) => ({ scheduling: '📅', diagnosis: '🔬', emergency: '🚨', feedback: '📝' }[i] || '💬')
const confidenceBadge = (v) =>
  v >= 0.8 ? 'badge bg-green-50 text-green-700' : v >= 0.7 ? 'badge bg-yellow-50 text-yellow-700' : 'badge bg-red-50 text-red-700'
const urgencyBadge = (v) =>
  v >= 0.85 ? 'badge bg-red-50 text-red-700' : v >= 0.6 ? 'badge bg-orange-50 text-orange-700' : 'badge bg-green-50 text-green-700'
const urgencyIcon = (v) => v >= 0.85 ? '🔴' : v >= 0.6 ? '🟡' : '🟢'
</script>
