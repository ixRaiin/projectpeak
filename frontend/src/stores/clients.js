// src/stores/clients.js
import { defineStore } from 'pinia';
import api from '@/lib/api';

export const useClients = defineStore('clients', {
  state: () => ({
    items: [],
    loading: false,
    error: null,
  }),
  actions: {
    async fetchAll(params = {}) {
      this.loading = true; this.error = null;
      try {
        const q = new URLSearchParams(params).toString();
        const data = await api.get(`/clients${q ? `?${q}` : ''}`);
        this.items = Array.isArray(data) ? data : (data.clients || []);
      } catch (e) {
        this.error = e.message;
      } finally {
        this.loading = false;
      }
    },
    async create(body) {
      const c = await api.post('/clients', body);
      this.items.unshift(c);
      return c;
    },
    async remove(id) {
      await api.delete(`/clients/${id}`);
      this.items = this.items.filter(x => x.id !== id);
    },
  },
});
