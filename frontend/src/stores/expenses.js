// src/stores/expenses.js
import { defineStore } from 'pinia';
import api from '@/lib/api';

export const useExpenses = defineStore('expenses', {
  state: () => ({
    items: [],
    loading: false,
    error: null,
  }),
  actions: {
    async fetchForProject(pid) {
      this.loading = true; this.error = null;
      try {
        const data = await api.get(`/projects/${pid}/expenses`);
        this.items = Array.isArray(data) ? data : (data.expenses || []);
      } catch (e) {
        this.error = e.message;
      } finally {
        this.loading = false;
      }
    },
    async create(pid, body) {
      this.error = null;
      const created = await api.post(`/projects/${pid}/expenses`, body);
      this.items.unshift(created);
      return created;
    },
  },
});
