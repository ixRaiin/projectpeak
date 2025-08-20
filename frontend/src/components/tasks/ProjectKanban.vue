<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useTasksStore } from '@/stores/tasks'

const props = defineProps({
  projectId: { type: [Number, String], required: true },
})
const emit = defineEmits(['progress'])

const pid = Number(props.projectId)
const tasks = useTasksStore()

/* ----- Top toolbar ----- */
const newTitle = ref('')

/* ----- Columns (grouped by status) ----- */
const cols = computed(() => tasks.grouped(pid)) // { todo, doing, done }

/* ----- Drawer state ----- */
const drawer = reactive({ open: false, taskId: null })
const activeTask = computed(() => (tasks.byProject[pid] || []).find(t => t.id === drawer.taskId))
const edit = reactive({ title: '', due_date: '', status: 'todo' })
const comments = computed(() => tasks.commentsByTask[activeTask?.value?.id] || [])
const newComment = ref('')

/* ----- Actions ----- */
async function createTask() {
  const title = newTitle.value.trim()
  if (!title) return
  await tasks.createTask(pid, { title, status: 'todo' })
  newTitle.value = ''
  emit('progress', tasks.progressByProject[pid])
}

async function onEdit(task, patch) {
  await tasks.updateTask(pid, task.id, patch)
  emit('progress', tasks.progressByProject[pid])
}

async function onDelete(task) {
  if (confirm(`Delete task "${task.title}"?`)) {
    await tasks.deleteTask(pid, task.id)
    emit('progress', tasks.progressByProject[pid])
    if (drawer.taskId === task.id) closeDetails()
  }
}

/* ----- Drag & Drop (HTML5) ----- */
function dragStart(e, t) {
  e.dataTransfer.setData('text/plain', String(t.id))
}
function allowDrop(e) { e.preventDefault() }
async function dropTo(status, e) {
  e.preventDefault()
  const id = Number(e.dataTransfer.getData('text/plain'))
  if (!id) return
  await tasks.moveTask(pid, id, status, null) // append to end of target column
  emit('progress', tasks.progressByProject[pid])
}

/* ----- Drawer handlers ----- */
function openDetails(task) {
  drawer.open = true
  drawer.taskId = task.id
  edit.title = task.title || ''
  edit.due_date = task.due_date || ''
  edit.status = task.status || 'todo'
  tasks.fetchComments(pid, task.id).catch(()=>{})
}
function closeDetails() { drawer.open = false; drawer.taskId = null }
async function saveEdit() {
  if (!activeTask.value) return
  await tasks.updateTask(pid, activeTask.value.id, {
    title: edit.title,
    due_date: edit.due_date || null,
    status: edit.status,
  })
  emit('progress', tasks.progressByProject[pid])
}
async function applyStatus() {
  if (!activeTask.value) return
  await tasks.updateTask(pid, activeTask.value.id, { status: edit.status })
  emit('progress', tasks.progressByProject[pid])
}

/* ----- Comments ----- */
async function addComment() {
  const txt = newComment.value.trim()
  if (!activeTask.value || !txt) return
  await tasks.addComment(pid, activeTask.value.id, { body: txt })
  newComment.value = ''
}
async function deleteComment(c) {
  if (!activeTask.value) return
  await tasks.deleteComment(pid, activeTask.value.id, c.id)
}

/* ----- Boot ----- */
onMounted(async () => {
  await tasks.refresh(pid) // fetch tasks + progress
  emit('progress', tasks.progressByProject[pid])
})
</script>

