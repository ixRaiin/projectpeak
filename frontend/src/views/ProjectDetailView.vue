<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useProjects } from '@/stores/projects'
import { useExpenses } from '@/stores/expenses'
import { useCategories } from '@/stores/categories'
import { api } from '@/lib/api'

const route = useRoute()
const pid = computed(() => Number(route.params.id))

const projects = useProjects()
const expenses = useExpenses()
const categories = useCategories()

const project = computed(() => projects.items.find(p => p.id === pid.value) || null)
const summary = ref(null)
const loadingSummary = ref(false)
const sumErr = ref(null)

const form = ref({
  expense_date: new Date().toISOString().slice(0,10),
  vendor: '',
  memo: '',
  lines: [{ category_id: null, qty: 1, unit_price_usd: null }],
})

function addLine() { form.value.lines.push({ category_id: null, qty: 1, unit_price_usd: null }) }
function removeLine(i) { form.value.lines.splice(i, 1) }

const canSubmit = computed(() => {
  if (!form.value.expense_date) return false
  if (!form.value.lines.length) return false
  return form.value.lines.every(l =>
    l.category_id && Number(l.qty) > 0 && (l.unit_price_usd === 0 || Number(l.unit_price_usd) > 0)
  )
})

function fmtUSD(v) {
  if (v == null) return '—'
  const n = Number(v)
  if (Number.isNaN(n)) return String(v)
  return new Intl.NumberFormat(undefined, { style: 'currency', currency: 'USD' }).format(n)
}

async function loadSummary() {
  loadingSummary.value = true; sumErr.value = null
  try {
    summary.value = await api().get(`/projects/${pid.value}/summary`)
  } catch (e) {
    sumErr.value = e?.error || 'Failed to load summary'
  } finally {
    loadingSummary.value = false
  }
}

async function submitExpense() {
  if (!canSubmit.value) return
  const payload = {
    expense_date: form.value.expense_date,
    vendor: form.value.vendor || null,
    memo: form.value.memo || null,
    lines: form.value.lines.map(l => ({
      category_id: l.category_id,
      qty: Number(l.qty),
      unit_price_usd: Number(l.unit_price_usd),
    })),
  }
  await expenses.create(pid.value, payload)
  await loadSummary()
  // reset
  form.value.vendor = ''
  form.value.memo = ''
  form.value.lines = [{ category_id: null, qty: 1, unit_price_usd: null }]
}

onMounted(async () => {
  if (!project.value) await projects.fetchOne(pid.value)
  if (!categories.items.length) await categories.fetchAll()
  await expenses.fetchForProject(pid.value)
  await loadSummary()
})
</script>

<template>
  <div class="p-6 space-y-8">
    <header class="flex items-end justify-between">
      <div>
        <h1 class="text-2xl font-semibold">
          {{ project ? (project.code + ' — ' + project.name) : 'Project' }}
        </h1>
        <p v-if="project" class="text-sm text-gray-600">
          Client #{{ project.client_id }}
          <span v-if="project.start_date"> · Start {{ project.start_date }}</span>
          <span v-if="project.end_date"> · End {{ project.end_date }}</span>
        </p>
      </div>
    </header>

    <!-- Summary -->
    <section class="border rounded p-4">
      <div class="flex items-center justify-between mb-3">
        <h2 class="font-semibold">Planned vs Actual</h2>
        <button class="text-sm border rounded px-2 py-1" @click="loadSummary">Refresh</button>
      </div>
      <div v-if="loadingSummary">Loading summary…</div>
      <p v-if="sumErr" class="text-red-600 text-sm">{{ sumErr }}</p>

      <div v-if="summary">
        <div class="overflow-x-auto">
          <table class="min-w-full text-sm">
            <thead>
              <tr class="text-left border-b">
                <th class="py-2 pr-4">Category</th>
                <th class="py-2 pr-4">Planned</th>
                <th class="py-2 pr-4">Actual</th>
                <th class="py-2 pr-4">Variance</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in summary.per_category" :key="row.category_id" class="border-b">
                <td class="py-2 pr-4">{{ row.category_name || ('#' + row.category_id) }}</td>
                <td class="py-2 pr-4">{{ fmtUSD(row.planned_usd) }}</td>
                <td class="py-2 pr-4">{{ fmtUSD(row.actual_usd) }}</td>
                <td class="py-2 pr-4">{{ fmtUSD(row.variance_usd) }}</td>
              </tr>
            </tbody>
            <tfoot>
              <tr class="font-medium">
                <td class="py-2 pr-4">Totals</td>
                <td class="py-2 pr-4">{{ fmtUSD(summary.totals.planned_total_usd) }}</td>
                <td class="py-2 pr-4">{{ fmtUSD(summary.totals.actual_total_usd) }}</td>
                <td class="py-2 pr-4">{{ fmtUSD(summary.totals.variance_total_usd) }}</td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>
    </section>

    <!-- Add Expense -->
    <section class="border rounded p-4 space-y-3">
      <h2 class="font-semibold">Add Expense</h2>
      <form @submit.prevent="submitExpense" class="space-y-3">
        <div class="grid md:grid-cols-4 gap-3">
          <input v-model="form.expense_date" type="date" class="border rounded p-2" required>
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
          <button type="button" class="border rounded px-3 py-1" @click="addLine">+ Add line</button>
        </div>

        <div class="flex items-center gap-3">
          <button :disabled="!canSubmit" class="rounded px-3 py-2 text-white"
                  :class="canSubmit ? 'bg-black' : 'bg-gray-400 cursor-not-allowed'">
            Save expense
          </button>
          <span v-if="expenses.error" class="text-red-600 text-sm">{{ expenses.error }}</span>
        </div>
      </form>
    </section>

    <!-- Expense List -->
    <section>
      <h2 class="font-semibold mb-2">Expenses</h2>
      <div v-if="expenses.loading">Loading…</div>
      <ul v-else class="divide-y border rounded">
        <li v-for="e in expenses.items" :key="e.id" class="p-3 space-y-1">
          <div class="flex items-center justify-between">
            <div class="font-medium">
              {{ e.expense_date }} — {{ e.vendor || '—' }}
            </div>
            <div class="text-sm text-gray-600">{{ e.reference_no || '' }}</div>
          </div>
          <div class="text-sm text-gray-600">{{ e.memo }}</div>
          <div class="text-sm mt-1">
            <span v-for="ln in e.lines" :key="ln.id" class="mr-4">
              {{ ln.category_id }} · {{ ln.qty }} × {{ fmtUSD(ln.unit_price_usd) }}
              = <strong>{{ fmtUSD(ln.line_total_usd) }}</strong>
            </span>
          </div>
        </li>
      </ul>
    </section>
  </div>
</template>
