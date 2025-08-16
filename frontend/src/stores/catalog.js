// src/stores/catalog.js
import { defineStore } from 'pinia';
import api from '@/lib/api';

export const useCatalog = defineStore('catalog', {
  state: () => ({
    categories: [],
    components: [],  // NOTE: filtered by last fetchComponents() call
    loading: false,
    error: null,
  }),
  actions: {
    async fetchCategories(params = {}) {
      this.loading = true; this.error = null;
      try {
        const q = new URLSearchParams(params).toString();
        const data = await api.get(`/categories${q ? `?${q}` : ''}`);
        this.categories = Array.isArray(data) ? data : (data.categories || []);
      } catch (e) {
        this.error = e.message;
      } finally {
        this.loading = false;
      }
    },
    async createCategory(body) {
      const row = await api.post('/categories', body);
      this.categories.unshift(row);
      return row;
    },

    async fetchComponents(params = {}) {
      this.loading = true; this.error = null;
      try {
        const q = new URLSearchParams(params).toString();
        const data = await api.get(`/components${q ? `?${q}` : ''}`);
        this.components = Array.isArray(data) ? data : (data.components || []);
      } catch (e) {
        this.error = e.message;
      } finally {
        this.loading = false;
      }
    },
    async createComponent(body) {
      const row = await api.post('/components', body);
      this.components.unshift(row);
      return row;
    },
  },
});
