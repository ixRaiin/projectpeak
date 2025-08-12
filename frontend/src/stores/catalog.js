import { defineStore } from 'pinia'
import { api } from '@/lib/api'

export const useCatalog = defineStore('catalog', {
  state: () => ({
    categories: [],
    components: [],
    loadingCats: false,
    loadingComps: false,
    error: null,
  }),
  actions: {
    async fetchCategories({ q = '', includeDeleted = false } = {}) {
      this.loadingCats = true; this.error = null
      try {
        const qs = new URLSearchParams()
        if (q) qs.set('q', q)
        if (includeDeleted) qs.set('include_deleted', 'true')
        const { categories } = await api(`/categories${qs.toString() ? `?${qs}` : ''}`)
        this.categories = categories || []
      } catch (e) { this.error = e.message }
      finally { this.loadingCats = false }
    },
    async fetchComponents({ category_id, q = '' } = {}) {
      this.loadingComps = true; this.error = null
      try {
        const qs = new URLSearchParams()
        if (category_id) qs.set('category_id', String(category_id))
        if (q) qs.set('q', q)
        const { components } = await api(`/components${qs.toString() ? `?${qs}` : ''}`)
        this.components = components || []
      } catch (e) { this.error = e.message }
      finally { this.loadingComps = false }
    },
  }
})
