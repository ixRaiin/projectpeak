<script setup>
import { useRouter } from 'vue-router'
import { useAuth } from '@/stores/auth'

const router = useRouter()
const auth = useAuth()

async function doLogout() {
  await auth.logout()
  // Send user to a public page; the guard will not try to load protected views
  router.replace({ path: '/login' })
}
</script>

<template>
  <div class="p-6 space-y-4">
    <h1 class="text-2xl font-semibold">Welcome</h1>
    <p class="text-gray-600">You are logged in as: <strong>{{ auth.user?.name || auth.user?.email }}</strong></p>

    <div class="flex gap-3">
      <router-link to="/projects" class="underline">Projects</router-link>
      <router-link to="/catalog" class="underline">Catalog</router-link>
      <router-link to="/clients" class="underline">Clients</router-link>
    </div>

    <button
      type="button"
      class="mt-4 rounded bg-black text-white px-3 py-2"
      @click="doLogout"
    >
      Logout
    </button>
  </div>
</template>
