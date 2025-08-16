<script setup>
import { ref, onMounted, computed } from 'vue'
import { useProjects } from '@/stores/projects'
import { useClients } from '@/stores/clients'
import { useCatalog } from '@/stores/catalog'

const projects = useProjects()
const clients = useClients()
const catalog = useCatalog()

/* ---------------- state ---------------- */
const q = ref('')
const newProject = ref({
  client_id: null,
  name: '',
  description: '',
  project_type: '',
  start_date: '',
  end_date: '',
  budget_amount_usd: '',
  tax_rate: '',
})
const createErr = ref(null)

// side panel
const selected = ref(null) // currently managed project object
const pc = ref({ category_id: null, base_cost_usd: '' })
const bom = ref({ category_id: null, component_id: null, quantity: 1, unit_price_usd: '', note: '' })
const pcErr = ref(null)
const bomErr = ref(null)

/* ---------------- perf helpers ---------------- */
// O(1) client name lookup instead of find() per row
const clientMap = computed(() => {
  const m = Object.create(null)
  for (const c of clients.items) m[c.id] = c.name
  return m
})
const clientName = (id) => clientMap.value[id] ?? '—'

// Debounced search
let t
const search = () => {
  clearTimeout(t)
  t = setTimeout(() => projects.fetchAll({ q: q.value }), 250)
}

// Filtered components for selected category (BOM)
const filteredComponents = computed(() =>
  bom.value.category_id
    ? catalog.components.filter(x => x.category_id === bom.value.category_id)
    : []
)

const loadCompsForCat = async (catId) => {
  if (catId) await catalog.fetchComponents({ category_id: catId })
}

/* ---------------- actions ---------------- */
const submit = async () => {
  createErr.value = null
  try {
    if (!newProject.value.client_id || !newProject.value.name.trim()) return
    const payload = {
      ...newProject.value,
      budget_amount_usd: newProject.value.budget_amount_usd === '' ? undefined : Number(newProject.value.budget_amount_usd),
      tax_rate: newProject.value.tax_rate === '' ? undefined : Number(newProject.value.tax_rate),
    }
    const created = await projects.create(payload)
    // optimistic insert if store returns the created project
    if (created && created.id) {
      projects.items.unshift(created)
    } else {
      // fallback if your store doesn't return it
      await projects.fetchAll()
    }
    // reset
    newProject.value = { client_id: null, name: '', description: '', project_type: '', start_date: '', end_date: '', budget_amount_usd: '', tax_rate: '' }
  } catch (e) {
    createErr.value = e?.message || 'Failed to create project'
  }
}

const openManage = async (p) => {
  selected.value = p
  // fetch categories & project detail in parallel
  await Promise.all([
    catalog.fetchCategories(),
    projects.openDetail(p.id) // should populate projects.detail.{cats,bom,summary}
  ])
}

const addCategory = async () => {
  pcErr.value = null
  try {
    if (!pc.value.category_id) return
    await projects.addProjectCat(selected.value.id, {
      category_id: pc.value.category_id,
      base_cost_usd: pc.value.base_cost_usd === '' ? 0 : Number(pc.value.base_cost_usd),
    })
    pc.value = { category_id: null, base_cost_usd: '' }
    await projects.fetchProjectSummary(selected.value.id)
  } catch (e) {
    pcErr.value = e?.message || 'Failed to add category'
  }
}

const addBom = async () => {
  bomErr.value = null
  try {
    const payload = {
      category_id: bom.value.category_id,
      component_id: bom.value.component_id,
      quantity: Number(bom.value.quantity || 1),
      unit_price_usd: bom.value.unit_price_usd === '' ? undefined : Number(bom.value.unit_price_usd),
      note: bom.value.note || undefined,
    }
    if (!payload.category_id || !payload.component_id) return
    await projects.addProjectBom(selected.value.id, payload)
    bom.value = { category_id: null, component_id: null, quantity: 1, unit_price_usd: '', note: '' }
    await projects.fetchProjectSummary(selected.value.id)
  } catch (e) {
    bomErr.value = e?.message || 'Failed to add component'
  }
}

const removePc = async (row) => {
  await projects.deleteProjectCat(selected.value.id, row.id)
  await projects.fetchProjectSummary(selected.value.id)
}
const removeBom = async (row) => {
  await projects.deleteProjectBom(selected.value.id, row.id)
  await projects.fetchProjectSummary(selected.value.id)
}

/* ---------------- mount ---------------- */
onMounted(async () => {
  // parallel initial fetches
  await Promise.all([
    clients.items.length ? Promise.resolve() : clients.fetchAll(),
    projects.fetchAll(),
  ])
})
</script>

