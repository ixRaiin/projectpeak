// src/stores/projects.js
import { defineStore } from 'pinia';
import api from '@/lib/api';

function asArray(x) {
  // Accept [{...}], {items:[...]}, {rows:[...]}, {data:[...]}, null/undefined
  if (Array.isArray(x)) return x;
  if (x && Array.isArray(x.items)) return x.items;
  if (x && Array.isArray(x.rows)) return x.rows;
  if (x && Array.isArray(x.data)) return x.data;
  return [];
}

export const useProjects = defineStore('projects', {
  state: () => ({
    items: [],
    loading: false,
    error: null,
    detail: {
      cats: [],
      bom: [],
      summary: null,
    },
  }),
  actions: {
    async fetchAll(params = {}) {
      this.loading = true; this.error = null;
      try {
        const q = new URLSearchParams(params).toString();
        const data = await api.get(`/projects${q ? `?${q}` : ''}`);

        // Accept [], {items:[]}, {rows:[]}, {data:[]}, {projects:[]}
        let arr = asArray(data);
        if (!arr.length && data && Array.isArray(data.projects)) arr = data.projects;

        this.items = arr;
      } catch (e) {
        this.error = e?.message || 'Failed to load projects';
        this.items = [];
      } finally {
        this.loading = false;
      }
    },

    async fetchOne(id) {
      this.loading = true; this.error = null;
      try {
        const p = await api.get(`/projects/${id}`);
        // if not already in list, insert/replace
        const i = this.items.findIndex(x => x.id === p.id);
        if (i === -1) this.items.push(p); else this.items[i] = p;
        return p;
      } catch (e) {
        this.error = e.message;
        throw e;
      } finally {
        this.loading = false;
      }
    },
    async create(body) {
      const created = await api.post('/projects', body);
      return created;
    },
    async remove(id) {
      await api.delete(`/projects/${id}`);
      this.items = this.items.filter(p => p.id !== id);
    },

    // ---------- detail ----------
    async openDetail(pid) {
      this.error = null;
      const [cats, bom, summary] = await Promise.all([
        api.get(`/projects/${pid}/categories`),
        api.get(`/projects/${pid}/components`),
        api.get(`/projects/${pid}/summary`).catch(() => null),
      ]);
      this.detail.cats = asArray(cats);
      this.detail.bom = asArray(bom);
      this.detail.summary = summary;
    },

    async addProjectCat(pid, body) {
      const res = await api.post(`/projects/${pid}/categories`, body);
      const row = res?.project_category || res; // accept wrapped or raw
      if (!Array.isArray(this.detail.cats)) this.detail.cats = asArray(this.detail.cats);
      this.detail.cats = [...this.detail.cats, row];
      return row;
    },
    async deleteProjectCat(pid, pcid) {
      await api.delete(`/projects/${pid}/categories/${pcid}`);
      this.detail.cats = asArray(this.detail.cats).filter(r => r.id !== pcid);
    },

    async addProjectBom(pid, body) {
      const res = await api.post(`/projects/${pid}/components`, body);
      const row = res?.project_component || res;
      if (!Array.isArray(this.detail.bom)) this.detail.bom = asArray(this.detail.bom);
      this.detail.bom = [...this.detail.bom, row];
      return row;
    },
    async deleteProjectBom(pid, id) {
      await api.delete(`/projects/${pid}/components/${id}`);
      this.detail.bom = asArray(this.detail.bom).filter(r => r.id !== id);
    },

    async fetchProjectSummary(pid) {
      this.detail.summary = await api.get(`/projects/${pid}/summary`);
    },
  },
});
