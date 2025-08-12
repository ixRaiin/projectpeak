<script setup>
import { ref, onMounted, watch } from 'vue'
import { useCatalog } from '@/stores/catalog'

const catalog = useCatalog()

// Category form
const catName = ref('')
const catDesc = ref('')
const catSearch = ref('')

// Component form
const selectedCatId = ref(null)
const compName = ref('')
const compPrice = ref('')
const compUom = ref('')
const compSearch = ref('')

const createCategory = async () => {
  if (!catName.value.trim()) return
  await catalog.createCategory({ name: catName.value, description: catDesc.value || null })
  catName.value = ''; catDesc.value = ''
}

const createComponent = async () => {
  if (!selectedCatId.value || !compName.value.trim()) return
  await catalog.createComponent({
    category_id: selectedCatId.value,
    name: compName.value,
    default_unit_price_usd: compPrice.value === '' ? undefined : Number(compPrice.value),
    uom: compUom.value || null
  })
  compName.value=''; compPrice.value=''; compUom.value=''
  await catalog.fetchComponents({ category_id: selectedCatId.value })
}

const doSearchCats = () => catalog.fetchCategories({ q: catSearch.value })
const doSearchComps = () => catalog.fetchComponents({ category_id: selectedCatId.value, q: compSearch.value })

watch(selectedCatId, async (id) => {
  if (id) await catalog.fetchComponents({ category_id: id })
  else catalog.components = []
})

onMounted(() => catalog.fetchCategories())
</script>

<template>
  <div class="p-6 space-y-8">
    <h1 class="text-2xl font-semibold">Catalog</h1>

    <div class="grid md:grid-cols-2 gap-6">
      <!-- Categories -->
      <div class="space-y-4">
        <div class="flex items-center gap-3">
          <h2 class="font-semibold">Categories</h2>
          <input v-model="catSearch" @keyup.enter="doSearchCats" placeholder="Search…" class="border rounded px-3 py-1" />
          <button class="rounded bg-black text-white px-3 py-1" @click="doSearchCats">Search</button>
        </div>

        <form @submit.prevent="createCategory" class="space-y-2 border rounded p-4">
          <div class="font-medium">Create category</div>
          <input v-model="catName" placeholder="Name *" class="w-full border rounded p-2" required />
          <input v-model="catDesc" placeholder="Description" class="w-full border rounded p-2" />
          <button class="rounded bg-black text-white px-3 py-2">Add</button>
        </form>

        <ul class="divide-y border rounded">
          <li v-for="c in catalog.categories" :key="c.id" class="p-3 flex items-center justify-between gap-3">
            <div>
              <div class="font-medium">{{ c.name }}</div>
              <div v-if="c.description" class="text-sm text-gray-600">{{ c.description }}</div>
            </div>
            <div class="flex gap-2">
              <button class="text-red-600 text-sm" @click="catalog.deleteCategory(c.id)">Delete</button>
              <button class="text-sm underline" @click="selectedCatId = c.id">Select</button>
            </div>
          </li>
          <li v-if="!catalog.categories.length" class="p-3 text-sm text-gray-500">No categories yet.</li>
        </ul>
      </div>

      <!-- Components -->
      <div class="space-y-4">
        <div class="flex items-center gap-3">
          <h2 class="font-semibold">Components</h2>
          <select v-model.number="selectedCatId" class="border rounded px-3 py-1">
            <option :value="null" disabled>Select category…</option>
            <option v-for="c in catalog.categories" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>
          <input v-model="compSearch" @keyup.enter="doSearchComps" placeholder="Search…" class="border rounded px-3 py-1" />
          <button class="rounded bg-black text-white px-3 py-1" @click="doSearchComps" :disabled="!selectedCatId">Search</button>
        </div>

        <form @submit.prevent="createComponent" class="space-y-2 border rounded p-4">
          <div class="font-medium">Create component</div>
          <input v-model="compName" placeholder="Name *" class="w-full border rounded p-2" required />
          <div class="grid grid-cols-2 gap-3">
            <input v-model="compPrice" type="number" step="0.0001" placeholder="Default price (USD)" class="w-full border rounded p-2" />
            <input v-model="compUom" placeholder="Unit (e.g. meter, piece)" class="w-full border rounded p-2" />
          </div>
          <button class="rounded bg-black text-white px-3 py-2" :disabled="!selectedCatId">Add</button>
          <p v-if="!selectedCatId" class="text-sm text-gray-500">Select a category first.</p>
        </form>

        <ul class="divide-y border rounded">
          <li v-for="x in catalog.components" :key="x.id" class="p-3 flex items-center justify-between gap-3">
            <div>
              <div class="font-medium">{{ x.name }}</div>
              <div class="text-sm text-gray-600">
                <span v-if="x.uom">{{ x.uom }}</span>
                <span v-if="x.default_unit_price_usd"> · ${{ x.default_unit_price_usd }}</span>
              </div>
            </div>
            <button class="text-red-600 text-sm" @click="catalog.deleteComponent(x.id)">Delete</button>
          </li>
          <li v-if="selectedCatId && !catalog.components.length" class="p-3 text-sm text-gray-500">No components for this category.</li>
        </ul>
      </div>
    </div>
  </div>
</template>
