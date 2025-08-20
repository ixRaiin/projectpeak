<template>
  <div class="p-6 max-w-6xl mx-auto space-y-6">
    <!-- Header -->
    <div class="flex items-start justify-between gap-3">
      <div>
        <h1 class="text-2xl font-semibold">{{ project?.name || 'Project' }}</h1>
        <p class="text-sm text-gray-600">
          <span class="inline-flex items-center px-2 py-0.5 rounded bg-gray-100 text-gray-800">
            {{ project?.status || 'planned' }}
          </span>
          <span v-if="project?.code" class="ml-2 text-gray-500">#{{ project.code }}</span>
        </p>
      </div>
      <div class="min-w-[200px]">
        <div class="h-2 bg-gray-100 rounded">
          <div class="m-3 h-2 rounded bg-black" :style="{ width: (localProgress ?? project?.progress_percent ?? 0) + '%' }"></div>
        </div>
      </div>
    </div>

    <!-- Tabs -->
    <div class="border-b">
      <nav class="flex gap-6 -mb-px text-sm">
        <button :class="tabBtn('details')" @click="goTab('details')">Project Details</button>
        <button :class="tabBtn('expenses')" @click="goTab('expenses')">Expenses</button>
        <button :class="tabBtn('tasks')" @click="goTab('tasks')">Tasks</button>
      </nav>
    </div>

    <!-- Project Details -->
    <div v-if="activeTab === 'details'" class="space-y-6">
      <h2 class="text-xl font-semibold">Project Details</h2>

      <form @submit.prevent="saveEdits" class="space-y-4 max-w-3xl">
        <div class="grid md:grid-cols-2 gap-4">
          <label class="block">
            <span class="block text-sm text-gray-600">Name *</span>
            <input v-model="form.name" class="w-full border rounded p-2" required />
          </label>

          <label class="block">
            <span class="block text-sm text-gray-600">Code</span>
            <input v-model="form.code" class="w-full border rounded p-2" />
          </label>

          <label class="block">
            <span class="block text-sm text-gray-600">Client</span>
            <select v-model.number="form.client_id" class="w-full border rounded p-2">
              <option v-for="c in clients.items" :key="c.id" :value="c.id">{{ c.name }}</option>
            </select>
          </label>

          <label class="block">
            <span class="block text-sm text-gray-600">Status</span>
            <select v-model="form.status" class="w-full border rounded p-2">
              <option value="planned">Planned</option>
              <option value="active">Active</option>
              <option value="completed">Completed</option>
            </select>
          </label>

          <label class="block">
            <span class="block text-sm text-gray-600">Start Date</span>
            <input type="date" v-model="form.start_date" class="w-full border rounded p-2" />
          </label>

          <label class="block">
            <span class="block text-sm text-gray-600">End Date</span>
            <input type="date" v-model="form.end_date" class="w-full border rounded p-2" />
          </label>

          <label class="block">
            <span class="block text-sm text-gray-600">Budget (USD)</span>
            <input type="number" step="0.01" v-model="form.budget_amount_usd" class="w-full border rounded p-2" />
          </label>

          <label class="block">
            <span class="block text-sm text-gray-600">Tax Rate (e.g., 0.05)</span>
            <input type="number" step="0.0001" v-model="form.tax_rate" class="w-full border rounded p-2" />
          </label>

          <label class="block">
            <span class="block text-sm text-gray-600">Currency</span>
            <input v-model="form.currency" class="w-full border rounded p-2" />
          </label>
        </div>

        <label class="block">
          <span class="block text-sm text-gray-600">Description</span>
          <textarea v-model="form.description" rows="3" class="w-full border rounded p-2"></textarea>
        </label>

        <div class="flex gap-3">
          <button type="submit" class="px-4 py-2 rounded bg-black text-white" :disabled="saving">
            {{ saving ? 'Saving…' : 'Save Changes' }}
          </button>
          <button type="button" class="px-4 py-2 rounded border" @click="resetForm">Cancel</button>
        </div>
        <p v-if="error" class="text-red-600 text-sm">{{ error }}</p>
      </form>
    </div>

    <!-- Expenses -->
