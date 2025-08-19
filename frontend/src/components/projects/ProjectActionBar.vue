<template>
<div class="flex flex-col md:flex-row md:items-center gap-3">
<div class="flex items-center gap-2">
<button
class="px-3 py-2 rounded bg-black text-white focus:outline-none focus:ring-2 focus:ring-black/40"
@click="$emit('create')"
type="button"
>Add Project</button>


<div class="relative">
<input
v-model="q"
@input="debouncedSearch"
placeholder="Search projects…"
class="border rounded px-3 py-2 min-w-[220px]"
aria-label="Search projects"
/>
</div>
</div>


<div class="flex items-center gap-2">
<select v-model="status" @change="$emit('filter', status)" class="border rounded px-2 py-2">
<option value="all">All statuses</option>
<option value="planned">Planned</option>
<option value="active">Active</option>
<option value="completed">Completed</option>
</select>


<select v-model="sort" @change="$emit('sort', sort)" class="border rounded px-2 py-2">
<option value="updated_desc">Updated (newest)</option>
<option value="updated_asc">Updated (oldest)</option>
<option value="name_asc">Name (A→Z)</option>
<option value="name_desc">Name (Z→A)</option>
</select>


<div class="ml-auto flex items-center gap-1 rounded border p-1">
<button
class="px-3 py-1.5 rounded hover:bg-gray-100"
:class="{ 'bg-black text-white hover:bg-black': view==='table' }"
@click="$emit('toggle', 'table')"
type="button"
aria-pressed="view==='table'"
>Table</button>
<button
class="px-3 py-1.5 rounded hover:bg-gray-100"
:class="{ 'bg-black text-white hover:bg-black': view==='grid' }"
@click="$emit('toggle', 'grid')"
type="button"
aria-pressed="view==='grid'"
>Grid</button>
</div>
</div>
</div>
</template>


<script setup>
import { ref, watch } from 'vue'


const props = defineProps({
qProp: { type: String, default: '' },
statusProp: { type: String, default: 'all' },
sortProp: { type: String, default: 'updated_desc' },
initialView: { type: String, default: 'table' },
})


const emit = defineEmits(['create', 'search', 'filter', 'sort', 'toggle'])


const q = ref(props.qProp)
</script>
