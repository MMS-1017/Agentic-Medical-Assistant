<template>
  <div class="min-h-screen bg-gradient-to-br from-medical-900 via-medical-700 to-medical-500
              flex items-center justify-center p-4">
    <div class="w-full max-w-md">

      <!-- Logo card -->
      <div class="text-center mb-8">
        <div class="inline-flex items-center justify-center w-20 h-20 rounded-2xl
                    bg-white/10 backdrop-blur text-5xl mb-4 shadow-xl">
          🏥
        </div>
        <h1 class="text-3xl font-bold text-white">MediAssist AI</h1>
        <p class="text-medical-100 mt-1 text-sm">Your intelligent medical companion</p>
      </div>

      <!-- Form card -->
      <div class="bg-white rounded-2xl shadow-2xl p-8">
        <!-- Tabs -->
        <div class="flex rounded-xl bg-slate-100 p-1 mb-6">
          <button
            v-for="tab in ['Login', 'Register']"
            :key="tab"
            @click="activeTab = tab"
            class="flex-1 py-2 text-sm font-medium rounded-lg transition-all"
            :class="activeTab === tab
              ? 'bg-white text-medical-700 shadow-sm'
              : 'text-slate-500 hover:text-slate-700'"
          >
            {{ tab }}
          </button>
        </div>

        <!-- Error -->
        <div v-if="auth.error" class="mb-4 px-4 py-3 bg-red-50 border border-red-100 rounded-xl
                                       text-sm text-red-700">
          ⚠️ {{ auth.error }}
        </div>

        <!-- Login form -->
        <form v-if="activeTab === 'Login'" @submit.prevent="handleLogin" class="space-y-4">
          <div>
            <label class="block text-xs font-semibold text-slate-600 mb-1.5">Email</label>
            <input v-model="loginForm.email" type="email" class="input" placeholder="you@example.com" required />
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-600 mb-1.5">Password</label>
            <input v-model="loginForm.password" type="password" class="input" placeholder="••••••••" required />
          </div>
          <button type="submit" class="btn-primary w-full mt-2" :disabled="auth.loading">
            <svg v-if="auth.loading" class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
            </svg>
            {{ auth.loading ? 'Signing in…' : 'Sign in' }}
          </button>
          <p class="text-center text-xs text-slate-400 mt-3">
            Demo: <span class="font-mono text-slate-600">ahmed.m@example.com / Password123!</span>
          </p>
        </form>

        <!-- Register form -->
        <form v-else @submit.prevent="handleRegister" class="space-y-4">
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-semibold text-slate-600 mb-1.5">First name</label>
              <input v-model="registerForm.first_name" class="input" placeholder="Ahmed" required />
            </div>
            <div>
              <label class="block text-xs font-semibold text-slate-600 mb-1.5">Last name</label>
              <input v-model="registerForm.last_name" class="input" placeholder="Mohamed" required />
            </div>
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-600 mb-1.5">Email</label>
            <input v-model="registerForm.email" type="email" class="input" placeholder="you@example.com" required />
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-600 mb-1.5">Phone</label>
            <input v-model="registerForm.phone" class="input" placeholder="+201001234567" />
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-600 mb-1.5">Password</label>
            <input v-model="registerForm.password" type="password" class="input" placeholder="••••••••" required />
          </div>
          <button type="submit" class="btn-primary w-full mt-2" :disabled="auth.loading">
            {{ auth.loading ? 'Creating account…' : 'Create account' }}
          </button>
        </form>
      </div>

      <p class="text-center text-medical-100 text-xs mt-6">
        🔒 Your data is encrypted and protected
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth   = useAuthStore()
const router = useRouter()
const route  = useRoute()

const activeTab = ref('Login')
const loginForm = ref({ email: '', password: '' })
const registerForm = ref({ first_name: '', last_name: '', email: '', phone: '', password: '' })

async function handleLogin() {
  const ok = await auth.login(loginForm.value.email, loginForm.value.password)
  if (ok) router.push(route.query.redirect || '/')
}
async function handleRegister() {
  const ok = await auth.register(registerForm.value)
  if (ok) router.push('/')
}
</script>