<div v-else-if="activeTab === 'expenses'" class="space-y-4">
  <div class="flex items-center justify-between">
    <h2 class="font-semibold">Expenses</h2>
    <button class="px-3 py-2 rounded bg-black text-white" @click="openAddExpense">
      Add Expense
    </button>
  </div>

  <div v-if="exp.loading.expenses">Loading expenses…</div>
  <div v-else>
    <table class="w-full text-sm border rounded overflow-hidden">
      <thead class="bg-gray-50 text-left">
        <tr>
          <th class="px-3 py-2">Date</th>
          <th class="px-3 py-2">Vendor</th>
          <th class="px-3 py-2">Reference</th>
          <th class="px-3 py-2">Note</th>
          <th class="px-3 py-2 text-right">Unit Price</th>
          <th class="px-3 py-2 text-right">Total</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="e in expensesForProject" :key="e.id" class="border-t">
          <td class="px-3 py-2">{{ e.expense_date }}</td>
          <td class="px-3 py-2">{{ e.vendor || '—' }}</td>
          <td class="px-3 py-2">{{ e.reference_no || '—' }}</td>
          <td class="px-3 py-2 text-gray-600">
            {{ truncateNote(e.memo ?? e.note ?? '—') }}
          </td>

          <!-- Show unit price if there's exactly 1 line -->
          <td class="px-3 py-2 text-right">
            <span v-if="(e.lines?.length || 0) === 1">
              {{ formatUsd(e.lines[0].unit_price_usd) }}
            </span>
            <span v-else>—</span>
          </td>

          <!-- Show subtotal = Σ(qty × unit_price) -->
          <td class="px-3 py-2 text-right">
            {{ formatUsd(expenseSubtotal(e)) }}
          </td>
                    <!-- debug -->
          <td colspan="6" class="text-xs text-gray-500">
            {{ e.lines?.map(l => `qty=${l.quantity}, up=${l.unit_price_usd}`) }}
          </td>
        </tr>

        <tr v-if="!expensesForProject.length">
          <td colspan="6" class="px-3 py-4 text-gray-500">No expenses yet.</td>
        </tr>
      </tbody>
    </table>
  </div>



  <!-- Add Expense Modal -->
  <div
    v-if="showAddExpense"
    class="fixed inset-0 bg-black/30 z-50 flex items-center justify-center p-4"
  >
    <div class="bg-white rounded-xl shadow-2xl w-full max-w-3xl p-6">
      <div class="flex items-center justify-between mb-3">
        <h3 class="text-lg font-semibold">Add Expense</h3>
        <button class="text-sm underline" @click="closeAddExpense">Close</button>
      </div>
      <AddExpenseForm
        :project-id="pid"
        @success="onExpenseCreated"
        @cancel="closeAddExpense"
      />
    </div>
  </div>
</div>


    <!-- Tasks -->
    <div v-else-if="activeTab === 'tasks'">
      <ProjectKanban :project-id="pid" @progress="onProgress" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/lib/api'
import { useProjects } from '@/stores/projects'
import { useClients } from '@/stores/clients'
import { useExpensesStore } from '@/stores/expenses'
import AddExpenseForm from '@/components/expenses/AddExpenseForm.vue'
import ProjectKanban from '@/components/tasks/ProjectKanban.vue'

const route = useRoute()
const router = useRouter()
const projects = useProjects()
const clients = useClients()
const exp = useExpensesStore()

const pid = Number(route.params.id)

// --- Tab state (map 'summary' → 'details' for backward compatibility)
const normalizeTab = (t) => (t === 'summary' ? 'details' : (t || 'details'))
const activeTab = ref(normalizeTab(route.query.tab))
watch(() => route.query.tab, (t) => { activeTab.value = normalizeTab(t) })
function goTab(tab) { router.replace({ query: { ...route.query, tab } }) }
function tabBtn(tab) {
  return [
    'px-1 pb-2 border-b-2 -mb-px',
    activeTab.value === tab ? 'border-black text-black' : 'border-transparent text-gray-500 hover:text-black'
  ].join(' ')
}

// --- Project lookup
const project = computed(() => projects.items.find(p => p.id === pid) || null)

// --- Details form
const form = ref({
  name: '',
  code: '',
  client_id: null,
  status: 'planned',
  start_date: '',
  end_date: '',
  budget_amount_usd: '',
  tax_rate: '',
  currency: 'USD',
  description: '',
})
const error = ref(null)
const saving = ref(false)

function hydrateForm() {
  if (!project.value) return
  const p = project.value
  form.value = {
    name: p.name || '',
    code: p.code || '',
    client_id: p.client_id ?? null,
    status: p.status || 'planned',
    start_date: p.start_date || '',
    end_date: p.end_date || '',
    budget_amount_usd: p.budget_amount_usd ?? '',
    tax_rate: p.tax_rate ?? '',
    currency: p.currency || 'USD',
    description: p.description || '',
  }
}
function resetForm() { hydrateForm() }

// Safe numeric parser: handles '', null, '$1,234.50'
function toNumber(v) {
  if (v == null) return 0
  if (typeof v === 'number') return Number.isFinite(v) ? v : 0
  if (typeof v === 'string') {
    const n = Number(v.replace(/[^0-9.-]/g, ''))
    return Number.isFinite(n) ? n : 0
  }
  const n = Number(v)
  return Number.isFinite(n) ? n : 0
}

