<template>
<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
<article v-for="p in items" :key="p.id" class="border rounded p-4 space-y-2">
<div class="flex items-start justify-between gap-2">
<h3 class="font-semibold truncate" :title="p.name">{{ p.code ? p.code + ' — ' : '' }}{{ p.name }}</h3>
<span :class="badgeClass(p.status)">{{ (p.status || 'planned') }}</span>
</div>
<p class="text-sm text-gray-600 truncate">Client: {{ clientName(p.client_id) }}</p>
<div class="h-2 bg-gray-100 rounded">
<div class="h-2 rounded bg-black" :style="{ width: (p.progress_percent ?? 0) + '%' }"></div>
</div>
<div class="text-xs text-gray-500">
<span v-if="p.start_date">{{ p.start_date }}</span>
<span v-if="p.end_date"> → {{ p.end_date }}</span>
</div>
<div class="flex flex-wrap gap-2 pt-1">
<button class="underline" @click="$emit('view', p)">View</button>
<button class="underline" @click="$emit('open-board', p)">Open Board</button>
<button class="underline" @click="$emit('add-expense', p)">Add Expense</button>
<button class="text-red-600 underline" @click="$emit('delete', p)">Delete</button>
</div>
</article>
</div>
</template>


<script setup>
const props = defineProps({
items: { type: Array, default: () => [] },
clientName: { type: Function, required: true },
})


const badgeClass = (status) => {
const s = (status || 'planned').toLowerCase()
const base = 'inline-flex items-center px-2 py-0.5 rounded text-xs'
if (s === 'completed' || s === 'complete') return base + ' bg-green-100 text-green-800'
if (s === 'active') return base + ' bg-blue-100 text-blue-800'
return base + ' bg-gray-100 text-gray-800'
}
</script>
