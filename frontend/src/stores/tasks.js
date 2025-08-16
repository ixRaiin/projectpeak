// src/stores/tasks.js
import { defineStore } from 'pinia';
import api from '@/lib/api';

export const useTasks = defineStore('tasks', {
  state: () => ({
    items: [],
    progress: { percent: 0 },
    loading: false,
    error: null,
  }),

  actions: {
    async fetchForProject(pid) {
      this.loading = true; this.error = null;
      try {
        const data = await api.get(`/projects/${pid}/tasks`);
        // accept either an array or {tasks:[...]}
        this.items = Array.isArray(data) ? data : (data.tasks || []);
      } catch (e) {
        this.error = e?.message || 'Failed to load tasks';
      } finally {
        this.loading = false;
      }
    },

    async fetchProgress(pid) {
      try {
        const data = await api.get(`/projects/${pid}/tasks/progress`);
        this.progress = data || { percent: 0 };
      } catch (e) {
        this.error = e?.message || 'Failed to load progress';
      }
    },

    async create(pid, body) {
      const t = await api.post(`/projects/${pid}/tasks`, body);
      // accept either raw task or {task: {...}}
      const task = t?.task || t;
      this.items.push(task);
      return task;
    },

    async update(pid, tid, patch) {
      const res = await api.patch(`/projects/${pid}/tasks/${tid}`, patch);
      const updated = res?.task || res;
      const i = this.items.findIndex(x => x.id === tid);
      if (i !== -1) this.items[i] = { ...this.items[i], ...updated };
      return updated;
    },

    async remove(pid, tid) {
      await api.delete(`/projects/${pid}/tasks/${tid}`);
      this.items = this.items.filter(t => t.id !== tid);
    },
  },
});
