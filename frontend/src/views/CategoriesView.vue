<script setup>
import { ref, onMounted } from 'vue'
import { useCategories } from '@/stores/categories'

const cats = useCategories()
const form = ref({ name: '', description: '' })
const editingId = ref(null)
const editBuf = ref({ name: '', description: '' })

const create = async () => {
  if (!form.value.name.trim()) return
  await cats.create({ name: form.value.name.trim(), description: form.value.description || undefined })
  form.value = { name: '', description: '' }
}

const startEdit = (row) => {
  editingId.value = row.id
  editBuf.value = { name: row.name, description: row.description ?? '' }
}
const saveEdit = async (id) => {
  await cats.update(id, {
    name: editBuf.value.name.trim(),
    description: editBuf.value.description || null
  })
  editingId.value = null
}
const cancelEdit = () => { editingId.value = null }

onMounted(() => cats.fetchAll())
</script>

<template>
  <div class="p-6 space-y-6">
    <h1 class="text-2xl font-semibold">Categories</h1>

    <form @submit.prevent="create" class="grid md:grid-cols-3 gap-3 items-end">
      <input v-model="form.name" placeholder="Name *" class="border rounded p-2">
      <input v-model="form.description" placeholder="Description (optional)" class="border rounded p-2">
      <button class="bg-black text-white rounded px-3 py-2">Add</button>
    </form>

    <div v-if="cats.loading">Loading…</div>
    <p v-if="cats.error" class="text-red-600 text-sm">{{ cats.error }}</p>

    <table class="w-full border rounded overflow-hidden">
      <thead class="bg-gray-50 text-left">
        <tr><th class="p-2">Name</th><th class="p-2">Description</th><th class="p-2 w-40">Actions</th></tr>
      </thead>
      <tbody>
        <tr v-for="c in cats.items" :key="c.id" class="border-t">
          <td class="p-2">
            <template v-if="editingId === c.id">
              <input v-model="editBuf.name" class="border rounded p-1 w-full">
            </template>
            <template v-else>{{ c.name }}</template>
          </td>
          <td class="p-2">
            <template v-if="editingId === c.id">
              <input v-model="editBuf.description" class="border rounded p-1 w-full">
            </template>
            <template v-else>{{ c.description ?? '—' }}</template>
          </td>
          <td class="p-2 flex gap-2">
            <button v-if="editingId !== c.id" class="text-sm underline" @click="startEdit(c)">Edit</button>
            <template v-else>
              <button class="text-sm underline" @click="saveEdit(c.id)">Save</button>
              <button class="text-sm underline text-gray-500" @click="cancelEdit">Cancel</button>
            </template>
            <button class="text-sm text-red-600 underline" @click="cats.remove(c.id)">Delete</button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
