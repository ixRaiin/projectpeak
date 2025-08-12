import { defineStore } from 'pinia';
import { api } from '@/lib/api';

export const useCategories = defineStore('categories', {
  state: () => ({ items: [], loading: false, error: '' }),
  actions: {
    async fetchAll() {
      this.loading = true; this.error = '';
      try {
        const { categories } = await api.get('/categories');
        this.items = categories;
      } catch (e) {
        this.error = e.message;
      } finally { this.loading = false; }
    },
    async create(payload) {
      this.error = '';
      const created = await api.post('/categories', payload);
      this.items.push(created);
    },
    async update(id, payload) {
      this.error = '';
      const updated = await api.patch(`/categories/${id}`, payload);
      const i = this.items.findIndex(x => x.id === id);
      if (i !== -1) this.items[i] = updated;
    },
    async remove(id) {
      this.error = '';
      await api.delete(`/categories/${id}`);
      this.items = this.items.filter(x => x.id !== id);
    }
  }
});
