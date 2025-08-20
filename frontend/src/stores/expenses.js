// src/stores/expenses.js
import { defineStore } from 'pinia'
import api from '@/lib/api'

// --- helpers (internal only) ---
function asArray(x) {
  if (Array.isArray(x)) return x
  if (x && Array.isArray(x.expenses)) return x.expenses
  if (x && Array.isArray(x.items)) return x.items
  if (x && Array.isArray(x.rows)) return x.rows
  if (x && Array.isArray(x.data)) return x.data
  return []
}
const sortByDateDesc = (a, b) =>
  String(b?.expense_date || '').localeCompare(String(a?.expense_date || ''))

function normalizeLine(input = {}) {
  const qRaw = input.quantity != null ? input.quantity : (input.qty != null ? input.qty : 1)
  const qty = Number.isFinite(Number(qRaw)) ? Number(qRaw) : 1

  const upRaw =
    input.unit_price_usd != null && input.unit_price_usd !== ''
      ? input.unit_price_usd
      : (input.component_unit_price != null ? input.component_unit_price : 0)
  const unit_price_usd = Number.isFinite(Number(upRaw)) ? Number(upRaw) : 0

  const out = {
    category_id: Number(input.category_id),
    component_id: input.component_id != null ? Number(input.component_id) : undefined,
    qty,
    quantity: qty,
    unit_price_usd,
  }
  if (out.component_id === undefined) delete out.component_id
  return out
}

function normalizeLineFromServer(input = {}) {
  // quantity can be `quantity` or `qty`
  const qRaw = input.quantity != null ? input.quantity : input.qty
  const quantity = Number(qRaw)
  const safeQty = Number.isFinite(quantity) ? quantity : 1

  // unit price can be `unit_price_usd` or `component_unit_price` (and a few aliases)
  const upRaw =
    input.unit_price_usd != null ? input.unit_price_usd
    : (input.component_unit_price != null ? input.component_unit_price
    : (input.unit_price != null ? input.unit_price
    : (input.price_usd != null ? input.price_usd
    : input.price)))

  const unit_price_usd = Number.isFinite(Number(upRaw)) ? Number(upRaw) : 0

  // prefer server-provided line total if present, else compute
  const preTotal =
    input.line_total_usd ?? input.total_usd ?? input.total ?? null
  const line_total_usd = Number.isFinite(Number(preTotal))
    ? Number(preTotal)
    : safeQty * unit_price_usd

  const out = {
    id: input.id, // keep id if you have it
    category_id: Number(input.category_id),
    component_id: input.component_id != null ? Number(input.component_id) : undefined,
    quantity: safeQty,
    unit_price_usd,
    line_total_usd,
  }
  if (out.component_id === undefined) delete out.component_id
  return out
}


export const useExpensesStore = defineStore('expenses', {
  state: () => ({
    byProject: {},
    loading: { expenses: false },
    errors: {
      expenses: null,
      mutateById: {},
      lineByKey: {},
    },
  }),

  actions: {
    // ---- READ ----
    async fetchExpenses(pid) {
      this.loading.expenses = true
      this.errors.expenses = null
      try {
        const res = await api.get(`/projects/${pid}/expenses`)
        const list = asArray(res).slice().sort(sortByDateDesc)

        // ⬇️ normalize lines from server so the UI always has `quantity`
        const normalized = list.map(e => ({
          ...e,
          lines: Array.isArray(e.lines) ? e.lines.map(normalizeLineFromServer) : [],
        }))

        this.byProject[pid] = normalized
        return normalized
      } catch (e) {
        this.errors.expenses = e?.message || 'Failed to load expenses'
        this.byProject[pid] = this.byProject[pid] || []
        return this.byProject[pid]
      } finally {
        this.loading.expenses = false
      }
    },

    // ---- Header mutations ----
    async createExpense(pid, payload) {
      try {
        const body = { ...payload }

        // Normalize optional lines if caller sent them in the header create
        if (Array.isArray(body.lines)) {
          body.lines = body.lines.map(normalizeLine)
        }

        // Ensure expense_date is a string (YYYY-MM-DD) if provided
        if (body.expense_date instanceof Date) {
          const d = body.expense_date
          body.expense_date = d.toISOString().slice(0, 10)
        }

        const created = await api.post(`/projects/${pid}/expenses`, body)
        if (!this.byProject[pid]) this.byProject[pid] = []
        this.byProject[pid].unshift(created)
        this.byProject[pid].sort(sortByDateDesc)
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
        const normalized = { ...patch }
        if (normalized.expense_date instanceof Date) {
          const d = normalized.expense_date
          normalized.expense_date = d.toISOString().slice(0, 10)
        }

        const updated = await api.patch(`/projects/${pid}/expenses/${eid}`, normalized)
        if (idx !== -1) list[idx] = updated
        this.byProject[pid] = list.slice().sort(sortByDateDesc)
        this.errors.mutateById[eid] = null
        return updated
      } catch (e) {
        if (idx !== -1 && prev) list[idx] = prev
        this.errors.mutateById[eid] = e?.message || 'Failed to update expense'
        throw e
      }
    },

    // ---- Lines ----
    async addLine(pid, eid, payload) {
      // payload: { category_id, component_id, qty|quantity, unit_price_usd, component_unit_price? }
      const key = `${eid}:new`
      this.errors.lineByKey[key] = null
      try {
        const body = normalizeLine(payload)
        await api.post(`/projects/${pid}/expenses/${eid}/lines`, body)
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
        const body = normalizeLine({ ...patch, quantity: patch.quantity ?? patch.qty })
        await api.patch(`/projects/${pid}/expenses/${eid}/lines/${lid}`, body)
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
