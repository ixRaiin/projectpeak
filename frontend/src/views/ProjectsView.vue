<template>
  <div class="p-6 space-y-6 max-w-7xl mx-auto">
    <ProjectActionBar
      :initial-view="initialView"
      :q-prop="q"
      :status-prop="status"
      :sort-prop="sort"
      @create="goCreate"
      @search="onSearch"
      @filter="onFilter"
      @sort="onSort"
      @toggle="onToggle"
    />

    <div v-if="projects.loading" class="space-y-3">
      <div class="h-10 bg-gray-100 rounded animate-pulse"></div>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div v-for="i in 6" :key="i" class="h-32 bg-gray-100 rounded animate-pulse"></div>
      </div>
    </div>

    <div v-else>
      <ProjectTable
        v-if="view === 'table'"
        :items="projects.items"
        :client-name="clientName"
        @view="openDetail"
        @delete="confirmDelete"
        @add-expense="openAddExpense"
        @open-board="openBoard"
      />

      <ProjectGrid
        v-else
        :items="projects.items"
        :client-name="clientName"
        @view="openDetail"
        @delete="confirmDelete"
        @add-expense="openAddExpense"
        @open-board="openBoard"
      />

      <p v-if="!projects.items.length" class="text-sm text-gray-500 mt-4">No projects found.</p>
      <p v-if="projects.error" class="text-sm text-red-600 mt-2">{{ projects.error }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProjects } from '@/stores/projects'
import { useClients } from '@/stores/clients'
import ProjectActionBar from '@/components/projects/ProjectActionBar.vue'
import ProjectTable from '@/components/projects/ProjectTable.vue'
import ProjectGrid from '@/components/projects/ProjectGrid.vue'

const projects = useProjects()
const clients = useClients()
const route = useRoute()
const router = useRouter()

// ----- local query/sort state (NOT in store) -----
const q = ref('')
const status = ref('all')            // all | planned | active | completed
const sort = ref('updated_desc')     // updated_desc | updated_asc | name_asc | name_desc

// ----- view state (persist in query + localStorage) -----
const initialView = (route.query.view === 'grid' || route.query.view === 'table')
  ? route.query.view
  : (localStorage.getItem('projects:view') || 'table')

const view = ref(initialView)

watch(view, (v) => {
  localStorage.setItem('projects:view', v)
  router.replace({ query: { ...route.query, view: v } })
})

// ----- client lookup helper -----
const clientMap = computed(() => {
  const m = Object.create(null)
  for (const c of clients.items) m[c.id] = c.name
  return m
})
const clientName = (id) => clientMap.value[id] ?? '—'

// ----- action bar handlers -----
const onSearch = (val) => {
  q.value = val
  projects.fetchAll({ q: q.value, status: status.value, sort: sort.value })
}
const onFilter = (val) => {
  status.value = val
  projects.fetchAll({ q: q.value, status: status.value, sort: sort.value })
}
const onSort = (val) => {
  sort.value = val
  projects.fetchAll({ q: q.value, status: status.value, sort: sort.value })
}
const onToggle = (v) => { view.value = v }
const goCreate = () => router.push({ name: 'project-new' })

// ----- row/card actions -----
const openDetail = (p) => router.push({ name: 'project-detail', params: { id: p.id } })
const openAddExpense = (p) =>
  router.push({ name: 'project-detail', params: { id: p.id }, query: { open: 'add-expense' } })
const openBoard = (p) =>
  router.push({ name: 'project-detail', params: { id: p.id }, query: { tab: 'tasks' } })

const confirmDelete = async (p) => {
  if (confirm(`Delete project “${p.name}”?`)) {
    await projects.remove(p.id)
  }
}

// ----- mount -----
onMounted(async () => {
  await Promise.all([
    clients.items.length ? Promise.resolve() : clients.fetchAll(),
    projects.fetchAll({ q: q.value, status: status.value, sort: sort.value })
  ])
})
</script>
