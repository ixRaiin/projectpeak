// src/stores/auth.js
import { defineStore } from 'pinia';
import api from '@/lib/api';

export const useAuth = defineStore('auth', {
  state: () => ({
    user: null,
    loading: false,
    error: null,
  }),
  actions: {
    async fetchMe() {
      this.loading = true; this.error = null;
      try {
        const me = await api.get('/auth/me');
        this.user = me || null;
      } catch (e) {
        this.user = null;
        this.error = e.message;
      } finally {
        this.loading = false;
      }
    },
    async login(email, password) {
      this.loading = true; this.error = null;
      try {
        await api.post('/auth/login', { email, password });
        await this.fetchMe();
      } catch (e) {
        this.error = e.message;
        throw e;
      } finally {
        this.loading = false;
      }
    },
    async logout() {
      this.loading = true; this.error = null;
      try {
        // ignore any API error; local logout still proceeds
        await api.post('/auth/logout', {});
      } catch {/* ignore */ }
      this.user = null;
      this.loading = false;
    },
  },
});
