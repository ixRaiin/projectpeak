import { defineStore } from 'pinia';
import { api } from '@/lib/api';

export const useComponents = defineStore('components', {
  state: () => ({ items: [], loading: false, error: '' }),
  actions: {
    async fetchAll(params = {}) {
      this.loading = true; this.error = '';
      try {
        const { components } = await api.get('/components', params);
        this.items = components;
      } catch (e) {
        this.error = e.message;
      } finally { this.loading = false; }
    },
    async create(payload) {
      this.error = '';
      const created = await api.post('/components', payload);
      this.items.push(created);
    },
    async update(id, payload) {
      this.error = '';
      const updated = await api.patch(`/components/${id}`, payload);
      const i = this.items.findIndex(x => x.id === id);
      if (i !== -1) this.items[i] = updated;
    },
    async remove(id) {
      this.error = '';
      await api.delete(`/components/${id}`);
      this.items = this.items.filter(x => x.id !== id);
    }
  }
});
