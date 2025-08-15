import { defineStore } from 'pinia'
import { api } from '@/lib/api'

export const useExpenses = defineStore('expenses', {
  state: () => ({
    items: [],
    loading: false,
    error: null,
  }),
  actions: {
    async fetchForProject(pid) {
      this.loading = true; this.error = null
      try {
        const res = await api().get(`/projects/${pid}/expenses`)
        this.items = res.expenses || []
      } catch (e) {
        this.error = e?.error || 'Failed to load expenses'
      } finally {
        this.loading = false
      }
    },
    async create(pid, payload) {
      this.error = null
      try {
        await api().post(`/projects/${pid}/expenses`, payload)
        await this.fetchForProject(pid)
      } catch (e) {
        this.error = e?.error || 'Failed to create expense'
        throw e
      }
    },
  },
})
