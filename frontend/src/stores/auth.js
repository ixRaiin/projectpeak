import { defineStore } from 'pinia';
import { api } from '@/lib/api';

export const useAuth = defineStore('auth', {
  state: () => ({ user: null, loading: false, error: null }),
  actions: {
    async fetchMe() {
      this.loading = true; this.error = null;
      try { const { user } = await api('/auth/me'); this.user = user; }
      catch (e) { this.error = e.message; this.user = null; }
      finally { this.loading = false; }
    },
    async register(payload) {
      this.loading = true; this.error = null;
      try { const u = await api('/auth/register', { method: 'POST', body: payload });
            this.user = { id: u.id, name: u.name, email: u.email }; }
      catch (e) { this.error = e.message; throw e; }
      finally { this.loading = false; }
    },
    async login(payload) {
      this.loading = true; this.error = null;
      try { const u = await api('/auth/login', { method: 'POST', body: payload });
            this.user = { id: u.id, name: u.name, email: u.email }; }
      catch (e) { this.error = e.message; throw e; }
      finally { this.loading = false; }
    },
    async logout() {
      await api('/auth/logout', { method: 'POST' });
      this.user = null;
    }
  }
});
