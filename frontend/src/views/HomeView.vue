<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { RouterLink } from 'vue-router'
import api from '@/lib/api'
import { useAuth } from '@/stores/auth'

// Auth
const auth = useAuth()

// Loading & data
const loading = ref(true)
const errorMsg = ref('')
const projects = ref([])

// ---- Clients cache (id -> name) ----
const clientsObj = reactive({})
const clientsLoading = ref(false)
const clientsError = ref('')

async function loadClients() {
  clientsLoading.value = true
  clientsError.value = ''
  try {
    const res = await api.get('/clients')
    const list = Array.isArray(res) ? res : (res.clients || [])
    list.forEach(c => { if (c?.id != null) clientsObj[c.id] = c.name || '' })
  } catch (e) {
    clientsError.value = 'Failed to load clients.'
    console.error(e)
  } finally {
    clientsLoading.value = false
  }
}
function clientNameOf(p) {
  return (p?.client_name) || (p?.client_id != null ? clientsObj[p.client_id] : '') || '—'
}

// Filters
const q = ref('')
const status = ref('all')
const client = ref('all')

// Caches
const progressById = reactive(new Map())     // pid -> { percent, counts }
const expensesTotalById = reactive(new Map()) // pid -> number (Σ expense totals)

// Concurrency control
const MAX_CONCURRENT = 4
const queue = []
let active = 0
function run(task){ return new Promise(res => { queue.push({task,res}); pump() }) }
function pump(){ while(active<MAX_CONCURRENT && queue.length){ const {task,res}=queue.shift(); active++; task().finally(()=>{active--;res();pump()}) } }

// ---------- API ----------
async function loadProjects() {
  loading.value = true
  errorMsg.value = ''
  try {
    const res = await api.get('/projects') // api.js prefixes /api
    const list = Array.isArray(res) ? res : (res.projects || [])
    projects.value = list
  } catch (e) {
    errorMsg.value = 'Failed to load projects.'
    console.error(e)
  } finally {
    loading.value = false
  }
}

const progressPromises = new Map()
function fetchProgress(pid) {
  if (progressById.has(pid)) return Promise.resolve(progressById.get(pid))
  if (progressPromises.has(pid)) return progressPromises.get(pid)
  const p = api.get(`/projects/${pid}/tasks/progress`)
    .then((res) => {
      const data = {
        percent: Number(res?.percent || 0),
        counts: res?.counts || { todo: 0, in_progress: 0, done: 0 },
      }
      progressById.set(pid, data)
      return data
    })
    .catch((e) => { console.error('progress error', pid, e); return { percent:0, counts:{ todo:0, in_progress:0, done:0 } } })
    .finally(() => progressPromises.delete(pid))
  progressPromises.set(pid, p)
  return p
}

/** ---------- Expense math (from your reference) ---------- */
// Safe numeric parser
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
function expenseGrandTotal(expense) {
  // Prefer header totals if present; otherwise subtotal (+ tax if available)
  const headerTotal = toNumber(expense?.total_usd ?? expense?.total)
  if (headerTotal > 0) return headerTotal
  const sub = expenseSubtotal(expense)
  const tax = toNumber(expense?.tax_usd ?? expense?.tax)
  return sub + tax
}

/** Fetch Σ totals for a project using the above logic */
const expensesPromises = new Map()
function fetchExpensesTotal(pid) {
  if (expensesTotalById.has(pid)) return Promise.resolve(expensesTotalById.get(pid))
  if (expensesPromises.has(pid)) return expensesPromises.get(pid)
  const p = api.get(`/projects/${pid}/expenses`)
    .then((res) => {
      const list = Array.isArray(res) ? res : (res.expenses || res.items || [])
      const sum = list.reduce((acc, e) => acc + expenseGrandTotal(e), 0)
      expensesTotalById.set(pid, sum)
      return sum
    })
    .catch((e) => { console.error('expenses error', pid, e); expensesTotalById.set(pid, 0); return 0 })
    .finally(() => expensesPromises.delete(pid))
  expensesPromises.set(pid, p)
  return p
}

// ---------- Derived ----------
const statuses = computed(() => ['all', ...new Set(projects.value.map(p => p.status).filter(Boolean)) ])
const clientsList  = computed(() => ['all', ...new Set(projects.value.map(p => clientNameOf(p)).filter(Boolean)) ])

