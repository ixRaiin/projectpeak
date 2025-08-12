<script setup>
import { ref, onMounted, watch } from 'vue'
import { useComponents } from '@/stores/components'
import { useCategories } from '@/stores/categories'

const comps = useComponents()
const cats = useCategories()

const filter = ref({ category_id: null, q: '' })
const form = ref({ category_id: null, name: '', default_unit_price_usd: '', uom: '' })

const refresh = () => comps.fetchAll({
  category_id: filter.value.category_id || undefined,
  q: filter.value.q || undefined
})

const create = async () => {
  if (!form.value.category_id || !form.value.name.trim()) return
  await comps.create({
    category_id: form.value.category_id,
    name: form.value.name.trim(),
    default_unit_price_usd: form.value.default_unit_price_usd === '' ? undefined : Number(form.value.default_unit_price_usd),
    uom: form.value.uom || undefined
  })
  form.value = { category_id: form.value.category_id, name: '', default_unit_price_usd: '', uom: '' }
}

onMounted(async () => {
  if (!cats.items.length) await cats.fetchAll()
  await refresh()
})
watch(filter, refresh, { deep: true })
</script>

<template>
  <div class="p-6 space-y-6">
    <h1 class="text-2xl font-semibold">Components</h1>

    <div class="grid md:grid-cols-3 gap-3">
      <select v-model.number="filter.category_id" class="border rounded p-2">
        <option :value="null">All categories</option>
        <option v-for="c in cats.items" :key="c.id" :value="c.id">{{ c.name }}</option>
      </select>
      <input v-model="filter.q" placeholder="Search name…" class="border rounded p-2">
      <div></div>
    </div>

    <form @submit.prevent="create" class="grid md:grid-cols-4 gap-3 items-end">
      <select v-model.number="form.category_id" class="border rounded p-2" required>
        <option :value="null" disabled>Select category…</option>
        <option v-for="c in cats.items" :key="c.id" :value="c.id">{{ c.name }}</option>
      </select>
      <input v-model="form.name" placeholder="Name *" class="border rounded p-2" required>
      <input v-model="form.default_unit_price_usd" type="number" step="0.01" placeholder="Default price (USD)" class="border rounded p-2">
      <div class="flex gap-2">
        <input v-model="form.uom" placeholder="UoM (e.g. hr, pc)" class="border rounded p-2 w-full">
        <button class="bg-black text-white rounded px-3">Add</button>
      </div>
    </form>

    <div v-if="comps.loading">Loading…</div>
    <p v-if="comps.error" class="text-red-600 text-sm">{{ comps.error }}</p>

    <ul class="divide-y border rounded">
      <li v-for="x in comps.items" :key="x.id" class="p-3 flex items-center justify-between">
        <div>
          <div class="font-medium">{{ x.name }} <span class="text-gray-500">({{ x.uom || '—' }})</span></div>
          <div class="text-sm text-gray-600">Category #{{ x.category_id }} · Default: {{ x.default_unit_price_usd ?? '—' }}</div>
        </div>
        <button class="text-red-600 text-sm" @click="comps.remove(x.id)">Delete</button>
      </li>
    </ul>
  </div>
</template>
