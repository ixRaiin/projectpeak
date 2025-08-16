<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRoute, RouterLink } from 'vue-router';
import api from '@/lib/api';

import { useProjects } from '@/stores/projects';
import { useExpenses } from '@/stores/expenses';
import { useTasks } from '@/stores/tasks';
import { useCatalog } from '@/stores/catalog';

const route = useRoute();
const pid = computed(() => Number(route.params.id));

const projects = useProjects();
const expenses = useExpenses();
const tasks = useTasks();
const catalog = useCatalog();

const project = computed(() =>
  projects.items.find(p => p.id === pid.value) || null
);

// ---------- summary ----------
const summary = ref(null);
const loadingSummary = ref(false);
const sumErr = ref(null);

// ---------- expenses form ----------
const form = ref({
  expense_date: new Date().toISOString().slice(0, 10),
  vendor: '',
  memo: '',
  lines: [{ category_id: null, quantity: 1, unit_price_usd: null, note: '' }],
});
function addLine() {
  form.value.lines.push({ category_id: null, quantity: 1, unit_price_usd: null, note: '' });
}
function removeLine(i) { form.value.lines.splice(i, 1); }

const canSubmit = computed(() => {
  if (!form.value.expense_date) return false;
  if (!form.value.lines.length) return false;
  return form.value.lines.every(l =>
    l.category_id &&
    Number(l.quantity) > 0 &&
    (l.unit_price_usd === 0 || Number(l.unit_price_usd) > 0)
  );
});

// ---------- tasks quick add / edit ----------
const newTask = ref({ title: '' });
const STATUS_OPTS = ['todo', 'doing', 'done'];

async function addRootTask() {
  const title = newTask.value.title.trim();
  if (!title) return;
  await tasks.create(pid.value, { title });
  newTask.value.title = '';
  await tasks.fetchProgress(pid.value);
}
async function onChangeStatus(t, ev) {
  await tasks.update(pid.value, t.id, { status: ev.target.value });
  await tasks.fetchProgress(pid.value);
}
async function onBlurTitle(t, ev) {
  const title = ev.target.value.trim();
  if (title && title !== t.title) await tasks.update(pid.value, t.id, { title });
}
async function onDeleteTask(t) {
  await tasks.remove(pid.value, t.id);
  await tasks.fetchProgress(pid.value);
}

// ---------- utils ----------
function fmtUSD(v) {
  if (v == null) return '—';
  const n = Number(v);
  if (Number.isNaN(n)) return String(v);
  return new Intl.NumberFormat(undefined, { style: 'currency', currency: 'USD' }).format(n);
}
async function loadSummary() {
  loadingSummary.value = true; sumErr.value = null;
  try {
    summary.value = await api.get(`/projects/${pid.value}/summary`);
  } catch (e) {
    sumErr.value = e?.message || 'Failed to load summary';
  } finally {
    loadingSummary.value = false;
  }
}
async function submitExpense() {
  if (!canSubmit.value) return;
  const payload = {
    expense_date: form.value.expense_date,
    vendor: form.value.vendor || null,
    memo: form.value.memo || null,
    lines: form.value.lines.map(l => ({
      category_id: l.category_id,
      quantity: Number(l.quantity),
      unit_price_usd: Number(l.unit_price_usd),
      note: l.note || null,
    })),
  };
  await expenses.create(pid.value, payload);
  await loadSummary();
  form.value.vendor = '';
  form.value.memo = '';
  form.value.lines = [{ category_id: null, quantity: 1, unit_price_usd: null, note: '' }];
}

onMounted(async () => {
  // make sure project & catalogs are loaded
  if (!project.value && projects.fetchOne) await projects.fetchOne(pid.value);
  if (!catalog.categories.length && catalog.fetchCategories) await catalog.fetchCategories();

  await projects.openDetail?.(pid.value);
  await expenses.fetchForProject(pid.value);
  await tasks.fetchForProject(pid.value);
  await tasks.fetchProgress(pid.value);
  await loadSummary();
});
</script>

