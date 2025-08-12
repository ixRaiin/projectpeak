import { defineStore } from 'pinia'
import { api } from '@/lib/api'

export const useClients = defineStore('clients', {
  state: () => ({ items: [], loading: false, error: null }),
  actions: {
    async fetchAll(q = '') {
      this.loading = true; this.error = null
      try {
        const res = await api(`/clients${q ? `?q=${encodeURIComponent(q)}` : ''}`)
        this.items = res.clients ?? []
      } catch (e) { this.error = e.message }
      finally { this.loading = false }
    },
    async create(payload) {
      const created = await api('/clients', { method: 'POST', body: payload })
      this.items.unshift(created)
      return created
    },
    async update(id, patch) {
      const updated = await api(`/clients/${id}`, { method: 'PATCH', body: patch })
      const idx = this.items.findIndex(x => x.id === id)
      if (idx !== -1) this.items[idx] = updated
      return updated
    },
    async remove(id) {
      await api(`/clients/${id}`, { method: 'DELETE' })
      this.items = this.items.filter(x => x.id !== id)
    }
  }
})
