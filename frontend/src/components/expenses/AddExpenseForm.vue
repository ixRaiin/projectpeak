<template>
  <form @submit.prevent="submit" class="space-y-5">
    <!-- Header -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <label class="block md:col-span-1">
        <span class="text-sm text-gray-600">Date *</span>
        <input v-model="form.expense_date" type="date" required class="w-full border rounded p-2" />
        <p v-if="fieldErr.expense_date" class="text-xs text-red-600 mt-1">{{ fieldErr.expense_date }}</p>
      </label>

      <label class="block md:col-span-2">
        <span class="text-sm text-gray-600">Vendor *</span>
        <input v-model="form.vendor" placeholder="e.g., Acme Supplies" required class="w-full border rounded p-2" />
        <p v-if="fieldErr.vendor" class="text-xs text-red-600 mt-1">{{ fieldErr.vendor }}</p>
      </label>

      <label class="block md:col-span-1">
        <span class="text-sm text-gray-600">Reference #</span>
        <input v-model="form.reference_no" placeholder="INV-00123" class="w-full border rounded p-2" />
      </label>
    </div>

    <label class="block">
      <span class="text-sm text-gray-600">Note</span>
      <textarea v-model="form.note" rows="2" class="w-full border rounded p-2"></textarea>
    </label>

    <!-- Lines -->
    <div class="space-y-3">
      <div class="flex items-center justify-between">
        <h3 class="font-semibold">Lines</h3>
        <button type="button" class="text-sm underline" @click="addLine">Add line</button>
      </div>

      <div
        v-for="(ln, idx) in form.lines"
        :key="ln.key"
        class="grid grid-cols-1 md:grid-cols-12 gap-2 items-end border rounded p-3"
      >
        <!-- Category -->
        <label class="block md:col-span-3">
          <span class="text-sm text-gray-600">Category *</span>
          <select
            v-model.number="ln.category_id"
            class="w-full border rounded p-2"
            @change="onCategoryChange(idx)"
          >
            <option :value="null" disabled>Select category…</option>
            <option v-for="c in catalog.categories" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>
          <p v-if="lineErr[idx]?.category_id" class="text-xs text-red-600 mt-1">{{ lineErr[idx].category_id }}</p>
        </label>

        <!-- Component -->
        <label class="block md:col-span-4">
          <span class="text-sm text-gray-600">Component *</span>
          <select
            v-model.number="ln.component_id"
            class="w-full border rounded p-2"
            :disabled="!ln.category_id"
            @change="onComponentChange(idx)"
          >
            <option :value="null" disabled>Select component…</option>
            <option v-for="cmp in filteredComponents(ln.category_id)" :key="cmp.id" :value="cmp.id">
              {{ cmp.name }}
            </option>
          </select>
          <p v-if="lineErr[idx]?.component_id" class="text-xs text-red-600 mt-1">{{ lineErr[idx].component_id }}</p>
        </label>

        <!-- Qty -->
        <label class="block md:col-span-2">
          <span class="text-sm text-gray-600">Qty *</span>
          <input v-model.number="ln.quantity" type="number" min="0" step="0.0001" class="w-full border rounded p-2" />
          <p v-if="lineErr[idx]?.quantity" class="text-xs text-red-600 mt-1">{{ lineErr[idx].quantity }}</p>
        </label>

        <!-- Unit Price (read‑only) -->
        <label class="block md:col-span-2">
          <span class="text-sm text-gray-600">Unit Price</span>
          <div class="w-full border rounded p-2 bg-gray-50 text-gray-800">
            <span v-if="isFiniteNumber(ln.unit_price_usd)">
              ${{ Number(ln.unit_price_usd).toFixed(2) }}
            </span>
            <span v-else class="text-gray-400">—</span>
          </div>
          <!-- <p class="text-[11px] text-gray-500 mt-1" v-if="ln._prefilled">
            Prefilled from component default.
          </p> -->
        </label>

        <!-- Line total + remove -->
        <!-- <div class="md:col-span-1 flex items-center justify-between md:justify-end gap-3">
          <div class="text-sm text-gray-700 font-medium whitespace-nowrap">
            ${{ lineTotal(ln).toFixed(2) }}
          </div>
          <button type="button" class="text-red-600 text-sm underline" @click="removeLine(idx)">Remove</button>
        </div> -->
      </div>

      <p v-if="fieldErr.lines" class="text-xs text-red-600">{{ fieldErr.lines }}</p>

      <!-- Summary -->
      <div class="flex items-center justify-between border rounded p-3 bg-gray-50 text-sm">
        <span>Subtotal</span>
        <span class="font-medium">${{ subtotal.toFixed(2) }}</span>
      </div>
    </div>

    <!-- Actions -->
    <div class="flex gap-2 pt-2">
      <button
        class="px-4 py-2 rounded bg-black text-white focus:outline-none focus:ring-2 focus:ring-black/40 disabled:opacity-50"
        :disabled="submitting"
      >
        {{ submitting ? 'Saving…' : 'Save Expense' }}
      </button>
      <button type="button" class="px-4 py-2 rounded border hover:bg-gray-50" @click="$emit('cancel')">
        Cancel
      </button>
    </div>

    <p v-if="error" class="text-red-600 text-sm">{{ error }}</p>
  </form>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useExpensesStore } from '@/stores/expenses'
