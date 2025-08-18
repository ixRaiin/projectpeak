<script setup>
import { computed, onMounted, watch, ref, reactive } from 'vue'
import { useRoute, RouterLink } from 'vue-router'

import { useProjects } from '@/stores/projects'
import { useTasksStore } from '@/stores/tasks'
import { useExpensesStore } from '@/stores/expenses'
import { useCatalog } from '@/stores/catalog'

// ---------- Route / IDs ----------
const route = useRoute()
const pid = computed(() => Number(route.params.id))

// ---------- Stores ----------
const projects = useProjects()
const tasks = useTasksStore()
const expenses = useExpensesStore()
const catalog = useCatalog()

// ---------- Header / Project ----------
const project = computed(() =>
  (projects.items || []).find(p => p.id === pid.value) || null
)

// ---------- Tasks / Progress ----------
const taskList = computed(() => tasks.byProject[pid.value] || [])
const progress = computed(() => tasks.progressByProject[pid.value] || null)
const progressPercent = computed(() => Math.max(0, Math.min(100, Number(progress.value?.percent ?? 0))))

// ---------- Expenses ----------
const expenseList = computed(() => expenses.byProject[pid.value] || [])

// ---------- Global UX ----------
const toast = ref(null)
let toastTimer
function showToast(msg) {
  clearTimeout(toastTimer)
  toast.value = msg
  toastTimer = setTimeout(() => (toast.value = null), 2400)
}

// ---------- Utilities ----------
function fmtUSD(v) {
  if (v == null) return '—'
  const n = Number(v)
  if (Number.isNaN(n)) return String(v)
  return new Intl.NumberFormat(undefined, { style: 'currency', currency: 'USD' }).format(n)
}
function fmtTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return isNaN(d.getTime()) ? '' : d.toLocaleString()
}
function clamp01(n) { return Math.max(0, Math.min(1, n)) }

// ---------- Data Fetch ----------
const initialLoading = ref(true)
async function triggerFetches() {
  try {
    await Promise.all([
      tasks.fetchTasks(pid.value),
      tasks.fetchProgress(pid.value),
      expenses.fetchExpenses(pid.value),
      // categories for expense lines
      catalog.categories?.length ? Promise.resolve() : catalog.fetchCategories?.(),
    ])
  } finally {
    initialLoading.value = false
  }
}

onMounted(async () => {
  if (!project.value && projects.fetchOne) {
    try { await projects.fetchOne(pid.value) } catch {}
  }
  await triggerFetches()
})
watch(pid, () => { initialLoading.value = true; triggerFetches() })

// ====================================================================
// TASKS (create/update/delete) + COMMENTS (list/add/delete)
// ====================================================================
const STATUS_OPTS = ['todo', 'doing', 'done']
const newTitle = ref('')

// pending flags (prevents double submit)
const isAddingTask = ref(false)
const isSavingExpenseId = ref(null) // number | null
const isAddingLineFor = ref(null)   // eid | null
const isSavingLineKey = ref(null)   // `${eid}:${lid}` | null

async function addTask() {
  const title = newTitle.value.trim()
  if (!title || isAddingTask.value) return
  isAddingTask.value = true
  try {
    await tasks.createTask(pid.value, { title })
    newTitle.value = ''
    // Progress often changes with new tasks
    await tasks.fetchProgress(pid.value)
    showToast('Task added')
  } catch (e) {
    showToast(tasks.errors?.mutate || e?.message || 'Failed to add task')
  } finally {
    isAddingTask.value = false
  }
}
async function changeStatus(task, ev) {
  const status = ev.target.value
  try {
    await tasks.updateTask(pid.value, task.id, { status })
    await tasks.fetchProgress(pid.value)
    showToast('Status updated')
  } catch (e) {
    showToast(tasks.errors?.mutate || e?.message || 'Failed to update status')
  }
}
async function saveTitle(task, ev) {
  const title = ev?.target?.value?.trim?.() ?? task.title
  if (!title || title === task.title) return
  try {
    await tasks.updateTask(pid.value, task.id, { title })
    showToast('Title saved')
  } catch (e) {
    showToast(tasks.errors?.mutate || e?.message || 'Failed to save title')
  }
}
async function deleteTask(task) {
  if (!confirm('Delete this task?')) return
  try {
    await tasks.deleteTask(pid.value, task.id)
    await tasks.fetchProgress(pid.value)
    showToast('Task deleted')
  } catch (e) {
    showToast(tasks.errors?.mutate || e?.message || 'Failed to delete task')
  }
}

