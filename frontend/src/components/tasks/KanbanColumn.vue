<script setup>
const props = defineProps({
  title: { type: String, required: true },
  status: { type: String, required: true }, // 'todo' | 'doing' | 'done'
  tasks: { type: Array, default: () => [] },
})
const emit = defineEmits(['drop-task','edit','delete','open'])

function dragStart(e, t) {
  e.dataTransfer.setData('text/plain', String(t.id))
}
function allowDrop(e) { e.preventDefault() }
function drop(e) {
  e.preventDefault()
  const id = Number(e.dataTransfer.getData('text/plain'))
  emit('drop-task', { id, status: props.status })
}
</script>

<template>
  <section
    class="border rounded p-3 bg-gray-50/60 min-h-[240px]"
    @dragover="allowDrop"
    @drop="drop"
  >
    <div class="flex items-center justify-between mb-2">
      <h3 class="font-semibold">{{ title }}</h3>
      <span class="text-xs text-gray-500">{{ tasks?.length || 0 }}</span>
    </div>

    <div class="space-y-2">
      <article
        v-for="t in (tasks || [])"
        :key="t.id"
        class="bg-white border rounded p-3 shadow-sm cursor-move"
        draggable="true"
        @dragstart="dragStart($event, t)"
      >
        <div class="flex items-start justify-between gap-2">
          <button class="text-left font-medium truncate" @click="$emit('open', t)">
            {{ t.title }}
          </button>
          <div class="flex items-center gap-2">
            <input
              type="date"
              class="border rounded px-1 py-0.5 text-xs"
              v-model="t.due_date"
              @change="$emit('edit', t, { due_date: t.due_date })"
            />
            <button class="text-xs text-red-600" @click="$emit('delete', t)">Delete</button>
          </div>
        </div>
      </article>

      <p v-if="!(tasks && tasks.length)" class="text-sm text-gray-500">No tasks.</p>
    </div>
  </section>
</template>
