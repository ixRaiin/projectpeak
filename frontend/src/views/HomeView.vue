<script setup>
import { useAuth } from '@/stores/auth'
import { useRouter } from 'vue-router'
const auth = useAuth()
const router = useRouter()

const doLogout = async () => {
  await auth.logout()
  router.push('/login')
}
</script>

<template>
  <div class="p-6 space-y-4">
    <h1 class="text-2xl font-semibold">ProjectPeak</h1>
    <p v-if="auth.user">Welcome, <span class="font-medium">{{ auth.user.name }}</span>!</p>
    <div class="flex gap-4 p-4 border-b">
      <RouterLink to="/projects" class="underline">Projects</RouterLink>
      <RouterLink to="/catalog" class="underline">Catalog</RouterLink>
      <RouterLink to="/clients">Clients</RouterLink>
      <RouterLink to="/categories">Categories</RouterLink>
      <RouterLink to="/components">Components</RouterLink>
      <button class="rounded bg-black text-white px-3 py-1" @click="doLogout">Logout</button>
    </div>
  </div>
</template>