import { useCatalog } from '@/stores/catalog'

const props = defineProps({
  projectId: { type: [Number, String], required: true },
})
const emit = defineEmits(['success', 'cancel'])

const expenses = useExpensesStore()
const catalog = useCatalog()

const error = ref(null)
const submitting = ref(false)
const fieldErr = ref({})
const lineErr = ref([])

const form = ref({
  expense_date: '',
  vendor: '',
  reference_no: '',
  note: '',
  lines: [],
})

const isFiniteNumber = (v) => Number.isFinite(Number(v))

/* -------- line helpers -------- */
function addLine() {
  form.value.lines.push({
    key: cryptoRandom(),
    category_id: null,
    component_id: null,
    quantity: 1,
    unit_price_usd: '',
    _prefilled: false,
  })
}
function removeLine(idx) {
  form.value.lines.splice(idx, 1)
}

function filteredComponents(categoryId) {
  if (!categoryId) return []
  // Components are loaded per category into catalog.components
  return catalog.components.filter(c => Number(c.category_id) === Number(categoryId))
}

function onCategoryChange(idx) {
  const ln = form.value.lines[idx]
  if (!ln) return
  ln.component_id = null
  ln.unit_price_usd = ''
  ln._prefilled = false
  // Load components for the selected category (same pattern as Catalog.vue)
  if (ln.category_id) {
    catalog.fetchComponents({ category_id: ln.category_id }).catch(() => {})
  } else {
    // clear if deselected
    // (optional) catalog.components = []
  }
}

function onComponentChange(idx) {
  const ln = form.value.lines[idx]
  if (!ln || !ln.component_id) return
  // Look up in the currently loaded component list for this category
  const cmp = catalog.components.find(c => Number(c.id) === Number(ln.component_id))
  if (cmp) {
    // Prefer default_unit_price_usd; fall back to unit_price_usd if present
    const price = cmp.default_unit_price_usd ?? cmp.unit_price_usd
    if (price != null && Number.isFinite(Number(price))) {
      ln.unit_price_usd = Number(price)
      ln._prefilled = true
    }
  }
}

function onUnitPriceInput(idx) {
  const ln = form.value.lines[idx]
  if (ln) ln._prefilled = false
}

function lineTotal(ln) {
  const q = Number(ln.quantity || 0)
  const up = Number(ln.unit_price_usd || 0)
  return (Number.isFinite(q) ? q : 0) * (Number.isFinite(up) ? up : 0)
}

const subtotal = computed(() => form.value.lines.reduce((s, l) => s + lineTotal(l), 0))

/* -------- validation & submit -------- */
function validate() {
  fieldErr.value = {}
  lineErr.value = []

  if (!form.value.expense_date) fieldErr.value.expense_date = 'Date is required.'
  if (!form.value.vendor.trim()) fieldErr.value.vendor = 'Vendor is required.'
  if (!form.value.lines.length) fieldErr.value.lines = 'Add at least one line.'

  form.value.lines.forEach((ln, i) => {
    const e = {}
    if (!ln.category_id) e.category_id = 'Category is required.'
    if (!ln.component_id) e.component_id = 'Component is required.'
    if (!Number.isFinite(Number(ln.quantity)) || Number(ln.quantity) <= 0) e.quantity = 'Qty must be > 0.'
    lineErr.value[i] = e
  })

  return Object.keys(fieldErr.value).length === 0 &&
         lineErr.value.every(obj => !obj || Object.keys(obj).length === 0)
}

async function submit() {
  error.value = null
  if (submitting.value) return
  if (!validate()) return

  try {
    submitting.value = true
    const pid = Number(props.projectId)

    const payload = {
      expense_date: form.value.expense_date,
      vendor: form.value.vendor,
      reference_no: form.value.reference_no || undefined,
      memo: form.value.note || undefined, // maps to your API's 'memo'
      lines: form.value.lines.map(l => ({
        category_id: Number(l.category_id),
        component_id: Number(l.component_id),
        quantity: Number(l.quantity || 1),
        unit_price_usd: l.unit_price_usd === '' ? undefined : Number(l.unit_price_usd),
      })),
    }

    const created = await expenses.createExpense(pid, payload)
    emit('success', created)

    // reset for next use
    form.value = { expense_date: '', vendor: '', reference_no: '', note: '', lines: [] }
    addLine()
  } catch (e) {
    error.value = e?.message || 'Failed to save expense'
  } finally {
    submitting.value = false
  }
}

/* -------- boot -------- */
function cryptoRandom() {
  if (window.crypto?.getRandomValues) {
    const a = new Uint32Array(1)
    window.crypto.getRandomValues(a)
    return `k${a[0].toString(36)}`
  }
  return `k${Math.random().toString(36).slice(2)}`
}

onMounted(async () => {
  // Load categories once (same pattern as your Catalog.vue)
  if (!catalog.categories.length) {
    try { await catalog.fetchCategories({}) } catch {/* ignore errors */ }
  }
  // Components are fetched on demand per selected category
  if (!form.value.lines.length) addLine()
})
</script>