<template>
  <div class="p-6 space-y-6 max-w-5xl mx-auto">
    <div class="flex items-center justify-between gap-3">
      <div>
        <h1 class="text-2xl font-semibold">
          {{ project ? `${project.code} — ${project.name}` : 'Project' }}
        </h1>
        <RouterLink class="text-sm underline" to="/projects">← Back to projects</RouterLink>
      </div>
      <div class="text-sm text-gray-500" v-if="tasks.progress?.percent != null">
        Progress: {{ Math.round(tasks.progress.percent) }}%
      </div>
    </div>

    <!-- Tasks -->
    <section class="space-y-2 border rounded p-4">
      <h2 class="font-semibold mb-1">Tasks</h2>
      <form class="flex flex-wrap gap-2 items-center" @submit.prevent="addRootTask">
        <input v-model="newTask.title" placeholder="Task title" class="border rounded p-2 flex-1" />
        <button class="rounded bg-black text-white px-3 py-2 cursor-pointer">Add task</button>
      </form>

      <ul class="divide-y border rounded">
        <li v-for="t in tasks.items" :key="t.id" class="p-3 flex items-center gap-3">
          <select class="border rounded p-2" :value="t.status || 'todo'" @change="onChangeStatus(t, $event)">
            <option v-for="s in STATUS_OPTS" :key="s" :value="s">{{ s }}</option>
          </select>

          <input class="border rounded p-2 flex-1" :defaultValue="t.title" @blur="onBlurTitle(t, $event)" />

          <button class="text-red-600 text-sm" type="button" @click="onDeleteTask(t)">Delete</button>
        </li>
        <li v-if="!tasks.items.length" class="p-3 text-sm text-gray-500">No tasks yet.</li>
      </ul>
    </section>

    <!-- Expenses -->
    <section class="space-y-3">
      <h2 class="font-semibold">Add expense</h2>
      <form class="border rounded p-4 space-y-3" @submit.prevent="submitExpense">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
          <label class="block">
            <span class="text-sm text-gray-600">Date</span>
            <input v-model="form.expense_date" type="date" class="w-full border rounded p-2" />
          </label>
          <input v-model="form.vendor" placeholder="Vendor" class="border rounded p-2" />
          <input v-model="form.memo" placeholder="Memo" class="border rounded p-2" />
        </div>

        <div class="space-y-2">
          <div v-for="(l, i) in form.lines" :key="i" class="grid grid-cols-1 md:grid-cols-5 gap-2 items-center">
            <select v-model.number="l.category_id" class="border rounded p-2">
              <option :value="null" disabled>Select category…</option>
              <option v-for="c in catalog.categories" :key="c.id" :value="c.id">{{ c.name }}</option>
            </select>
            <input v-model.number="l.quantity" type="number" min="0" step="0.0001" placeholder="Qty" class="border rounded p-2" />
            <input v-model="l.unit_price_usd" type="number" step="0.0001" placeholder="Unit $" class="border rounded p-2" />
            <input v-model="l.note" placeholder="Note" class="border rounded p-2" />
            <button class="text-red-600 text-sm" type="button" @click="removeLine(i)">Remove</button>
          </div>
          <button class="text-sm underline" type="button" @click="addLine">+ Add line</button>
        </div>

        <button :disabled="!canSubmit" class="rounded bg-black text-white px-3 py-2 cursor-pointer disabled:opacity-60">
          Save expense
        </button>
      </form>

      <div>
        <h3 class="font-semibold mb-2">Expenses</h3>
        <ul class="divide-y border rounded">
          <li v-for="e in expenses.items" :key="e.id" class="p-3">
            <div class="font-medium">
              {{ e.expense_date }} — {{ e.vendor || '—' }} · Total: {{ fmtUSD(e.total_usd) }}
            </div>
            <ul class="text-sm text-gray-700 pl-4 list-disc">
              <li v-for="ln in e.lines || []" :key="ln.id">
                {{ catalog.categories.find(c => c.id === ln.category_id)?.name || ('#'+ln.category_id) }}
                — {{ ln.quantity }} × {{ fmtUSD(ln.unit_price_usd) }} = {{ fmtUSD(ln.line_total_usd) }}
              </li>
            </ul>
          </li>
          <li v-if="!expenses.items.length" class="p-3 text-sm text-gray-500">No expenses yet.</li>
        </ul>
      </div>
    </section>

    <!-- Summary -->
    <section class="space-y-3">
      <div class="flex items-center justify-between">
        <h2 class="font-semibold">Summary (planned vs actual)</h2>
        <button class="text-sm underline" type="button" @click="loadSummary" :disabled="loadingSummary">Refresh</button>
      </div>

      <div v-if="sumErr" class="text-red-600 text-sm">{{ sumErr }}</div>

      <div v-if="summary">
        <ul class="divide-y border rounded">
          <li v-for="r in summary.per_category" :key="r.category_id" class="p-3 flex items-center justify-between">
            <div class="font-medium">{{ r.category_name || ('#'+r.category_id) }}</div>
            <div class="text-sm">
              Planned {{ fmtUSD(r.planned_usd) }}
              · Actual {{ fmtUSD(r.actual_usd) }}
              · Var {{ fmtUSD(r.variance_usd) }}
            </div>
          </li>
        </ul>
        <div class="mt-3 p-3 border rounded bg-gray-50 text-sm">
          <div>Planned total: {{ fmtUSD(summary.totals?.planned_total_usd) }}</div>
          <div>Actual total: {{ fmtUSD(summary.totals?.actual_total_usd) }}</div>
          <div class="font-medium">Variance: {{ fmtUSD(summary.totals?.variance_total_usd) }}</div>
        </div>
      </div>
      <div v-else-if="loadingSummary" class="text-sm text-gray-500">Loading…</div>
      <div v-else class="text-sm text-gray-500">No summary yet.</div>
    </section>
  </div>
</template>