// ---------- Comments ----------
const openComments = reactive(new Set())        // task IDs with thread open
const newCommentByTid = reactive({})            // { [tid]: string }

function toggleComments(t) {
  if (openComments.has(t.id)) {
    openComments.delete(t.id)
  } else {
    openComments.add(t.id)
    if (!tasks.commentsByTask[t.id]?.length) {
      tasks.fetchComments(pid.value, t.id).catch(() => {})
    }
  }
}
async function addComment(t) {
  const body = (newCommentByTid[t.id] || '').trim()
  if (!body) return
  try {
    await tasks.addComment(pid.value, t.id, body)
    newCommentByTid[t.id] = ''
  } catch {
    // store holds error per task
  }
}
async function deleteComment(t, c) {
  if (!confirm('Delete this comment?')) return
  try {
    await tasks.deleteComment(pid.value, t.id, c.id)
  } catch {}
}

// ====================================================================
// EXPENSES
//  - Header inline edit (date/vendor/ref/memo)
//  - Lines CRUD with unit price pulled from catalog components per category
// ====================================================================

// ----- Header editing -----
const editing = reactive(new Set())
const draftById = reactive({}) // { [eid]: { expense_date, vendor, reference_no, memo } }

function startEdit(e) {
  editing.add(e.id)
  draftById[e.id] = {
    expense_date: e.expense_date || new Date().toISOString().slice(0, 10),
    vendor: e.vendor || '',
    reference_no: e.reference_no || '',
    memo: e.memo || '',
  }
}
function cancelEdit(e) {
  editing.delete(e.id)
  delete draftById[e.id]
  if (expenses.errors.mutateById[e.id]) expenses.errors.mutateById[e.id] = null
}
function isoDateValid(s) {
  return typeof s === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(s)
}
async function saveEdit(e) {
  const d = draftById[e.id]
  if (!d || !isoDateValid(d.expense_date)) {
    expenses.errors.mutateById[e.id] = 'Please provide a valid ISO date (YYYY-MM-DD).'
    return
  }
  if (isSavingExpenseId.value) return
  isSavingExpenseId.value = e.id
  try {
    await expenses.patchExpense(pid.value, e.id, {
      expense_date: d.expense_date,
      vendor: d.vendor || null,
      reference_no: d.reference_no || null,
      memo: d.memo || null,
    })
    showToast('Expense saved')
    cancelEdit(e)
  } catch {
    showToast(expenses.errors?.mutateById?.[e.id] || 'Failed to save expense')
  } finally {
    isSavingExpenseId.value = null
  }
}
async function addExpense() {
  const today = new Date().toISOString().slice(0, 10)
  try {
    const created = await expenses.createExpense(pid.value, { expense_date: today })
    startEdit(created)
    showToast('Expense created')
  } catch {
    showToast(expenses.errors?.mutateById?.new || 'Failed to create expense')
  }
}

// ----- Lines state -----
// open lines per expense
const openLines = reactive(new Set())

// drafts:
// - new line: newLineByEid[eid] = { category_id, qty, _unit }
// - edit line: editLineDraft[`${eid}:${lid}`] = { category_id, qty, _unit }
const newLineByEid = reactive({})
const editLineDraft = reactive({})

function ensureNewLine(eid) {
  if (!newLineByEid[eid]) {
    newLineByEid[eid] = { category_id: null, qty: 1, _unit: 0 }
  }
}
function toggleLines(e) {
  if (openLines.has(e.id)) openLines.delete(e.id)
  else { openLines.add(e.id); ensureNewLine(e.id) }
}
function validLineDraft(d) {
  if (!d) return 'Invalid payload'
  if (!d.category_id) return 'Select a category'
  const q = Number(d.qty ?? d.quantity)
  if (!(q > 0)) return 'Quantity must be > 0'
  return null
}

