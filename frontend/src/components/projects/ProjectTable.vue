<template>
  <div class="border rounded overflow-hidden">
    <table class="w-full text-sm">
      <thead class="bg-gray-50 text-left">
      <tr>
      <th class="px-3 py-2">Project</th>
      <th class="px-3 py-2">Client</th>
      <th class="px-3 py-2">Status</th>
      <th class="px-3 py-2">Progress</th>
      <th class="px-3 py-2">Dates</th>
      <th class="px-3 py-2 text-right">Actions</th>
      </tr>
      </thead>
      <tbody>
        <tr v-for="p in items" :key="p.id" class="border-t">
          <td class="px-3 py-2">
          <div class="font-medium truncate">{{ p.code ? p.code + ' — ' : '' }}{{ p.name }}</div>
          </td>
          <td class="px-3 py-2 text-gray-600">{{ clientName(p.client_id) }}</td>
          <td class="px-3 py-2">
            <span :class="badgeClass(p.status)">{{ (p.status || 'planned') }}</span>
          </td>
          <td class="px-3 py-2">
            <div class="h-2 bg-gray-100 rounded">
              <div class="h-2 rounded bg-black" :style="{ width: (p.progress_percent ?? 0) + '%' }"></div>
            </div>
          </td>
          <td class="px-3 py-2 text-gray-600">
            <span v-if="p.start_date">{{ p.start_date }}</span>
            <span v-if="p.end_date"> → {{ p.end_date }}</span>
          </td>
          <td class="px-3 py-2">
            <div class="flex justify-end gap-2">
              <button class="underline" @click="$emit('edit', p)">Edit</button>
              <button class="underline" @click="$emit('tasks', p)">Board</button>
              <button class="underline" @click="$emit('expenses', p)">Expenses</button>
              <button class="text-red-600 underline" @click="$emit('delete', p)">Delete</button>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
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
