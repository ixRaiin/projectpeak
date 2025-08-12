import { defineStore } from 'pinia'
import { api } from '@/lib/api'

export const useExpenses = defineStore('expenses', {
  state: () => ({ items: [], loading: false, error: '' }),
  actions: {
    async fetchByProject(pid) {
      this.loading = true; this.error = ''
      try {
        const { expenses } = await api.get(`/projects/${pid}/expenses`)
        this.items = expenses
      } catch (e) { this.error = e.message }
      finally { this.loading = false }
    },
    async create(pid, payload) {
      const e = await api.post(`/projects/${pid}/expenses`, payload)
      this.items.unshift(e)
      return e
    },
    async remove(id) {
      await api.delete(`/expenses/${id}`)
      this.items = this.items.filter(x => x.id !== id)
    }
  }
})
