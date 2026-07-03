<template>
  <nav class="sticky top-0 z-50 bg-white border-b border-slate-100 shadow-sm">
    <div class="mx-auto max-w-5xl px-4 h-16 flex items-center justify-between">

      <!-- Logo -->
      <router-link to="/" class="flex items-center gap-2.5 font-bold text-medical-700 text-lg">
        <span class="text-2xl">🏥</span>
        MediAssist AI
      </router-link>

      <!-- Nav links -->
      <div class="hidden sm:flex items-center gap-1">
        <router-link
          v-for="link in links"
          :key="link.to"
          :to="link.to"
          class="px-3 py-2 rounded-lg text-sm font-medium text-slate-600
                 hover:bg-slate-100 hover:text-slate-900 transition-colors"
          active-class="bg-medical-50 text-medical-700 hover:bg-medical-50"
        >
          <span class="mr-1.5">{{ link.icon }}</span>{{ link.label }}
        </router-link>
      </div>

      <!-- User info + logout -->
      <div class="flex items-center gap-3">
        <div class="hidden sm:flex items-center gap-2 px-3 py-1.5 bg-amber-50 rounded-full">
          <span class="text-amber-500">⭐</span>
          <span class="text-sm font-semibold text-amber-700">{{ auth.loyaltyPoints }} pts</span>
        </div>
        <div class="w-9 h-9 rounded-full bg-medical-600 flex items-center justify-center
                    text-white text-sm font-bold select-none">
          {{ initials }}
        </div>
        <button @click="logout" class="btn-ghost text-slate-400 hover:text-red-500 px-2">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- Mobile nav -->
    <div class="sm:hidden flex border-t border-slate-100">
      <router-link
        v-for="link in links"
        :key="link.to"
        :to="link.to"
        class="flex-1 py-2.5 flex flex-col items-center gap-0.5 text-xs text-slate-500
               hover:text-medical-600 transition-colors"
        active-class="text-medical-600"
      >
        <span class="text-lg">{{ link.icon }}</span>
        {{ link.label }}
      </router-link>
    </div>
  </nav>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()
const initials = computed(() => {
  const p = auth.patient
  if (!p) return '?'
  return `${p.first_name?.[0] ?? ''}${p.last_name?.[0] ?? ''}`.toUpperCase()
})
const links = [
  { to: '/',              icon: '💬', label: 'Chat'          },
  { to: '/appointments',  icon: '📅', label: 'Appointments'  },
  { to: '/prescriptions', icon: '💊', label: 'Prescriptions' },
  { to: '/profile',       icon: '👤', label: 'Profile'       },
]
function logout() {
  auth.logout()
  router.push('/login')
}
</script>