<template>
  <div class="space-y-4">
    <!-- Toolbar -->
    <div class="flex items-center justify-between">
      <h2 class="font-semibold">Tasks</h2>
      <div class="flex items-center gap-2">
        <input
          v-model="newTitle"
          @keyup.enter="createTask"
          placeholder="New task title…"
          class="border rounded px-3 py-2 min-w-[240px]"
        />
        <button class="px-3 py-2 rounded bg-black text-white" @click="createTask" :disabled="!newTitle.trim()">
          Add
        </button>
      </div>
    </div>

    <!-- Board -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <!-- To‑Do -->
      <section class="border rounded p-3 bg-gray-50/60 min-h-[240px]" @dragover="allowDrop" @drop="dropTo('todo', $event)">
        <div class="flex items-center justify-between mb-2">
          <h3 class="font-semibold">To‑Do</h3>
          <span class="text-xs text-gray-500">{{ cols.todo.length }}</span>
        </div>
        <div class="space-y-2">
          <article
            v-for="t in cols.todo"
            :key="t.id"
            class="bg-white border rounded p-3 shadow-sm cursor-move"
            draggable="true"
            @dragstart="dragStart($event, t)"
          >
            <div class="flex items-start justify-between gap-2">
              <button class="text-left font-medium truncate" @click="openDetails(t)">{{ t.title }}</button>
              <div class="flex items-center gap-2">
                <input
                  type="date"
                  class="border rounded px-1 py-0.5 text-xs"
                  v-model="t.due_date"
                  @change="onEdit(t, { due_date: t.due_date })"
                />
                <button class="text-xs text-red-600" @click="onDelete(t)">Delete</button>
              </div>
            </div>
          </article>
          <p v-if="!cols.todo.length" class="text-sm text-gray-500">No tasks.</p>
        </div>
      </section>

      <!-- In‑Progress -->
      <section class="border rounded p-3 bg-gray-50/60 min-h-[240px]" @dragover="allowDrop" @drop="dropTo('doing', $event)">
        <div class="flex items-center justify-between mb-2">
          <h3 class="font-semibold">In‑Progress</h3>
        </div>
        <div class="space-y-2">
          <article
            v-for="t in cols.doing"
            :key="t.id"
            class="bg-white border rounded p-3 shadow-sm cursor-move"
            draggable="true"
            @dragstart="dragStart($event, t)"
          >
            <div class="flex items-start justify-between gap-2">
              <button class="text-left font-medium truncate" @click="openDetails(t)">{{ t.title }}</button>
              <div class="flex items-center gap-2">
                <input
                  type="date"
                  class="border rounded px-1 py-0.5 text-xs"
                  v-model="t.due_date"
                  @change="onEdit(t, { due_date: t.due_date })"
                />
                <button class="text-xs text-red-600" @click="onDelete(t)">Delete</button>
              </div>
            </div>
          </article>
          <p v-if="!cols.doing.length" class="text-sm text-gray-500">No tasks.</p>
        </div>
      </section>

      <!-- Completed -->
      <section class="border rounded p-3 bg-gray-50/60 min-h-[240px]" @dragover="allowDrop" @drop="dropTo('done', $event)">
        <div class="flex items-center justify-between mb-2">
          <h3 class="font-semibold">Completed</h3>
        </div>
        <div class="space-y-2">
          <article
            v-for="t in cols.done"
            :key="t.id"
            class="bg-white border rounded p-3 shadow-sm cursor-move"
            draggable="true"
            @dragstart="dragStart($event, t)"
          >
            <div class="flex items-start justify-between gap-2">
              <button class="text-left font-medium truncate" @click="openDetails(t)">{{ t.title }}</button>
              <div class="flex items-center gap-2">
                <input
                  type="date"
                  class="border rounded px-1 py-0.5 text-xs"
                  v-model="t.due_date"
                  @change="onEdit(t, { due_date: t.due_date })"
                />
                <button class="text-xs text-red-600" @click="onDelete(t)">Delete</button>
              </div>
            </div>
          </article>
          <p v-if="!cols.done.length" class="text-sm text-gray-500">No tasks.</p>
        </div>
      </section>
    </div>

    <!-- Drawer -->
    <div v-if="drawer.open" class="fixed inset-y-0 right-0 w-full md:w-[440px] bg-white shadow-2xl p-5 z-40 overflow-y-auto">
      <div class="flex items-start justify-between mb-4">
        <div>
          <h3 class="text-lg font-semibold">{{ activeTask?.title || 'Task' }}</h3>
          <p class="text-xs text-gray-500">
            Status:
            <select v-model="edit.status" class="border rounded px-2 py-1 text-xs" @change="applyStatus">
              <option value="todo">To‑Do</option>
              <option value="doing">In‑Progress</option>
              <option value="done">Completed</option>
            </select>
          </p>
        </div>
        <button class="text-sm underline" @click="closeDetails">Close</button>
      </div>

      <div class="space-y-3">
        <label class="block">
          <span class="text-sm text-gray-600">Title</span>
          <input v-model="edit.title" class="w-full border rounded p-2" @blur="saveEdit" />
        </label>
        <label class="block">
          <span class="text-sm text-gray-600">Due date</span>
          <input type="date" v-model="edit.due_date" class="w-full border rounded p-2" @change="saveEdit" />
        </label>
        <div class="flex items-center gap-2">
          <button class="px-3 py-2 rounded border" @click="saveEdit">Save</button>
          <button class="px-3 py-2 rounded border text-red-600" @click="onDelete(activeTask)">Delete</button>
        </div>

        <hr class="my-4" />

        <section>
          <h4 class="font-semibold mb-2">Comments</h4>
          <div v-if="tasks.loading.comments[activeTask?.id]" class="text-sm text-gray-500">Loading comments…</div>
          <ul class="space-y-2">
            <li v-for="c in comments" :key="c.id" class="border rounded p-2 text-sm">
              <div class="flex items-center justify-between">
                <span class="font-medium">{{ c.author_name || 'User' }}</span>
                <button class="text-xs text-red-600" @click="deleteComment(c)">Delete</button>
              </div>
              <p class="text-gray-700 whitespace-pre-wrap">{{ c.text ?? c.body }}</p>
            </li>
            <li v-if="!comments.length" class="text-sm text-gray-500">No comments yet.</li>
          </ul>
          <form @submit.prevent="addComment" class="mt-2 flex gap-2">
            <input v-model="newComment" placeholder="Write a comment…" class="flex-1 border rounded px-3 py-2" />
            <button class="px-3 py-2 rounded bg-black text-white" :disabled="!newComment.trim()">Add</button>
          </form>
        </section>
      </div>
    </div>
  </div>
</template>
