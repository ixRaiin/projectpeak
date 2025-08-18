<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { RouterLink } from 'vue-router'
import api from '@/lib/api'
import { useAuth } from '@/stores/auth'

const auth = useAuth()

const loading = ref(true)
const errorMsg = ref('')
const projects = ref([])

const q = ref('')
const status = ref('all')
const client = ref('all')

const summaryById = reactive(new Map())
const progressById = reactive(new Map())

const MAX_CONCURRENT = 4
const queue = []
let active = 0
function run(task){ return new Promise(res => { queue.push({task,res}); pump() }) }
function pump(){ while(active<MAX_CONCURRENT && queue.length){ const {task,res}=queue.shift(); active++; task().finally(()=>{active--;res();pump()}) } }

async function loadProjects() {
  loading.value = true
  errorMsg.value = ''
  try {
    const res = await api.get('/projects')
    const list = Array.isArray(res) ? res : (res.projects || [])
    projects.value = list
  } catch (e) {
    errorMsg.value = 'Failed to load projects.'
    console.error(e)
  } finally {
    loading.value = false
  }
}

const summaryPromises = new Map()
function fetchSummary(pid) {
  if (summaryById.has(pid)) return Promise.resolve(summaryById.get(pid))
  if (summaryPromises.has(pid)) return summaryPromises.get(pid)
  const p = api.get(`/projects/${pid}/summary`)
    .then((res) => {
      const data = {
        planned: Number(res?.totals?.planned || 0),
        actual: Number(res?.totals?.actual || 0),
        variance: Number(res?.totals?.variance || 0),
      }
      summaryById.set(pid, data)
      return data
    })
    .catch((e) => { console.error('summary error', pid, e); return { planned:0, actual:0, variance:0 } })
    .finally(() => summaryPromises.delete(pid))
  summaryPromises.set(pid, p)
  return p
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

const statuses = computed(() => ['all', ...new Set(projects.value.map(p => p.status).filter(Boolean)) ])
const clients  = computed(() => ['all', ...new Set(projects.value.map(p => p.client_name).filter(Boolean)) ])

const filtered = computed(() => {
  const k = q.value.trim().toLowerCase()
  return projects.value.filter(p => {
    const matchesQ = !k || (p.code||'').toLowerCase().includes(k) || (p.name||'').toLowerCase().includes(k) || (p.client_name||'').toLowerCase().includes(k)
    const matchesStatus = status.value === 'all' || p.status === status.value
    const matchesClient = client.value === 'all' || p.client_name === client.value
    return matchesQ && matchesStatus && matchesClient
  })
})

const PAGE_SIZE = 8
const visible = computed(() => filtered.value.slice(0, PAGE_SIZE))

watch(visible, (rows) => {
  rows.forEach(p => {
    run(() => fetchSummary(p.id))
    run(() => fetchProgress(p.id))
  })
}, { immediate: true })

const kpiActiveCount = computed(() =>
  projects.value.filter(p => (p.status || '').toLowerCase() === 'active').length
)
const kpiAvgProgress = computed(() => {
  const vals = projects.value.map(p => progressById.get(p.id)?.percent).filter(v => typeof v === 'number')
  return vals.length ? vals.reduce((a,b)=>a+b,0) / vals.length : 0
})
const kpiTotalActual = computed(() => {
  let t = 0; projects.value.forEach(p => { t += Number(summaryById.get(p.id)?.actual || 0) }); return t
})

const fmtCurrency = (n) => new Intl.NumberFormat('en-US', { style:'currency', currency:'USD' }).format(Number(n||0))
const fmtPercent  = (n) => `${Math.round(Number(n||0))}%`

onMounted(loadProjects)
</script>

<template>
  <div class="page !px-0 md:!px-0">
    <!-- Page header -->
    <header class="page-header">
      <h1 class="page-title">Dashboard</h1>
      <p class="page-meta">Welcome back, <strong>{{ auth.user?.name || auth.user?.email }}</strong></p>
    </header>

    <!-- Error -->
    <div v-if="errorMsg" class="section bg-[--color-error]/5 border-[--color-error]">
      <div class="text-[--color-error] text-sm">{{ errorMsg }}</div>
    </div>

    <!-- KPIs (tighter gap) -->
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
        <div class="muted mb-1">Total Actual Spend</div>
        <div class="text-3xl font-semibold">
          <span v-if="loading">—</span>
          <span v-else>{{ fmtCurrency(kpiTotalActual) }}</span>
        </div>
        <div class="help">Aggregated from project summaries</div>
      </div>
    </div>

    <!-- Content grid (slightly reduced spacing) -->
    <div class="grid gap-4 mt-5 md:grid-cols-3">
      <!-- Projects mini-table -->
      <section class="section md:col-span-2">
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
              <option v-for="c in clients" :key="c" :value="c">{{ c }}</option>
            </select>
          </div>
        </div>

        <div class="card p-0 overflow-hidden">
          <div class="grid grid-cols-6 px-4 py-2 border-b border-[--color-border-warm] text-sm font-medium">
            <div class="col-span-1">Code</div>
            <div class="col-span-2">Project</div>
            <div class="col-span-1">Client</div>
            <div class="col-span-1 text-right">Actual</div>
            <div class="col-span-1 text-right">Progress</div>
          </div>

          <template v-if="loading">
            <div v-for="i in 8" :key="i" class="px-4 py-3 border-b border-[--color-border-warm]">
              <div class="skeleton h-5 w-full"></div>
            </div>
          </template>

          <template v-else>
            <div
              v-for="p in visible"
              :key="p.id"
              class="grid grid-cols-6 px-4 py-3 border-b border-[--color-border-warm] table-row"
            >
              <div class="col-span-1 font-medium">{{ p.code }}</div>
              <div class="col-span-2">
                <div class="truncate">{{ p.name }}</div>
                <div class="muted">Status: {{ p.status || '—' }}</div>
              </div>
              <div class="col-span-1 truncate">{{ p.client_name || '—' }}</div>
              <div class="col-span-1 text-right">
                <span v-if="!summaryById.get(p.id)"><span class="skeleton h-4 w-20 inline-block"></span></span>
                <span v-else>{{ fmtCurrency(summaryById.get(p.id).actual) }}</span>
              </div>
              <div class="col-span-1 text-right">
                <span v-if="!progressById.get(p.id)"><span class="skeleton h-4 w-12 inline-block"></span></span>
                <span v-else>{{ fmtPercent(progressById.get(p.id).percent) }}</span>
              </div>
            </div>

            <div v-if="!visible.length" class="px-4 py-6 text-center muted">No projects match your filters.</div>

            <div class="px-4 py-3 text-right">
              <RouterLink to="/projects" class="btn btn-primary btn-primary-hover">View all projects</RouterLink>
            </div>
          </template>
        </div>
      </section>

      <!-- Finance Tracker -->
      <section class="section">
        <div class="mb-3">
          <div class="heading">Finance Tracker</div>
          <p class="muted mt-1">Rolling total of Actual across projects.</p>
        </div>

        <div class="grid gap-2">
          <div class="flex items-center justify-between">
            <span class="subtext">Total Actual (loaded)</span>
            <span class="font-semibold">{{ fmtCurrency(kpiTotalActual) }}</span>
          </div>

          <div class="divider my-2"></div>

          <div class="subtext mb-1">Visible Projects</div>
          <div v-for="p in visible" :key="p.id" class="flex items-center justify-between py-1">
            <span class="truncate">{{ p.code }} · {{ p.name }}</span>
            <span v-if="summaryById.get(p.id)">{{ fmtCurrency(summaryById.get(p.id).actual) }}</span>
            <span v-else class="skeleton h-4 w-16"></span>
          </div>
        </div>

        <div class="divider my-3"></div>

        <div>
          <div class="heading text-base">Recent Activity</div>
          <p class="muted mt-1">Coming soon — we’ll surface latest expenses & completed tasks.</p>
        </div>
      </section>
    </div>
  </div>
</template>
