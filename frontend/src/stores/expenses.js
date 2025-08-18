// src/stores/expenses.js
import { defineStore } from 'pinia'
import api from '@/lib/api'

export const useExpensesStore = defineStore('expenses', {
  state: () => ({
    byProject: {},                        // { [pid]: Expense[] }
    loading: { expenses: false },
    errors: {
      expenses: null,                     // fetch list errors
      mutateById: {},                     // { [eid]: string|null } header errors
      lineByKey: {},                      // { [`${eid}:${lid||'new'}`]: string|null } line errors
    },
  }),

  actions: {
    // ---- READ ----
    async fetchExpenses(pid) {
      this.loading.expenses = true
      this.errors.expenses = null
      try {
        const res = await api.get(`/projects/${pid}/expenses`)
        let list = Array.isArray(res?.expenses) ? res.expenses : []
        list = list.slice().sort((a, b) => String(b.expense_date).localeCompare(String(a.expense_date)))
        this.byProject[pid] = list
        return list
      } catch (e) {
        this.errors.expenses = e?.message || 'Failed to load expenses'
        this.byProject[pid] = this.byProject[pid] || []
        return this.byProject[pid]
      } finally {
        this.loading.expenses = false
      }
    },

    // ---- Header mutations (Step 5) ----
    async createExpense(pid, payload) {
      try {
        const created = await api.post(`/projects/${pid}/expenses`, payload)
        if (!this.byProject[pid]) this.byProject[pid] = []
        this.byProject[pid].unshift(created)
        this.byProject[pid].sort((a, b) => String(b.expense_date).localeCompare(String(a.expense_date)))
        return created
      } catch (e) {
        this.errors.mutateById['new'] = e?.message || 'Failed to create expense'
        throw e
      }
    },

    async patchExpense(pid, eid, patch) {
      const list = this.byProject[pid] || []
      const idx = list.findIndex(e => e.id === eid)
      const prev = idx !== -1 ? { ...list[idx] } : null
      if (idx !== -1) list[idx] = { ...list[idx], ...patch }

      try {
        const updated = await api.patch(`/projects/${pid}/expenses/${eid}`, patch)
        if (idx !== -1) list[idx] = updated
        this.byProject[pid] = list.slice().sort((a, b) => String(b.expense_date).localeCompare(String(a.expense_date)))
        this.errors.mutateById[eid] = null
        return updated
      } catch (e) {
        if (idx !== -1 && prev) list[idx] = prev
        this.errors.mutateById[eid] = e?.message || 'Failed to update expense'
        throw e
      }
    },

    // ---- Lines (Step 6) ----
    async addLine(pid, eid, payload) {
      // payload: { category_id, qty|quantity, unit_price_usd }
      const key = `${eid}:new`
      this.errors.lineByKey[key] = null
      try {
        await api.post(`/projects/${pid}/expenses/${eid}/lines`, payload)
        // Always refetch to stay in sync and get server-calculated totals if any
        await this.fetchExpenses(pid)
        return true
      } catch (e) {
        this.errors.lineByKey[key] = e?.message || 'Failed to add line'
        throw e
      }
    },

    async patchLine(pid, eid, lid, patch) {
      const key = `${eid}:${lid}`
      this.errors.lineByKey[key] = null
      try {
        await api.patch(`/projects/${pid}/expenses/${eid}/lines/${lid}`, patch)
        await this.fetchExpenses(pid)
        return true
      } catch (e) {
        this.errors.lineByKey[key] = e?.message || 'Failed to update line'
        throw e
      }
    },

    async deleteLine(pid, eid, lid) {
      const key = `${eid}:${lid}`
      this.errors.lineByKey[key] = null
      try {
        await api.delete(`/projects/${pid}/expenses/${eid}/lines/${lid}`)
        await this.fetchExpenses(pid)
        return true
      } catch (e) {
        this.errors.lineByKey[key] = e?.message || 'Failed to delete line'
        throw e
      }
    },
  },
})