function formatUsd(v) {
  const n = toNumber(v)
  return Number.isFinite(n) ? `$${n.toFixed(2)}` : '—'
}

function lineQty(ln) {
  return toNumber(ln?.quantity ?? ln?.qty ?? 1)
}

function lineUnit(ln) {
  const up = ln?.unit_price_usd ?? ln?.unit_price ?? ln?.price_usd ?? ln?.price ?? 0
  return toNumber(up)
}

function lineTotal(ln) {
  const pre = toNumber(ln?.line_total_usd ?? ln?.total_usd ?? ln?.total)
  if (pre > 0) return pre
  return lineQty(ln) * lineUnit(ln)
}

function expenseSubtotal(expense) {
  const lines = Array.isArray(expense?.lines) ? expense.lines : []
  return lines.reduce((sum, l) => sum + lineTotal(l), 0)
}

function truncateNote(note) {
  if (!note) return '—'
  const words = String(note).trim().split(/\s+/)
  return words.length > 100 ? words.slice(0, 100).join(' ') + '…' : note
}

async function saveEdits() {
  error.value = null
  saving.value = true
  try {
    const payload = { ...form.value }
    if (payload.budget_amount_usd === '' || payload.budget_amount_usd === null) delete payload.budget_amount_usd
    else payload.budget_amount_usd = Number(payload.budget_amount_usd)
    if (payload.tax_rate === '' || payload.tax_rate === null) delete payload.tax_rate
    else payload.tax_rate = Number(payload.tax_rate)
    const updated = await api.patch(`/projects/${pid}`, payload)
    const idx = projects.items.findIndex(p => p.id === pid)
    if (idx !== -1) projects.items[idx] = { ...projects.items[idx], ...updated }
    hydrateForm()
  } catch (e) {
    error.value = e?.message || 'Failed to update project'
  } finally {
    saving.value = false
  }
}

// --- Expenses
const expensesForProject = computed(() => exp.byProject[pid] || [])
const showAddExpense = ref(false)
function openAddExpense() { showAddExpense.value = true }
function closeAddExpense() {
  showAddExpense.value = false
  if (route.query.open) router.replace({ query: { ...route.query, open: undefined } })
}
async function onExpenseCreated() {
  await exp.fetchExpenses(pid)
  closeAddExpense()
}

// --- Progress sync from Kanban (robust to different shapes)
const localProgress = ref(null)

async function onProgress(progressObj) {
  if (!progressObj || typeof progressObj !== 'object') return

  const percent = Number(progressObj.percent ?? 0)

  // accept either .counts or .totals
  const counts = progressObj.counts || progressObj.totals
  const total = Number(counts?.total ?? counts?.leaves_total ?? 0)
  const done = Number(counts?.done ?? counts?.leaves_done ?? 0)

  // desired status
  let desired = progressObj.suggestion
  if (!desired) {
    // compute a safe fallback
    const anyDoing = Number(progressObj.by_status?.doing ?? 0) > 0
    desired = total === 0 ? 'planned'
            : (done === total ? 'completed' : (anyDoing || done > 0 ? 'active' : 'planned'))
  }

  localProgress.value = percent

  const patch = {}
  if (project.value && project.value.progress_percent !== percent) patch.progress_percent = percent
  if (project.value && desired && project.value.status !== desired) patch.status = desired
  if (Object.keys(patch).length) {
    try {
      const updated = await api.patch(`/projects/${pid}`, patch)
      const idx = projects.items.findIndex(p => p.id === pid)
      if (idx !== -1) projects.items[idx] = { ...projects.items[idx], ...updated }
    } catch { /* non-fatal */ }
  }
  if (desired === 'completed' && project.value?.status !== 'completed' && total > 0 && done === total) {
    if (confirm('All tasks are complete. Mark the project as Completed?')) {
      try {
        const updated = await api.patch(`/projects/${pid}`, { status: 'completed', progress_percent: 100 })
        const idx = projects.items.findIndex(p => p.id === pid)
        if (idx !== -1) projects.items[idx] = { ...projects.items[idx], ...updated }
      } catch {/* non-fatal */ }
    }
  }
}

// --- Boot
onMounted(async () => {
  if (!clients.items.length) { try { await clients.fetchAll() } catch {/* */} }
  if (!project.value) { try { await projects.fetchOne(pid) } catch {/* */} }
  hydrateForm()
  await exp.fetchExpenses(pid)
  // Back-compat: auto-open Add Expense modal if asked
  if (normalizeTab(route.query.tab) === 'expenses' && route.query.open === 'add') {
    showAddExpense.value = true
  }
})
</script>
