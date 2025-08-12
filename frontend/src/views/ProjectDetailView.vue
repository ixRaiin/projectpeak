<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useProjects } from '@/stores/projects'
import { useCategories } from '@/stores/categories'
import { useExpenses } from '@/stores/expenses'

const route = useRoute()
const pid = Number(route.params.id)

const projects = useProjects()
const categories = useCategories()
const expenses = useExpenses()

const form = ref({
  expense_date: new Date().toISOString().slice(0,10),
  vendor: '', reference_no: '', note: '',
  lines: [{ category_id: null, description: '', quantity: 1, unit_price_usd: 0 }]
})

const addLine = () => form.value.lines.push({ category_id: null, description: '', quantity: 1, unit_price_usd: 0 })
const rmLine = (i) => form.value.lines.splice(i, 1)

const submit = async () => {
  // drop empty lines
  form.value.lines = form.value.lines.filter(l => l.category_id && (l.quantity || l.unit_price_usd))
  if (!form.value.lines.length) return
  await expenses.create(pid, form.value)
  form.value.vendor = ''; form.value.reference_no = ''; form.value.note = ''
  form.value.lines = [{ category_id: null, description: '', quantity: 1, unit_price_usd: 0 }]
}

onMounted(async () => {
  if (!projects.items.length) await projects.fetchAll()
  if (!categories.items.length) await categories.fetchAll()
  await expenses.fetchByProject(pid)
})

const project = computed(() => projects.items.find(p => p.id === pid))
const catName = (id) => categories.items.find(c => c.id === id)?.name || `#${id}`
</script>

<template>
  <div class="p-6 space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-semibold">Project {{ project?.code }} — {{ project?.name }}</h1>
      <router-link to="/projects" class="underline text-sm">Back to Projects</router-link>
    </div>

    <!-- Create expense -->
    <form @submit.prevent="submit" class="border rounded p-4 space-y-3">
      <h2 class="font-semibold">Add Expense</h2>
      <div class="grid md:grid-cols-3 gap-3">
        <label class="block">
          <span class="text-sm text-gray-600">Date</span>
          <input v-model="form.expense_date" type="date" class="border rounded p-2 w-full" />
        </label>
        <input v-model="form.vendor" placeholder="Vendor" class="border rounded p-2" />
        <input v-model="form.reference_no" placeholder="Reference / Invoice #" class="border rounded p-2" />
      </div>
      <textarea v-model="form.note" placeholder="Note" class="border rounded p-2 w-full"></textarea>

      <div class="space-y-2">
        <div class="grid grid-cols-12 text-sm font-medium text-gray-600">
          <div class="col-span-4">Category</div>
          <div class="col-span-4">Description</div>
          <div class="col-span-2">Qty</div>
          <div class="col-span-2">Unit (USD)</div>
        </div>
        <div v-for="(ln, i) in form.lines" :key="i" class="grid grid-cols-12 gap-2 items-center">
          <select v-model.number="ln.category_id" class="border rounded p-2 col-span-4">
            <option :value="null" disabled>Select category…</option>
            <option v-for="c in categories.items" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>
          <input v-model="ln.description" placeholder="Description" class="border rounded p-2 col-span-4" />
          <input v-model.number="ln.quantity" type="number" step="0.01" class="border rounded p-2 col-span-2" />
          <div class="col-span-2 flex gap-2">
            <input v-model.number="ln.unit_price_usd" type="number" step="0.01" class="border rounded p-2 w-full" />
            <button type="button" class="px-2 text-red-600" @click="rmLine(i)" v-if="form.lines.length>1">✕</button>
          </div>
        </div>
        <button type="button" class="underline text-sm" @click="addLine">+ Add line</button>
      </div>

      <button class="bg-black text-white rounded px-3 py-2">Save Expense</button>
    </form>

    <!-- List expenses -->
    <div>
      <div class="flex items-center justify-between">
        <h2 class="font-semibold">Expenses</h2>
        <span class="text-sm text-gray-500">{{ expenses.items.length }} total</span>
      </div>
      <div v-if="expenses.loading">Loading…</div>
      <p v-if="expenses.error" class="text-red-600 text-sm">{{ expenses.error }}</p>
      <ul class="divide-y border rounded">
        <li v-for="e in expenses.items" :key="e.id" class="p-3 space-y-2">
          <div class="flex items-center justify-between">
            <div class="font-medium">{{ e.expense_date }} — {{ e.vendor || '—' }} <span class="text-gray-500">({{ e.reference_no || '—' }})</span></div>
            <div class="text-sm">Total: ${{ e.total_usd.toFixed(2) }}</div>
          </div>
          <ul class="text-sm text-gray-700">
            <li v-for="ln in e.lines" :key="ln.id">
              {{ catName(ln.category_id) }} — {{ ln.description || '—' }} · {{ ln.quantity }} × ${{ ln.unit_price_usd }} = ${{ ln.line_total_usd }}
            </li>
          </ul>
          <div class="text-xs text-gray-500">Subtotal ${{ e.subtotal_usd }} · Tax ${{ e.tax_usd }}</div>
          <button class="text-red-600 text-sm" @click="expenses.remove(e.id)">Delete</button>
        </li>
      </ul>
    </div>
  </div>
</template>
