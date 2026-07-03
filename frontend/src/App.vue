<template>
  <div class="min-h-screen bg-slate-50">
    <NavBar v-if="auth.isLoggedIn" />
    <router-view />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useAuthStore } from './stores/auth'
import NavBar from './components/NavBar.vue'

const auth = useAuthStore()
onMounted(() => { if (auth.token) auth.fetchProfile() })
</script>