const PAGE_SIZE = 5
const filtered = computed(() => {
  const k = q.value.trim().toLowerCase()
  return projects.value.filter(p => {
    const nameClient = clientNameOf(p)
    const matchesQ =
      !k ||
      (p.code || '').toLowerCase().includes(k) ||
      (p.name || '').toLowerCase().includes(k) ||
      (nameClient || '').toLowerCase().includes(k)

    const matchesStatus = status.value === 'all' || p.status === status.value
    const matchesClient = client.value === 'all' || nameClient === client.value
    return matchesQ && matchesStatus && matchesClient
  })
})
const visible = computed(() => filtered.value.slice(0, PAGE_SIZE))

watch(visible, (rows) => {
  rows.forEach(p => {
    run(() => fetchProgress(p.id))
    run(() => fetchExpensesTotal(p.id)) // use reference math
  })
}, { immediate: true })

// KPIs
const kpiActiveCount = computed(() =>
  projects.value.filter(p => (p.status || '').toLowerCase() === 'active').length
)
const kpiAvgProgress = computed(() => {
  const vals = projects.value.map(p => progressById.get(p.id)?.percent).filter(v => typeof v === 'number')
  return vals.length ? vals.reduce((a,b)=>a+b,0) / vals.length : 0
})
const kpiTotalExpenses = computed(() => {
  let t = 0; projects.value.forEach(p => { t += Number(expensesTotalById.get(p.id) || 0) }); return t
})

// Formatters
const fmtCurrency = (n) => new Intl.NumberFormat('en-US', { style:'currency', currency:'USD' }).format(Number(n||0))
const fmtPercent  = (n) => `${Math.round(Number(n||0))}%`

// Status → badge
function statusClass(status) {
  const s = String(status || '').toLowerCase()
  if (s === 'active') return 'badge-success'
  if (s === 'planned') return 'badge-warn'
  if (s === 'completed' || s === 'done' || s === 'finished') return 'badge-neutral'
  return 'badge-neutral'
}

// Progress color
function progressClass(pct) {
  const n = Number(pct || 0)
  if (n >= 67) return 'progress-green'
  if (n >= 34) return 'progress-navy'
  return 'progress-amber'
}

onMounted(async () => {
  await Promise.all([loadProjects(), loadClients()])
})
</script>