// Pull unit price from catalog components for a given category
async function loadUnitForCategory(category_id) {
  if (!category_id) return 0
  try {
    await catalog.fetchComponents({ category_id })
  } catch { return 0 }
  const first = (catalog.components || [])[0]
  return Number(first?.default_unit_price_usd ?? 0)
}
async function onNewLineCategoryChange(eid) {
  const catId = newLineByEid[eid]?.category_id
  newLineByEid[eid]._unit = await loadUnitForCategory(catId)
}
async function onEditLineCategoryChange(eid, ln) {
  const key = `${eid}:${ln.id}`
  const catId = editLineDraft[key]?.category_id
  editLineDraft[key]._unit = await loadUnitForCategory(catId)
}
function startEditLine(eid, ln) {
  const k = `${eid}:${ln.id}`
  editLineDraft[k] = {
    category_id: ln.category_id ?? null,
    qty: Number(ln.quantity ?? ln.qty ?? 1),
    _unit: Number(ln.unit_price_usd ?? 0), // seed with server value
  }
}
function cancelEditLine(eid, ln) {
  const k = `${eid}:${ln.id}`
  delete editLineDraft[k]
  if (expenses.errors.lineByKey[k]) expenses.errors.lineByKey[k] = null
}

async function addLine(e) {
  ensureNewLine(e.id)
  const d = newLineByEid[e.id]
  const msg = validLineDraft(d)
  if (msg) { expenses.errors.lineByKey[`${e.id}:new`] = msg; return }
  if (d._unit == null) d._unit = await loadUnitForCategory(d.category_id)

  if (isAddingLineFor.value) return
  isAddingLineFor.value = e.id
  try {
    await expenses.addLine(pid.value, e.id, {
      category_id: d.category_id,
      qty: Number(d.qty),
      unit_price_usd: Number(d._unit || 0),
    })
    newLineByEid[e.id] = { category_id: null, qty: 1, _unit: 0 }
    showToast('Line added')
  } catch { /* store error inline */ }
  finally { isAddingLineFor.value = null }
}

async function saveLine(eid, ln) {
  const k = `${eid}:${ln.id}`
  const d = editLineDraft[k]
  const msg = validLineDraft(d)
  if (msg) { expenses.errors.lineByKey[k] = msg; return }
  if (d._unit == null) d._unit = await loadUnitForCategory(d.category_id)

  if (isSavingLineKey.value) return
  isSavingLineKey.value = k
  try {
    await expenses.patchLine(pid.value, eid, ln.id, {
      category_id: d.category_id,
      qty: Number(d.qty),
      unit_price_usd: Number(d._unit || 0),
    })
    delete editLineDraft[k]
    showToast('Line saved')
  } catch { /* store error inline */ }
  finally { isSavingLineKey.value = null }
}

async function removeLine(eid, ln) {
  if (!confirm('Delete this line?')) return
  try {
    await expenses.deleteLine(pid.value, eid, ln.id)
    showToast('Line deleted')
  } catch { /* store error inline */ }
}

