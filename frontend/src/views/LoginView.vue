<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/stores/auth'

const router = useRouter()
const auth = useAuth()

const email = ref('admin@example.com')
const password = ref('')
const submitting = ref(false)

async function submit() {
  submitting.value = true
  try {
    await auth.login(email.value, password.value)
    router.push('/') // go home (or wherever)
  } catch (e) {
    // auth.error already set in store
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="max-w-sm mx-auto p-6 space-y-4">
    <h1 class="text-2xl font-semibold">Login</h1>

    <form @submit.prevent="submit" class="space-y-3">
      <input
        v-model="email"
        type="email"
        placeholder="Email"
        class="w-full border rounded p-2 bg-yellow-100"
        required
      />
      <input
        v-model="password"
        type="password"
        placeholder="Password"
        class="w-full border rounded p-2 bg-yellow-100"
        required
      />

      <button
        :disabled="submitting"
        class="w-full rounded bg-black text-white py-2 disabled:opacity-50"
      >
        {{ submitting ? 'Signing in…' : 'Sign in' }}
      </button>

      <p v-if="auth.error" class="text-red-600 text-sm mt-2">
        {{ auth.error }}
      </p>
    </form>
  </div>
</template>