<template>
  <div class="p-6 space-y-6 max-w-7xl mx-auto">
    <!-- Top bar -->
    <div class="flex flex-wrap items-center gap-3">
      <h1 class="text-2xl font-semibold">Projects</h1>
      <div class="flex items-center gap-2">
        <input
          v-model="q"
          @input="search"
          placeholder="Search…"
          class="border rounded px-3 py-1 min-w-[220px]"
          aria-label="Search projects"
        />
        <button
          class="rounded bg-black text-white px-3 py-1 cursor-pointer focus:outline-none focus:ring-2 focus:ring-black/40"
          @click="search"
          type="button"
        >
          Search
        </button>
      </div>
    </div>

    <div class="grid md:grid-cols-2 gap-6">
      <!-- Create form -->
      <form @submit.prevent="submit" class="space-y-2 border rounded p-4" aria-busy="false">
        <h2 class="font-semibold">Create project</h2>

        <select v-model.number="newProject.client_id" class="w-full border rounded p-2" required>
          <option :value="null" disabled>Select client…</option>
          <option v-for="c in clients.items" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>

        <input v-model="newProject.name" placeholder="Project name *" class="w-full border rounded p-2" required />
        <input v-model="newProject.project_type" placeholder="Project type (optional)" class="w-full border rounded p-2" />
        <textarea v-model="newProject.description" placeholder="Description" class="w-full border rounded p-2"></textarea>

        <div class="grid grid-cols-2 gap-3">
          <label class="block">
            <span class="text-sm text-gray-600">Start date</span>
            <input v-model="newProject.start_date" type="date" class="w-full border rounded p-2" />
          </label>
          <label class="block">
            <span class="text-sm text-gray-600">End date</span>
            <input v-model="newProject.end_date" type="date" class="w-full border rounded p-2" />
          </label>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <label class="block">
            <span class="text-sm text-gray-600">Budget (USD)</span>
            <input v-model="newProject.budget_amount_usd" type="number" step="0.01" class="w-full border rounded p-2" />
          </label>
          <label class="block">
            <span class="text-sm text-gray-600">Tax rate (e.g. 0.05)</span>
            <input v-model="newProject.tax_rate" type="number" step="0.0001" class="w-full border rounded p-2" />
          </label>
        </div>

        <button
          class="rounded bg-black text-white px-3 py-2 cursor-pointer focus:outline-none focus:ring-2 focus:ring-black/40"
          type="submit"
        >
          Add project
        </button>
        <p v-if="createErr" class="text-red-600 text-sm mt-1">{{ createErr }}</p>
      </form>

      <!-- List -->
      <div>
        <div class="flex items-center justify-between">
          <h2 class="font-semibold">All projects</h2>
          <span class="text-sm text-gray-500">{{ projects.items.length }} total</span>
        </div>
        <div v-if="projects.loading">Loading…</div>
        <ul class="divide-y border rounded" v-memo="[projects.items.length]">
          <li
            v-for="p in projects.items"
            :key="p.id"
            class="p-3 flex items-start justify-between gap-3"
          >
            <div class="min-w-0">
              <div class="font-medium truncate">{{ p.code }} — {{ p.name }}</div>
              <div class="text-sm text-gray-600 truncate">Client: {{ clientName(p.client_id) }}</div>
              <div class="text-xs text-gray-500 whitespace-nowrap overflow-hidden text-ellipsis">
                <span v-if="p.start_date">Start: {{ p.start_date }}</span>
                <span v-if="p.end_date"> · End: {{ p.end_date }}</span>
                <span v-if="p.budget_amount_usd"> · Budget: ${{ p.budget_amount_usd }}</span>
              </div>
            </div>
            <div class="flex-shrink-0 flex gap-3">
              <RouterLink
                class="text-sm underline cursor-pointer focus:outline-none focus:ring-2 focus:ring-black/30 rounded"
                :to="{ name: 'project-detail', params: { id: p.id } }"
                title="Open details"
              >
                View
              </RouterLink>
              <button
                class="text-sm underline cursor-pointer focus:outline-none focus:ring-2 focus:ring-black/30 rounded"
                @click="openManage(p)"
                type="button"
                title="Manage project"
              >
                Manage
              </button>
              <button
                class="text-red-600 text-sm cursor-pointer focus:outline-none focus:ring-2 focus:ring-red-400/40 rounded"
                @click="projects.remove(p.id)"
                type="button"
                title="Delete project"
              >
                Delete
              </button>
            </div>
          </li>
          <li v-if="!projects.items.length" class="p-3 text-sm text-gray-500">No projects yet.</li>
        </ul>
      </div>
    </div>

    <p v-if="projects.error" class="text-red-600 text-sm">{{ projects.error }}</p>

    <!-- Side panel -->
    <div
      v-if="selected"
      class="fixed inset-y-0 right-0 w-full md:w-[560px] bg-white shadow-2xl p-6 overflow-y-auto"
    >
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-xl font-semibold truncate">Manage: {{ selected.code }} — {{ selected.name }}</h2>
        <button
          class="text-sm underline cursor-pointer focus:outline-none focus:ring-2 focus:ring-black/30 rounded"
          @click="selected = null"
          type="button"
          title="Close"
        >
          Close
        </button>
      </div>

      <!-- Categories with base cost -->
      <section class="space-y-3 mb-8">
        <h3 class="font-semibold">Categories (base cost)</h3>
        <form @submit.prevent="addCategory" class="flex flex-wrap gap-2 items-center">
          <select
            v-model.number="pc.category_id"
            @change="loadCompsForCat(pc.category_id)"
            class="border rounded p-2"
          >
            <option :value="null" disabled>Select category…</option>
            <option v-for="c in catalog.categories" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>
          <input v-model="pc.base_cost_usd" type="number" step="0.01" placeholder="Base cost (USD)" class="border rounded p-2 w-40" />
          <button class="rounded bg-black text-white px-3 py-2 cursor-pointer">Add</button>
        </form>
        <p v-if="pcErr" class="text-red-600 text-sm">{{ pcErr }}</p>

        <ul class="divide-y border rounded">
          <li v-for="row in projects.detail.cats" :key="row.id" class="p-3 flex items-center justify-between">
            <div>
              <div class="font-medium">
                {{ catalog.categories.find(c => c.id === row.category_id)?.name || ('#'+row.category_id) }}
              </div>
              <div class="text-sm text-gray-600">Base cost: ${{ row.base_cost_usd }}</div>
            </div>
            <button class="text-red-600 text-sm cursor-pointer" @click="removePc(row)" type="button">Remove</button>
          </li>
          <li v-if="!projects.detail.cats.length" class="p-3 text-sm text-gray-500">No categories yet.</li>
        </ul>
      </section>

      <!-- BOM -->
      <section class="space-y-3 mb-8">
        <h3 class="font-semibold">Components (BOM)</h3>
        <form @submit.prevent="addBom" class="grid grid-cols-1 md:grid-cols-5 gap-2 items-center">
          <select v-model.number="bom.category_id" @change="loadCompsForCat(bom.category_id)" class="border rounded p-2 md:col-span-2">
            <option :value="null" disabled>Select category…</option>
            <option v-for="c in catalog.categories" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>
          <select v-model.number="bom.component_id" class="border rounded p-2 md:col-span-2" :disabled="!bom.category_id">
            <option :value="null" disabled>Select component…</option>
            <option v-for="x in filteredComponents" :key="x.id" :value="x.id">{{ x.name }}</option>
          </select>
          <input v-model.number="bom.quantity" type="number" min="0" step="0.0001" placeholder="Qty" class="border rounded p-2" />
          <input v-model="bom.unit_price_usd" type="number" step="0.0001" placeholder="Unit $" class="border rounded p-2 md:col-span-2" />
          <input v-model="bom.note" placeholder="Note" class="border rounded p-2 md:col-span-2" />
          <button class="rounded bg-black text-white px-3 py-2 md:col-span-1 cursor-pointer">Add</button>
        </form>
        <p v-if="bomErr" class="text-red-600 text-sm">{{ bomErr }}</p>

        <ul class="divide-y border rounded">
          <li v-for="row in projects.detail.bom" :key="row.id" class="p-3 flex items-center justify-between">
            <div class="min-w-0">
              <div class="font-medium truncate">
                {{ (catalog.components.find(c => c.id === row.component_id)?.name) || ('Component #'+row.component_id) }}
              </div>
              <div class="text-sm text-gray-600">
                Qty: {{ row.quantity }} · Unit: {{ row.unit_price_usd ?? 'default' }}
              </div>
            </div>
            <button class="text-red-600 text-sm cursor-pointer" @click="removeBom(row)" type="button">Remove</button>
          </li>
          <li v-if="!projects.detail.bom.length" class="p-3 text-sm text-gray-500">No components yet.</li>
        </ul>
      </section>

      <!-- Summary -->
      <section class="space-y-3">
        <div class="flex items-center justify-between">
          <h3 class="font-semibold">Summary (planned vs actual)</h3>
          <button
            class="text-sm underline cursor-pointer focus:outline-none focus:ring-2 focus:ring-black/30 rounded"
            @click="projects.fetchProjectSummary(selected.id)"
            type="button"
          >
            Refresh
          </button>
        </div>
        <div v-if="projects.detail.summary">
          <ul class="divide-y border rounded">
            <li v-for="r in projects.detail.summary.per_category" :key="r.category_id" class="p-3 flex items-center justify-between">
              <div class="font-medium">{{ r.category_name || ('#'+r.category_id) }}</div>
              <div class="text-sm">
                Planned ${{ r.planned_usd.toFixed(2) }}
                · Actual ${{ r.actual_usd.toFixed(2) }}
                · Var ${{ r.variance_usd.toFixed(2) }}
              </div>
            </li>
          </ul>
          <div class="mt-3 p-3 border rounded bg-gray-50 text-sm">
            <div>Planned total: ${{ projects.detail.summary.totals.planned_total_usd.toFixed(2) }}</div>
            <div>Actual total: ${{ projects.detail.summary.totals.actual_total_usd.toFixed(2) }}</div>
            <div class="font-medium">Variance: ${{ projects.detail.summary.totals.variance_total_usd.toFixed(2) }}</div>
          </div>
        </div>
        <div v-else class="text-sm text-gray-500">No summary yet.</div>
      </section>
    </div>
  </div>
</template>
