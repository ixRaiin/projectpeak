<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useExpenses } from '@/stores/expenses'
import { useProjects } from '@/stores/projects'
import { useCategories } from '@/stores/categories'

const route = useRoute()
const pid = computed(() => Number(route.params.id))
const projects = useProjects()
const expenses = useExpenses()
const categories = useCategories()

const form = ref({
  expense_date: new Date().toISOString().slice(0,10),
  vendor: '',
  memo: '',
  lines: [{ category_id: null, qty: 1, unit_price_usd: null }],
})

function addLine() { form.value.lines.push({ category_id: null, qty: 1, unit_price_usd: null }) }
function removeLine(i) { form.value.lines.splice(i,1) }

async function submitExpense() {
  // minimal validation: at least one valid line
  const lines = form.value.lines
    .filter(l => l.category_id && l.qty > 0 && (l.unit_price_usd ?? 0) >= 0)
    .map(l => ({ category_id: l.category_id, qty: Number(l.qty), unit_price_usd: Number(l.unit_price_usd) }))

  if (!lines.length) return
  await expenses.create(pid.value, {
    expense_date: form.value.expense_date,
    vendor: form.value.vendor || null,
    memo: form.value.memo || null,
    lines,
  })
  // reset quick form
  form.value.vendor = ''
  form.value.memo = ''
  form.value.lines = [{ category_id: null, qty: 1, unit_price_usd: null }]
}

onMounted(async () => {
  if (!projects.items.length) await projects.fetchAll()
  if (!categories.items.length) await categories.fetchAll()
  await expenses.fetchForProject(pid.value)
})
</script>

<template>
  <div class="p-6 space-y-6">
    <h1 class="text-2xl font-semibold">Project {{ pid }}</h1>

    <!-- Quick add expense -->
    <form @submit.prevent="submitExpense" class="space-y-3 border rounded p-4">
      <div class="grid md:grid-cols-4 gap-3">
        <label class="block">
          <span class="text-sm text-gray-600">Date</span>
          <input v-model="form.expense_date" type="date" class="w-full border rounded p-2" required>
        </label>
        <input v-model="form.vendor" placeholder="Vendor" class="border rounded p-2">
        <input v-model="form.memo" placeholder="Memo" class="border rounded p-2 md:col-span-2">
      </div>

      <div class="space-y-2">
        <div v-for="(l,i) in form.lines" :key="i" class="grid md:grid-cols-4 gap-2">
          <select v-model.number="l.category_id" class="border rounded p-2" required>
            <option :value="null" disabled>Select category…</option>
            <option v-for="c in categories.items" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>
          <input v-model.number="l.qty" type="number" min="0" step="0.01" placeholder="Qty" class="border rounded p-2">
          <input v-model.number="l.unit_price_usd" type="number" min="0" step="0.01" placeholder="Unit price (USD)" class="border rounded p-2">
          <button type="button" class="border rounded p-2" @click="removeLine(i)">Remove</button>
        </div>
        <button type="button" class="rounded px-3 py-1 border" @click="addLine">+ Add line</button>
      </div>

      <button class="rounded bg-black text-white px-3 py-2">Save expense</button>
      <p v-if="expenses.error" class="text-red-600 text-sm">{{ expenses.error }}</p>
    </form>

    <!-- List -->
    <div>
      <h2 class="font-semibold">Expenses</h2>
      <div v-if="expenses.loading">Loading…</div>
      <ul class="divide-y border rounded">
        <li v-for="e in expenses.items" :key="e.id" class="p-3">
          <div class="font-medium">{{ e.expense_date }} — {{ e.vendor || '—' }}</div>
          <div class="text-sm text-gray-600">{{ e.memo }}</div>
          <div class="text-sm mt-1">
            <span v-for="ln in e.lines" :key="ln.id" class="mr-3">
              #{{ ln.category_id }} · {{ ln.qty }} × ${{ ln.unit_price_usd }} = ${{ ln.line_total_usd }}
            </span>
          </div>
        </li>
      </ul>
    </div>
  </div>
</template>
