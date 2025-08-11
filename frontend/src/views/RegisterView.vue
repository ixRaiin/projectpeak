<script setup>
import { ref } from 'vue';
import { useAuth } from '@/stores/auth';
import { useRouter } from 'vue-router';

const name = ref('');
const email = ref('');
const password = ref('');
const auth = useAuth();
const router = useRouter();

const submit = async () => {
  try { await auth.register({ name: name.value, email: email.value, password: password.value }); router.push('/'); }
  catch (err) {
    auth.error = err?.message || 'Registration failed';
  }
};
</script>

<template>
  <div class="min-h-screen flex items-center justify-center p-6">
    <form @submit.prevent="submit" class="w-full max-w-sm space-y-4">
      <h1 class="text-2xl font-semibold">Register</h1>
      <input v-model="name" placeholder="Name" class="w-full border rounded p-2" required />
      <input v-model="email" type="email" placeholder="Email" class="w-full border rounded p-2" required />
      <input v-model="password" type="password" placeholder="Password (min 8)" class="w-full border rounded p-2" required />
      <button class="w-full rounded bg-black text-white py-2">Create account</button>
      <p v-if="auth.error" class="text-red-600 text-sm">{{ auth.error }}</p>
    </form>
  </div>
</template>
