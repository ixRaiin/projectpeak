// src/stores/tasks.js
import { defineStore } from 'pinia'
import api from '@/lib/api'

export const useTasksStore = defineStore('tasks', {
  state: () => ({
    byProject: {},
    progressByProject: {},
    commentsByTask: {},
    loading: {
      tasks: false,
      progress: false,
      comments: {},
    },
    errors: {
      tasks: null,
      progress: null,
      comments: {},
      mutate: null,
      commentsMutate: {},
    },
  }),

  actions: {
    async fetchTasks(pid) {
      this.loading.tasks = true
      this.errors.tasks = null
      try {
        const res = await api.get(`/projects/${pid}/tasks`)
        const list = Array.isArray(res?.tasks) ? res.tasks : []
        list.sort((a, b) => (a.order_index ?? 0) - (b.order_index ?? 0) || (a.id ?? 0) - (b.id ?? 0))
        this.byProject[pid] = list
        return list
      } catch (e) {
        this.errors.tasks = e?.message || 'Failed to load tasks'
        this.byProject[pid] = this.byProject[pid] || []
        return this.byProject[pid]
      } finally {
        this.loading.tasks = false
      }
    },

    async fetchProgress(pid) {
      this.loading.progress = true
      this.errors.progress = null
      try {
        const res = await api.get(`/projects/${pid}/tasks/progress`)
        this.progressByProject[pid] = res || {
          percent: 0,
          totals: { done: 0, total: 0, leaves_done: 0, leaves_total: 0 },
          by_status: { todo: 0, doing: 0, done: 0 },
          computed_at: new Date().toISOString(),
        }
        return this.progressByProject[pid]
      } catch (e) {
        this.errors.progress = e?.message || 'Failed to load progress'
        if (!this.progressByProject[pid]) {
          this.progressByProject[pid] = {
            percent: 0,
            totals: { done: 0, total: 0, leaves_done: 0, leaves_total: 0 },
            by_status: { todo: 0, doing: 0, done: 0 },
            computed_at: new Date().toISOString(),
          }
        }
        return this.progressByProject[pid]
      } finally {
        this.loading.progress = false
      }
    },

    async fetchComments(pid, tid) {
      this.loading.comments[tid] = true
      this.errors.comments[tid] = null
      try {
        const res = await api.get(`/projects/${pid}/tasks/${tid}/comments`)
        const list = Array.isArray(res?.comments) ? res.comments : []
        this.commentsByTask[tid] = list
        return list
      } catch (e) {
        this.errors.comments[tid] = e?.message || 'Failed to load comments'
        this.commentsByTask[tid] = this.commentsByTask[tid] || []
        return this.commentsByTask[tid]
      } finally {
        this.loading.comments[tid] = false
      }
    },

    async addComment(pid, tid, body) {
      this.errors.commentsMutate[tid] = null
      try {
        const created = await api.post(`/projects/${pid}/tasks/${tid}/comments`, { body })
        if (!this.commentsByTask[tid]) this.commentsByTask[tid] = []
        this.commentsByTask[tid].push(created)
        return created
      } catch (e) {
        this.errors.commentsMutate[tid] = e?.message || 'Failed to add comment'
        throw e
      }
    },

    async deleteComment(pid, tid, cid) {
      this.errors.commentsMutate[tid] = null
      // optimistic remove
      const list = this.commentsByTask[tid] || []
      const idx = list.findIndex(c => c.id === cid)
      const removed = idx !== -1 ? list.splice(idx, 1)[0] : null
      try {
        await api.delete(`/projects/${pid}/tasks/${tid}/comments/${cid}`)
        return true
      } catch (e) {
        if (removed) list.splice(idx, 0, removed)
        this.errors.commentsMutate[tid] = e?.message || 'Failed to delete comment'
        throw e
      }
    },

    async createTask(pid, payload) {
      this.errors.mutate = null
      try {
        const created = await api.post(`/projects/${pid}/tasks`, payload)
        if (!this.byProject[pid]) this.byProject[pid] = []
        this.byProject[pid].push(created)
        this.byProject[pid].sort((a, b) => (a.order_index ?? 0) - (b.order_index ?? 0) || (a.id ?? 0) - (b.id ?? 0))
        return created
      } catch (e) {
        this.errors.mutate = e?.message || 'Failed to create task'
        throw e
      } finally {
        this.fetchProgress(pid).catch(() => {})
      }
    },

    async updateTask(pid, tid, patch) {
      this.errors.mutate = null
      const list = this.byProject[pid] || []
      const idx = list.findIndex(t => t.id === tid)
      const prev = idx !== -1 ? { ...list[idx] } : null
      if (idx !== -1) list[idx] = { ...list[idx], ...patch }
      try {
        const updated = await api.patch(`/projects/${pid}/tasks/${tid}`, patch)
        if (idx !== -1) list[idx] = updated
        this.byProject[pid] = list.slice().sort((a, b) => (a.order_index ?? 0) - (b.order_index ?? 0) || (a.id ?? 0) - (b.id ?? 0))
        return updated
      } catch (e) {
        if (idx !== -1 && prev) list[idx] = prev
        this.errors.mutate = e?.message || 'Failed to update task'
        throw e
      } finally {
        this.fetchProgress(pid).catch(() => {})
      }
    },

    async deleteTask(pid, tid) {
      this.errors.mutate = null
      const list = this.byProject[pid] || []
      const idx = list.findIndex(t => t.id === tid)
      const removed = idx !== -1 ? list.splice(idx, 1)[0] : null
      try {
        await api.delete(`/projects/${pid}/tasks/${tid}`)
        return true
      } catch (e) {
        if (removed) list.splice(idx, 0, removed)
        this.errors.mutate = e?.message || 'Failed to delete task'
        throw e
      } finally {
        this.fetchProgress(pid).catch(() => {})
      }
    },
  },
})
