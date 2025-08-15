import { defineStore } from 'pinia'
import { api } from '@/lib/api'

export const useProjects = defineStore('projects', {
  state: () => ({
    items: [],
    loading: false,
    error: null,
    detail: {
      projectId: null,
      cats: [],
      bom: [],
      summary: null,
      loadingCats: false,
      loadingBom: false,
      loadingSummary: false,
    }
  }),
  actions: {
    async fetchAll({ q = '', client_id } = {}) {
      this.loading = true; this.error = null
      try {
        const qs = new URLSearchParams()
        if (q) qs.set('q', q)
        if (client_id) qs.set('client_id', String(client_id))
        const res = await api(`/projects${qs.toString() ? `?${qs}` : ''}`)
        this.items = res.projects ?? []
      } catch (e) { this.error = e.message }
      finally { this.loading = false }
    },
    async create(payload) {
      const created = await api('/projects', { method: 'POST', body: payload })
      this.items.unshift(created)
      return created
    },
    async remove(id) {
      await api(`/projects/${id}`, { method: 'DELETE' })
      this.items = this.items.filter(p => p.id !== id)
    },

    // ------- detail (categories / BOM / summary) -------
    async openDetail(pid) {
      this.detail.projectId = pid
      await Promise.all([this.fetchProjectCats(pid), this.fetchProjectBom(pid), this.fetchProjectSummary(pid)])
    },
    async fetchProjectCats(pid) {
      this.detail.loadingCats = true
      try {
        const { categories } = await api(`/projects/${pid}/categories`)
        this.detail.cats = categories ?? []
      } finally { this.detail.loadingCats = false }
    },
    async addProjectCat(pid, { category_id, base_cost_usd = 0 }) {
      return api(`/projects/${pid}/categories`, { method: 'POST', body: { category_id, base_cost_usd } })
        .then(pc => { this.detail.cats.push(pc); return pc })
    },
    async deleteProjectCat(pid, pcid) {
      await api(`/projects/${pid}/categories/${pcid}`, { method: 'DELETE' })
      this.detail.cats = this.detail.cats.filter(x => x.id !== pcid)
    },

    async fetchProjectBom(pid) {
      this.detail.loadingBom = true
      try {
        const { components } = await api(`/projects/${pid}/components`)
        this.detail.bom = components ?? []
      } finally { this.detail.loadingBom = false }
    },
    async addProjectBom(pid, body) {
      return api(`/projects/${pid}/components`, { method: 'POST', body })
        .then(row => { this.detail.bom.push(row); return row })
    },
    async deleteProjectBom(pid, bid) {
      await api(`/projects/${pid}/components/${bid}`, { method: 'DELETE' })
      this.detail.bom = this.detail.bom.filter(x => x.id !== bid)
    },

    async fetchProjectSummary(pid) {
      this.detail.loadingSummary = true
      try {
        this.detail.summary = await api(`/projects/${pid}/summary`)
      } finally { this.detail.loadingSummary = false }
    },
    async fetchOne(id) {
      this.loading = true; this.error = null
      try {
        const res = await api().get(`/projects/${id}`)
        const idx = this.items.findIndex(p => p.id === res.id)
        if (idx >= 0) this.items[idx] = res
        else this.items.push(res)
        return res
      } catch (e) {
        this.error = e?.error || 'Failed to load project'
        throw e
      } finally {
        this.loading = false
      }
    }
  }
})