// Expense subtotal: prefer server, else compute from server line values
function expenseTotal(exp) {
  if (typeof exp.total_usd === 'number') return exp.total_usd
  return (exp.lines || []).reduce((sum, ln) => {
    const q = Number(ln.quantity ?? ln.qty ?? 0)
    const u = Number(ln.unit_price_usd ?? 0)
    return sum + q * u
  }, 0)
}
</script>
<template>
  <div class="p-6 space-y-6 max-w-5xl mx-auto bg-[#faf7f2] min-h-screen text-gray-900">
    <!-- SR-friendly live region for toasts -->
    <div aria-live="polite" aria-atomic="true" class="sr-only">{{ toast || '' }}</div>

    <!-- Header -->
    <div class="flex items-center justify-between gap-3">
      <div>
        <h1 class="text-2xl font-semibold">
          {{ project ? `${project.code} — ${project.name}` : 'Project' }}
        </h1>
        <RouterLink class="text-sm underline text-gray-700 hover:text-gray-900" to="/projects">
          ← Back to projects
        </RouterLink>
      </div>
      <div class="text-sm" v-if="progress">
        Progress: {{ Math.round(progressPercent) }}%
      </div>
    </div>

    <!-- Visible Toast -->
    <div v-if="toast" class="rounded-xl bg-gray-900 text-white px-3 py-2 text-sm inline-block shadow">
      {{ toast }}
    </div>

    <!-- Progress -->
    <section class="space-y-3">
      <div class="h-3 w-full rounded-full bg-gray-300 overflow-hidden" role="progressbar"
           :aria-valuenow="Math.round(progressPercent)" aria-valuemin="0" aria-valuemax="100">
        <div class="h-3 bg-gray-900" :style="{ width: progressPercent + '%' }" />
      </div>
      <div class="text-xs" v-if="progress">
        {{ progress.totals?.done ?? 0 }} / {{ progress.totals?.total ?? 0 }} tasks done
        · leaves {{ progress.totals?.leaves_done ?? 0 }}/{{ progress.totals?.leaves_total ?? 0 }}
      </div>
      <div class="text-xs text-red-600" v-if="tasks.errors.progress">{{ tasks.errors.progress }}</div>
    </section>

    <!-- Loading skeleton (initial page) -->
    <section v-if="initialLoading" class="space-y-4">
      <div class="h-6 w-40 bg-gray-200 rounded animate-pulse"></div>
      <div class="space-y-2">
        <div class="h-10 bg-gray-200 rounded animate-pulse"></div>
        <div class="h-10 bg-gray-200 rounded animate-pulse"></div>
        <div class="h-10 bg-gray-200 rounded animate-pulse"></div>
      </div>
    </section>

    <!-- Main content -->
    <section v-else class="space-y-6">
      <!-- Tasks -->
      <section class="space-y-3 border border-gray-300 rounded-xl p-4 bg-white">
        <div class="flex items-center justify-between">
          <h2 class="font-semibold">Tasks</h2>
          <button
            class="px-3 py-2 rounded-xl bg-gray-900 text-white hover:bg-gray-800 transition disabled:opacity-60"
            :disabled="isAddingTask"
            @click="addTask"
          >
            {{ isAddingTask ? 'Adding…' : 'Add task' }}
          </button>
        </div>

        <div class="flex gap-2">
          <input
            v-model="newTitle"
            placeholder="Task title"
            class="min-h-[40px] border border-gray-300 rounded-lg p-2 flex-1 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-gray-900/30"
          />
        </div>

        <ul class="divide-y divide-gray-200 border border-gray-200 rounded-lg">
          <li v-for="t in taskList" :key="t.id" class="p-3">
            <div class="flex flex-wrap items-center gap-3">
              <select
                class="min-h-[40px] border border-gray-300 rounded-lg p-2"
                :value="t.status || 'todo'"
                @change="changeStatus(t, $event)"
              >
                <option v-for="s in STATUS_OPTS" :key="s" :value="s">{{ s }}</option>
              </select>

              <input
                class="min-h-[40px] border border-gray-300 rounded-lg p-2 flex-1"
                :defaultValue="t.title"
                @blur="saveTitle(t, $event)"
                @keyup.enter="saveTitle(t, $event)"
              />

              <button
                class="px-3 py-2 rounded-xl bg-gray-900 text-white hover:bg-gray-800 transition"
                type="button"
                @click="toggleComments(t)"
                :aria-expanded="openComments.has(t.id) ? 'true' : 'false'"
                :aria-controls="`comments-${t.id}`"
              >
                Comments ({{ (tasks.commentsByTask[t.id]?.length ?? 0) }})
              </button>

              <button
                class="text-red-700 hover:underline underline-offset-2"
                type="button"
                @click="deleteTask(t)"
              >
                Delete
              </button>
            </div>

            <!-- Comments thread -->
            <div
              v-if="openComments.has(t.id)"
              class="mt-3 border-t border-gray-200 pt-3"
              :id="`comments-${t.id}`"
            >
              <div class="text-sm text-red-600 mb-2" v-if="tasks.errors.comments[t.id]">
                {{ tasks.errors.comments[t.id] }}
              </div>

              <ul class="space-y-2">
                <li
                  v-for="c in (tasks.commentsByTask[t.id] || [])"
                  :key="c.id"
                  class="rounded-lg border border-gray-200 p-2"
                >
                  <div class="flex items-start gap-2">
                    <div class="flex-1">
                      <div class="text-sm">{{ c.body }}</div>
                      <div class="text-xs text-gray-600 mt-1">{{ fmtTime(c.created_at) }}</div>
                    </div>
                    <button
                      class="text-red-700 text-xs hover:underline"
                      type="button"
                      @click="deleteComment(t, c)"
                    >
                      Delete
                    </button>
                  </div>
                </li>

                <li v-if="!tasks.loading.comments[t.id] && !(tasks.commentsByTask[t.id]?.length)">
                  <span class="text-sm text-gray-500">No comments yet.</span>
                </li>
                <li v-if="tasks.loading.comments[t.id]" class="text-sm text-gray-500">Loading comments…</li>
              </ul>

              <form class="mt-3 flex items-start gap-2" @submit.prevent="addComment(t)">
                <textarea
                  v-model="newCommentByTid[t.id]"
                  rows="2"
                  placeholder="Write a comment…"
                  class="flex-1 border border-gray-300 rounded-lg p-2 resize-y placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-gray-900/20"
                  maxlength="4000"
                />
                <button class="px-3 py-2 rounded-xl bg-gray-900 text-white hover:bg-gray-800 transition">
                  Add
                </button>
              </form>
              <div class="text-xs text-red-600 mt-1" v-if="tasks.errors.commentsMutate[t.id]">
                {{ tasks.errors.commentsMutate[t.id] }}
              </div>
            </div>
          </li>

          <li v-if="!taskList.length && !tasks.loading.tasks" class="p-3 text-sm text-gray-500">
            No tasks yet.
          </li>
          <li v-if="tasks.loading.tasks" class="p-3 text-sm text-gray-500">Loading tasks…</li>
        </ul>

        <div class="text-sm text-red-600" v-if="tasks.errors.mutate">{{ tasks.errors.mutate }}</div>
        <div class="text-xs text-red-600" v-if="tasks.errors.tasks">{{ tasks.errors.tasks }}</div>
      </section>

      <!-- Expenses: header inline edit + LINES (unit auto from components) -->
      <section class="space-y-4 border border-gray-300 rounded-xl p-4 bg-white">
        <div class="flex items-center justify-between">
          <h2 class="font-semibold">Expenses</h2>
          <button
            class="px-3 py-2 rounded-xl bg-gray-900 text-white hover:bg-gray-800 transition"
            type="button"
            @click="addExpense"
          >
            Add expense
          </button>
        </div>

        <ul class="divide-y divide-gray-200">
          <li v-for="e in expenseList" :key="e.id" class="py-4 space-y-3">
            <!-- Header: read-only or edit -->
            <div v-if="!editing.has(e.id)" class="flex flex-wrap items-center justify-between gap-3">
              <div>
                <div class="font-medium">{{ e.expense_date }} — {{ e.vendor || '—' }}</div>
                <div class="text-xs text-gray-600">
                  Ref: {{ e.reference_no || '—' }} · Memo: {{ e.memo || '—' }}
                </div>
              </div>
              <div class="flex items-center gap-2">
                <div class="text-sm">Total: {{ fmtUSD(expenseTotal(e)) }}</div>
                <button
                  class="px-3 py-2 rounded-xl bg-gray-900 text-white hover:bg-gray-800 transition"
                  type="button"
                  @click="startEdit(e)"
                >
                  Edit
                </button>
                <button
                  class="px-3 py-2 rounded-xl border border-gray-300 hover:bg-gray-100 transition"
                  type="button"
                  @click="toggleLines(e)"
                  :aria-expanded="openLines.has(e.id) ? 'true' : 'false'"
                  :aria-controls="`lines-${e.id}`"
                >
                  {{ openLines.has(e.id) ? 'Hide lines' : 'Show lines' }}
                </button>
              </div>
            </div>

            <form v-else class="space-y-2" @submit.prevent="saveEdit(e)">
              <div class="grid grid-cols-1 md:grid-cols-4 gap-2">
                <label class="block">
                  <span class="text-xs text-gray-600">Date</span>
                  <input
                    v-model="draftById[e.id].expense_date"
                    type="date"
                    class="min-h-[40px] w-full border border-gray-300 rounded-lg p-2"
                    required
                  />
                </label>
                <label class="block">
                  <span class="text-xs text-gray-600">Vendor</span>
                  <input
                    v-model="draftById[e.id].vendor"
                    class="min-h-[40px] w-full border border-gray-300 rounded-lg p-2"
                    placeholder="Vendor"
                  />
                </label>
                <label class="block">
                  <span class="text-xs text-gray-600">Reference #</span>
                  <input
                    v-model="draftById[e.id].reference_no"
                    class="min-h-[40px] w-full border border-gray-300 rounded-lg p-2"
                    placeholder="Reference"
                  />
                </label>
                <label class="block md:col-span-1">
                  <span class="text-xs text-gray-600">Memo</span>
                  <input
                    v-model="draftById[e.id].memo"
                    class="min-h-[40px] w-full border border-gray-300 rounded-lg p-2"
                    placeholder="Memo"
                  />
                </label>
              </div>
              <div class="flex items-center gap-2">
                <button
                  class="px-3 py-2 rounded-xl bg-gray-900 text-white hover:bg-gray-800 transition disabled:opacity-60"
                  :disabled="isSavingExpenseId === e.id"
                >
                  {{ isSavingExpenseId === e.id ? 'Saving…' : 'Save' }}
                </button>
                <button
                  type="button"
                  class="px-3 py-2 rounded-xl border border-gray-300 hover:bg-gray-100 transition"
                  @click="cancelEdit(e)"
                >
                  Cancel
                </button>
                <div class="text-sm text-red-600" v-if="expenses.errors.mutateById[e.id]">
                  {{ expenses.errors.mutateById[e.id] }}
                </div>
              </div>
            </form>

            <!-- Lines panel -->
            <div v-if="openLines.has(e.id)" :id="`lines-${e.id}`" class="border-t border-gray-200 pt-3 space-y-3">
              <!-- Existing lines -->
              <div v-if="(e.lines && e.lines.length)" class="space-y-2">
                <div
                  v-for="ln in e.lines"
                  :key="ln.id"
                  class="grid grid-cols-1 md:grid-cols-12 gap-2 items-center border border-gray-200 rounded-lg p-2"
                >
                  <!-- Edit mode -->
                  <template v-if="editLineDraft[`${e.id}:${ln.id}`]">
                    <select
                      class="min-h-[40px] md:col-span-5 border border-gray-300 rounded-lg p-2"
                      v-model.number="editLineDraft[`${e.id}:${ln.id}`].category_id"
                      @change="onEditLineCategoryChange(e.id, ln)"
                    >
                      <option :value="null" disabled>Select category…</option>
                      <option v-for="c in catalog.categories" :key="c.id" :value="c.id">
                        {{ c.name }}
                      </option>
                    </select>

                    <input
                      class="min-h-[40px] md:col-span-2 border border-gray-300 rounded-lg p-2"
                      type="number" min="0.0000001" step="0.0001"
                      v-model.number="editLineDraft[`${e.id}:${ln.id}`].qty"
                      placeholder="Qty"
                    />

                    <!-- Unit (read-only) from draft -->
                    <div class="md:col-span-2 text-sm">
                      Unit: {{ fmtUSD(editLineDraft[`${e.id}:${ln.id}`]._unit || 0) }}
                    </div>

                    <!-- Live total -->
                    <div class="md:col-span-2 font-medium">
                      = {{ fmtUSD(
                        Number(editLineDraft[`${e.id}:${ln.id}`].qty || 0) *
                        Number(editLineDraft[`${e.id}:${ln.id}`]._unit || 0)
                      ) }}
                    </div>

                    <div class="md:col-span-12 flex gap-2">
                      <button
                        class="px-3 py-2 rounded-xl bg-gray-900 text-white hover:bg-gray-800 transition disabled:opacity-60"
                        type="button"
                        :disabled="isSavingLineKey === `${e.id}:${ln.id}`"
                        @click="saveLine(e.id, ln)"
                      >
                        {{ isSavingLineKey === `${e.id}:${ln.id}` ? 'Saving…' : 'Save' }}
                      </button>
                      <button
                        class="px-3 py-2 rounded-xl border border-gray-300 hover:bg-gray-100 transition"
                        type="button"
                        @click="cancelEditLine(e.id, ln)"
                      >
                        Cancel
                      </button>
                      <div class="text-sm text-red-600" v-if="expenses.errors.lineByKey[`${e.id}:${ln.id}`]">
                        {{ expenses.errors.lineByKey[`${e.id}:${ln.id}`] }}
                      </div>
                    </div>
                  </template>

                  <!-- Read-only line row (server values) -->
                  <template v-else>
                    <div class="md:col-span-5">
                      <div class="font-medium">
                        {{ catalog.categories.find(c => c.id === ln.category_id)?.name || ('#'+ln.category_id) }}
                      </div>
                      <div class="text-xs text-gray-600">ID: {{ ln.id }}</div>
                    </div>
                    <div class="md:col-span-2">
                      {{ ln.quantity ?? ln.qty }}
                    </div>
                    <div class="md:col-span-2">
                      Unit: {{ fmtUSD(ln.unit_price_usd) }}
                    </div>
                    <div class="md:col-span-2 font-medium">
                      {{ fmtUSD(ln.line_total_usd ?? ((Number(ln.quantity ?? ln.qty ?? 0)) * Number(ln.unit_price_usd ?? 0))) }}
                    </div>

                    <div class="md:col-span-12 flex gap-2">
                      <button
                        class="px-3 py-2 rounded-xl bg-gray-900 text-white hover:bg-gray-800 transition"
                        type="button"
                        @click="startEditLine(e.id, ln)"
                      >
                        Edit
                      </button>
                      <button
                        class="text-red-700 underline underline-offset-2"
                        type="button"
                        @click="removeLine(e.id, ln)"
                      >
                        Delete
                      </button>
                      <div class="text-sm text-red-600" v-if="expenses.errors.lineByKey[`${e.id}:${ln.id}`]">
                        {{ expenses.errors.lineByKey[`${e.id}:${ln.id}`] }}
                      </div>
                    </div>
                  </template>
                </div>
              </div>

              <!-- Add new line -->
              <div class="grid grid-cols-1 md:grid-cols-12 gap-2 items-center border border-gray-200 rounded-lg p-2">
                <select
                  class="min-h-[40px] md:col-span-5 border border-gray-300 rounded-lg p-2"
                  v-model.number="(newLineByEid[e.id] || (newLineByEid[e.id] = { category_id: null, qty: 1, _unit: 0 })).category_id"
                  @change="onNewLineCategoryChange(e.id)"
                >
                  <option :value="null" disabled>Select category…</option>
                  <option v-for="c in catalog.categories" :key="c.id" :value="c.id">
                    {{ c.name }}
                  </option>
                </select>

                <input
                  class="min-h-[40px] md:col-span-2 border border-gray-300 rounded-lg p-2"
                  type="number" min="0.0000001" step="0.0001"
                  v-model.number="newLineByEid[e.id].qty"
                  placeholder="Qty"
                />

                <!-- Unit (read-only) -->
                <div class="md:col-span-2 text-sm">
                  Unit: {{ fmtUSD(newLineByEid[e.id]._unit || 0) }}
                </div>

                <!-- Live total -->
                <div class="md:col-span-2 font-medium">
                  = {{ fmtUSD(
                    Number(newLineByEid[e.id].qty || 0) *
                    Number(newLineByEid[e.id]._unit || 0)
                  ) }}
                </div>

                <div class="md:col-span-12 flex gap-2">
                  <button
                    class="px-3 py-2 rounded-xl bg-gray-900 text-white hover:bg-gray-800 transition disabled:opacity-60"
                    type="button"
                    :disabled="isAddingLineFor === e.id"
                    @click="addLine(e)"
                  >
                    {{ isAddingLineFor === e.id ? 'Adding…' : 'Add line' }}
                  </button>
                  <div class="text-sm text-red-600" v-if="expenses.errors.lineByKey[`${e.id}:new`]">
                    {{ expenses.errors.lineByKey[`${e.id}:new`] }}
                  </div>
                </div>
              </div>

              <!-- Expense total (live) -->
              <div class="text-right font-semibold">
                Subtotal: {{ fmtUSD(expenseTotal(e)) }}
              </div>
            </div>
          </li>

          <li v-if="!expenseList.length && !expenses.loading.expenses" class="py-3 text-sm text-gray-500">
            No expenses yet.
          </li>
          <li v-if="expenses.loading.expenses" class="py-3 text-sm text-gray-500">
            Loading expenses…
          </li>
        </ul>

        <div class="text-xs text-red-600" v-if="expenses.errors.expenses">{{ expenses.errors.expenses }}</div>
      </section>

      <!-- Manual Refetch -->
      <div class="flex gap-3">
        <button
          class="px-3 py-2 rounded-xl bg-gray-900 text-white hover:bg-gray-800 transition"
          @click="triggerFetches"
        >
          Refetch
        </button>
      </div>
    </section>
  </div>
</template>
