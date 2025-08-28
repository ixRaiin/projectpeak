<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useProjects } from '@/stores/projects'
import { useClients } from '@/stores/clients'

const router = useRouter()
const projects = useProjects()
const clients = useClients()

const error = ref(null)
const submitting = ref(false)
const fieldErr = ref({})
const nextCodePreview = ref('')

const form = ref({
  client_id: '',
  name: '',
  description: '',
  status: 'planned',
  start_date: '',
  end_date: '',
  budget_amount_usd: '',
  tax_rate: '',
  currency: 'USD',
})

function validate() {
  fieldErr.value = {}
  if (!form.value.client_id) fieldErr.value.client_id = 'Client is required.'
  if (!form.value.name.trim()) fieldErr.value.name = 'Name is required.'

  // If both dates are set, ensure end >= start
  if (form.value.start_date && form.value.end_date) {
    if (form.value.end_date < form.value.start_date) {
      fieldErr.value.date_range = 'End date cannot be earlier than start date.'
    }
  }
  return Object.keys(fieldErr.value).length === 0
}

const submit = async () => {
  error.value = null
  if (submitting.value) return
  if (!validate()) return

  try {
    submitting.value = true
    const payload = { ...form.value }
    payload.client_id = Number(payload.client_id)
    if (!payload.client_id) throw new Error('Please select a client.')

    if (payload.budget_amount_usd === '' || payload.budget_amount_usd === null) {
      delete payload.budget_amount_usd
    } else {
      payload.budget_amount_usd = Number(payload.budget_amount_usd)
    }

    if (payload.tax_rate === '' || payload.tax_rate === null) {
      delete payload.tax_rate
    } else {
      payload.tax_rate = Number(payload.tax_rate)
    }
    delete payload.code

    const created = await projects.create(payload)
    const id = created?.id
    router.replace(id ? { name: 'project-detail', params: { id } } : { name: 'projects' })
  } catch (e) {
    error.value = e?.message || 'Failed to create project'
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  if (!clients.items.length) {
    try { await clients.fetchAll() } catch {/* ignore */}
  }
  try {
    if (projects && typeof projects.peekNextCode === 'function') {
      const res = await projects.peekNextCode()
      nextCodePreview.value = res?.next || ''
    }
  } catch {/* optional enhancement; ignore errors */}
})
</script>

<template>
  <div class="p-6 max-w-3xl mx-auto">
    <!-- Header -->
    <div class="mb-5 flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-semibold">Create Project</h1>
        <p class="text-sm text-gray-600 mt-1">
          Project code will be <span class="font-medium">auto‑generated</span>
          <span v-if="nextCodePreview" class="inline-flex items-center gap-1 ml-2 text-gray-700">
            (e.g., <span class="font-mono">{{ nextCodePreview }}</span>)
          </span>
        </p>
      </div>
    </div>

    <!-- Form Card -->
    <form @submit.prevent="submit" class="space-y-6 rounded-2xl border bg-white p-5 shadow-sm">
      <!-- Client & Status -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <label class="block">
          <span class="text-sm text-gray-600">Client *</span>
          <select v-model="form.client_id" required class="mt-1 w-full border rounded-lg p-2.5 focus:outline-none focus:ring-2 focus:ring-black/30">
            <option value="" disabled>Select client…</option>
            <option v-for="c in clients.items" :key="c.id" :value="String(c.id)">{{ c.name }}</option>
          </select>
          <p v-if="fieldErr.client_id" class="text-xs text-red-600 mt-1">{{ fieldErr.client_id }}</p>
        </label>

        <label class="block">
          <span class="text-sm text-gray-600">Status</span>
          <select v-model="form.status" class="mt-1 w-full border rounded-lg p-2.5 focus:outline-none focus:ring-2 focus:ring-black/30">
            <option value="planned">Planned</option>
            <option value="active">Active</option>
            <option value="completed">Completed</option>
          </select>
        </label>
      </div>

      <!-- Name (code removed) -->
      <div class="grid grid-cols-1">
        <label class="block">
          <span class="text-sm text-gray-600">Name *</span>
          <input v-model="form.name" required placeholder="Project name" class="mt-1 w-full border rounded-lg p-2.5 focus:outline-none focus:ring-2 focus:ring-black/30" />
          <p v-if="fieldErr.name" class="text-xs text-red-600 mt-1">{{ fieldErr.name }}</p>
        </label>
      </div>

      <!-- Description -->
      <label class="block">
        <span class="text-sm text-gray-600">Description</span>
        <textarea v-model="form.description" class="mt-1 w-full border rounded-lg p-2.5 focus:outline-none focus:ring-2 focus:ring-black/30" rows="3" placeholder="Optional notes about this project…"></textarea>
      </label>

      <!-- Dates -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <label class="block">
          <span class="text-sm text-gray-600">Start date</span>
          <input v-model="form.start_date" type="date" class="mt-1 w-full border rounded-lg p-2.5 focus:outline-none focus:ring-2 focus:ring-black/30" />
        </label>
        <label class="block">
          <span class="text-sm text-gray-600">End date</span>
          <input v-model="form.end_date" type="date" class="mt-1 w-full border rounded-lg p-2.5 focus:outline-none focus:ring-2 focus:ring-black/30" />
          <p v-if="fieldErr.date_range" class="text-xs text-red-600 mt-1">{{ fieldErr.date_range }}</p>
        </label>
      </div>

      <!-- Money -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <label class="block">
          <span class="text-sm text-gray-600">Budget (USD)</span>
          <input v-model="form.budget_amount_usd" type="number" step="0.01" inputmode="decimal" class="mt-1 w-full border rounded-lg p-2.5 focus:outline-none focus:ring-2 focus:ring-black/30" />
        </label>
        <label class="block">
          <span class="text-sm text-gray-600">Tax rate (e.g., 0.05)</span>
          <input v-model="form.tax_rate" type="number" step="0.0001" inputmode="decimal" class="mt-1 w-full border rounded-lg p-2.5 focus:outline-none focus:ring-2 focus:ring-black/30" />
        </label>
        <label class="block">
          <span class="text-sm text-gray-600">Currency</span>
          <select v-model="form.currency" class="mt-1 w-full border rounded-lg p-2.5 focus:outline-none focus:ring-2 focus:ring-black/30">
            <option value="USD">USD</option>
            <option value="KWD">KWD</option>
            <option value="EUR">EUR</option>
            <option value="GBP">GBP</option>
          </select>
        </label>
      </div>

      <!-- Actions -->
      <div class="flex items-center gap-2 pt-2">
        <button
          class="px-4 py-2 rounded-xl bg-black text-white focus:outline-none focus:ring-2 focus:ring-black/40 disabled:opacity-50"
          :disabled="submitting"
        >
          {{ submitting ? 'Creating…' : 'Create Project' }}
        </button>
        <RouterLink class="px-4 py-2 rounded-xl border hover:bg-gray-50" :to="{ name: 'projects' }">
          Cancel
        </RouterLink>
        <span class="ml-auto text-xs text-gray-500">Fields marked * are required</span>
      </div>

      <p v-if="error" class="text-red-600 text-sm">{{ error }}</p>
    </form>
  </div>
</template>

<style scoped>
/* Minimal, clean spacing tweaks for inputs */
input, select, textarea { transition: box-shadow 0.15s ease; }
</style>