<template>
  <div class="page !px-0 md:!px-0">
    <!-- Page header -->
    <header class="page-header">
      <h1 class="page-title">Dashboard</h1>
      <p class="page-meta">Welcome back, <strong>{{ auth.user?.name || auth.user?.email }}</strong></p>
    </header>

    <!-- Error -->
    <div v-if="errorMsg || clientsError" class="section bg-[--color-error]/5 border-[--color-error]">
      <div class="text-[--color-error] text-sm">
        {{ errorMsg || clientsError }}
      </div>
    </div>

    <!-- KPIs -->
    <div class="grid gap-4 md:grid-cols-3">
      <div class="section">
        <div class="muted mb-1">Active Projects</div>
        <div class="text-3xl font-semibold">{{ loading ? '—' : kpiActiveCount }}</div>
      </div>
      <div class="section">
        <div class="muted mb-1">Avg Task Progress</div>
        <div class="text-3xl font-semibold">
          <span v-if="loading">—</span>
          <span v-else>{{ fmtPercent(kpiAvgProgress) }}</span>
        </div>
        <div class="help">Updates as project progress is fetched</div>
      </div>
      <div class="section">
        <div class="muted mb-1">Total Expenses</div>
        <div class="text-3xl font-semibold">
          <span v-if="loading">—</span>
          <span v-else>{{ fmtCurrency(kpiTotalExpenses) }}</span>
        </div>
        <div class="help">Σ of all project expenses</div>
      </div>
    </div>

    <!-- Content grid -->
    <div class="grid gap-4 mt-5 md:grid-cols-3">
      <!-- Projects table -->
      <section class="section md:col-span-2">
        <!-- Filters -->
        <div class="flex flex-col sm:flex-row sm:items-end gap-3 mb-3">
          <div class="flex-1">
            <label class="label">Search</label>
            <input class="field" placeholder="Search by code, name, or client…" v-model="q" />
          </div>
          <div>
            <label class="label">Status</label>
            <select class="field" v-model="status">
              <option v-for="s in statuses" :key="s" :value="s">{{ s }}</option>
            </select>
          </div>
          <div>
            <label class="label">Client</label>
            <select class="field" v-model="client">
              <option v-for="c in clientsList" :key="c" :value="c">{{ c }}</option>
            </select>
          </div>
        </div>

        <div class="card p-0 overflow-hidden">
          <div class="overflow-x-auto">
            <table class="table-base w-full">
              <thead class="table-head">
                <tr class="text-xs uppercase tracking-wide text-[--color-text-3] border-b border-[--color-border-warm]">
                  <th class="text-left font-medium px-4 py-2">Code</th>
                  <th class="text-left font-medium px-4 py-2">Project</th>
                  <th class="text-left font-medium px-4 py-2">Client</th>
                  <th class="text-right font-medium px-4 py-2">Total</th>
                  <th class="text-right font-medium px-4 py-2 w-44">Progress</th>
                </tr>
              </thead>

              <!-- Loading skeleton rows -->
              <tbody v-if="loading">
                <tr v-for="i in 5" :key="i" class="border-b border-[--color-border-warm]">
                  <td class="px-4 py-3"><span class="skeleton h-4 w-24 block"></span></td>
                  <td class="px-4 py-3"><span class="skeleton h-4 w-56 block"></span></td>
                  <td class="px-4 py-3"><span class="skeleton h-4 w-28 block"></span></td>
                  <td class="px-4 py-3 text-right"><span class="skeleton h-4 w-20 inline-block"></span></td>
                  <td class="px-4 py-3 text-right"><span class="skeleton h-4 w-24 inline-block"></span></td>
                </tr>
              </tbody>

              <!-- Data rows -->
              <tbody v-else>
                <tr
                  v-for="p in visible"
                  :key="p.id"
                  class="table-row border-b border-[--color-border-warm] text-sm"
                >
                  <td class="px-4 py-2 font-medium whitespace-nowrap">
                    {{ p.code }}
                  </td>

                  <td class="px-4 py-2">
                    <div class="truncate">{{ p.name }}</div>
                    <div v-if="p.status" class="mt-0.5">
                      <span :class="['badge', statusClass(p.status)]">{{ p.status }}</span>
                    </div>
                  </td>

                  <td class="px-4 py-2 whitespace-nowrap truncate">
                    {{ clientNameOf(p) }}
                  </td>

                  <td class="px-4 py-2 text-right whitespace-nowrap">
                    <template v-if="expensesTotalById.get(p.id) != null">
                      {{ fmtCurrency(expensesTotalById.get(p.id)) }}
                    </template>
                    <template v-else>
                      <span class="skeleton h-4 w-20 inline-block"></span>
                    </template>
                  </td>

                  <td class="px-4 py-2">
                    <div class="flex items-center justify-end gap-2">
                      <div class="w-28 h-1.5 bg-black/10 rounded-full overflow-hidden">
                        <div
                          class="h-full rounded-full transition-[width,background] duration-300"
                          :class="progressClass(progressById.get(p.id)?.percent)"
                          :style="{ width: (progressById.get(p.id)?.percent || 0) + '%' }"
                        />
                      </div>
                      <div class="text-xs text-[--color-text-3] w-8 text-right">
                        <template v-if="progressById.get(p.id)">
                          {{ Math.round(progressById.get(p.id).percent) }}%
                        </template>
                        <template v-else>—</template>
                      </div>
                    </div>
                  </td>
                </tr>

                <tr v-if="!visible.length">
                  <td colspan="5" class="px-4 py-6 text-center muted">
                    No projects match your filters.
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Footer action -->
          <div class="px-4 py-3 text-right">
            <RouterLink to="/projects" class="btn btn-primary btn-primary-hover">
              View all projects
            </RouterLink>
          </div>
        </div>
      </section>

      <!-- Finance Tracker -->
      <section class="section">
        <div class="mb-3">
          <div class="heading">Finance Tracker</div>
          <p class="muted mt-1">Sum of all expense totals per project.</p>
        </div>

        <div class="grid gap-2">
          <div class="flex items-center justify-between">
            <span class="subtext">Total (loaded)</span>
            <span class="font-semibold">{{ fmtCurrency(kpiTotalExpenses) }}</span>
          </div>

          <div class="divider my-2"></div>

          <div class="subtext mb-1">Visible Projects</div>
          <div v-for="p in visible" :key="p.id" class="flex items-center justify-between py-1">
            <span class="truncate">{{ p.code }} · {{ p.name }}</span>
            <span v-if="expensesTotalById.get(p.id) != null">{{ fmtCurrency(expensesTotalById.get(p.id)) }}</span>
            <span v-else class="skeleton h-4 w-16"></span>
          </div>
        </div>

        <div class="divider my-3"></div>

        <div>
          <div class="heading text-base">Recent Activity</div>
          <p class="muted mt-1">Coming soon — latest expenses & completed tasks.</p>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
/* Progress colors */
.progress-green { background: linear-gradient(90deg, rgba(16,185,129,0.85), rgba(16,185,129,1)); }
.progress-navy  { background: linear-gradient(90deg, rgba(30,58,138,0.85), rgba(30,58,138,1)); }
.progress-amber { background: linear-gradient(90deg, rgba(245,158,11,0.85), rgba(245,158,11,1)); }
</style>
