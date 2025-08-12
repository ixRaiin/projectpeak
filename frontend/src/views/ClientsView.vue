<script setup>
import { ref, onMounted } from 'vue'
import { useClients } from '@/stores/clients'

const clients = useClients()
const q = ref('')

// form fields
const name = ref('')
const contact_name = ref('')
const email = ref('')
const phone = ref('')
const address = ref('')
const notes = ref('')

const createClient = async () => {
  if (!name.value.trim()) return
  await clients.create({
    name: name.value,
    contact_name: contact_name.value || null,
    email: email.value || null,
    phone: phone.value || null,
    address: address.value || null,
    notes: notes.value || null
  })
  name.value = ''; contact_name.value = ''; email.value = ''
  phone.value = ''; address.value = ''; notes.value = ''
}

const search = async () => clients.fetchAll(q.value)
onMounted(() => clients.fetchAll())
</script>

<template>
  <div class="p-6 space-y-6">
    <div class="flex items-center gap-3">
      <h1 class="text-2xl font-semibold">Clients</h1>
      <input v-model="q" @keyup.enter="search" placeholder="Search…" class="border rounded px-3 py-1" />
      <button class="rounded bg-black text-white px-3 py-1" @click="search">Search</button>
    </div>

    <div class="grid md:grid-cols-2 gap-6">
      <!-- Create form -->
      <form @submit.prevent="createClient" class="space-y-2 border rounded p-4">
        <h2 class="font-semibold">Create client</h2>
        <input v-model="name" placeholder="Name *" class="w-full border rounded p-2" required />
        <input v-model="contact_name" placeholder="Contact name" class="w-full border rounded p-2" />
        <input v-model="email" type="email" placeholder="Email" class="w-full border rounded p-2" />
        <input v-model="phone" placeholder="Phone" class="w-full border rounded p-2" />
        <input v-model="address" placeholder="Address" class="w-full border rounded p-2" />
        <textarea v-model="notes" placeholder="Notes" class="w-full border rounded p-2"></textarea>
        <button class="rounded bg-black text-white px-3 py-2">Add client</button>
        <p v-if="clients.error" class="text-red-600 text-sm mt-1">{{ clients.error }}</p>
      </form>

      <!-- List -->
      <div class="space-y-2">
        <div class="flex items-center justify-between">
          <h2 class="font-semibold">All clients</h2>
          <span class="text-sm text-gray-500">{{ clients.items.length }} total</span>
        </div>
        <div v-if="clients.loading">Loading…</div>
        <ul class="divide-y border rounded">
          <li v-for="c in clients.items" :key="c.id" class="p-3 flex items-start justify-between gap-3">
            <div>
              <div class="font-medium">{{ c.name }}</div>
              <div class="text-sm text-gray-600">
                <span v-if="c.contact_name">{{ c.contact_name }} · </span>
                <span v-if="c.email">{{ c.email }} · </span>
                <span v-if="c.phone">{{ c.phone }}</span>
              </div>
              <div v-if="c.address" class="text-xs text-gray-500">{{ c.address }}</div>
            </div>
            <button class="text-red-600 text-sm" @click="clients.remove(c.id)">Delete</button>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>
