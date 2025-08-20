// src/stores/tasks.js
import { defineStore } from 'pinia'
import api from '@/lib/api'

/* ---------------- helpers ---------------- */
const ord = (t) =>
  Number.isFinite(Number(t?.order_index)) ? Number(t.order_index)
  : Number.isFinite(Number(t?.sort_index)) ? Number(t.sort_index)
  : Number.isFinite(Number(t?.position)) ? Number(t.position)
  : 0

const sortTasks = (list) =>
  list.slice().sort((a, b) => (ord(a) - ord(b)) || ((a.id ?? 0) - (b.id ?? 0)))

const asArray = (x, key = 'tasks') => {
  if (Array.isArray(x)) return x
  if (x && Array.isArray(x[key])) return x[key]
  if (x && Array.isArray(x.items)) return x.items
  if (x && Array.isArray(x.data)) return x.data
  return []
}

const norm = (s) => String(s || '').toLowerCase()
const normStatus = (s) => {
  const v = norm(s)
  if (['todo', 'to-do', 'planned', 'backlog'].includes(v)) return 'todo'
  if (['doing', 'in-progress', 'progress', 'active'].includes(v)) return 'doing'
  if (['done', 'complete', 'completed', 'closed'].includes(v)) return 'done'
  return 'todo'
}

const groupByStatus = (list) => {
  const g = { todo: [], doing: [], done: [] }
  for (const t of list) g[normStatus(t.status)].push(t)
  return g
}

// Local, optimistic progress calculator for immediate UI feedback
const computeProgressLocal = (list) => {
  const groups = groupByStatus(list)
  const total = list.length
  const done = groups.done.length
  const percent = total ? Math.round((done / total) * 100) : 0
  // heuristic suggestion for project status
  const suggestion =
    total === 0 ? 'planned'
    : (done === total ? 'completed' : (groups.doing.length > 0 || done > 0 ? 'active' : 'planned'))
  return {
    percent,
    totals: { done, total, leaves_done: done, leaves_total: total },
    by_status: { todo: groups.todo.length, doing: groups.doing.length, done: groups.done.length },
    computed_at: new Date().toISOString(),
    suggestion,
  }
}

/* ---------------- store ---------------- */
export const useTasksStore = defineStore('tasks', {
  state: () => ({
    byProject: {},                 // { [pid]: Task[] }
    progressByProject: {},         // { [pid]: Progress }
    commentsByTask: {},            // { [tid]: Comment[] }
    loading: {
      tasks: false,
      progress: false,
      comments: {},               // { [tid]: boolean }
    },
    errors: {
      tasks: null,
      progress: null,
      comments: {},               // { [tid]: string|null }
      mutate: null,
      commentsMutate: {},         // { [tid]: string|null }
    },
  }),

  getters: {
    // Sorted list for a project
    list: (s) => (pid) => sortTasks(s.byProject[pid] || []),
    // Grouped by normalized status
    grouped: (s) => (pid) => groupByStatus(sortTasks(s.byProject[pid] || [])),
  },

  actions: {
    /* -------- reads -------- */
    async fetchTasks(pid) {
      this.loading.tasks = true
      this.errors.tasks = null
      try {
        const res = await api.get(`/projects/${pid}/tasks`)
        const list = sortTasks(asArray(res, 'tasks'))
        this.byProject[pid] = list
        // optimistic progress update (instant UI)
        this.progressByProject[pid] = computeProgressLocal(list)
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
        // accept either direct object or wrapped
        const progress = res?.progress || res || {}
        // Backfill minimal shape if BE omits fields
        this.progressByProject[pid] = {
          percent: Number(progress.percent ?? 0),
          totals: {
            done: Number(progress.totals?.done ?? 0),
            total: Number(progress.totals?.total ?? 0),
            leaves_done: Number(progress.totals?.leaves_done ?? progress.totals?.done ?? 0),
            leaves_total: Number(progress.totals?.leaves_total ?? progress.totals?.total ?? 0),
          },
          by_status: {
            todo: Number(progress.by_status?.todo ?? 0),
            doing: Number(progress.by_status?.doing ?? 0),
            done: Number(progress.by_status?.done ?? progress.by_status?.complete ?? 0),
          },
          computed_at: progress.computed_at || new Date().toISOString(),
          suggestion: progress.suggestion || computeProgressLocal(this.byProject[pid] || []).suggestion,
        }
        return this.progressByProject[pid]
      } catch (e) {
        this.errors.progress = e?.message || 'Failed to load progress'
        if (!this.progressByProject[pid]) {
          this.progressByProject[pid] = computeProgressLocal(this.byProject[pid] || [])
        }
        return this.progressByProject[pid]
      } finally {
        this.loading.progress = false
      }
    },

    async refresh(pid) {
      // fetch tasks and server progress in parallel; keep optimistic progress immediately
      const list = await this.fetchTasks(pid)
      this.progressByProject[pid] = computeProgressLocal(list)
      // don't throw if /progress fails
      this.fetchProgress(pid).catch(() => {})
      return list
    },

    /* -------- comments -------- */
    async fetchComments(pid, tid) {
      if (!this.loading.comments) this.loading.comments = {}
      if (!this.errors.comments) this.errors.comments = {}
      this.loading.comments[tid] = true
      this.errors.comments[tid] = null
      try {
        const res = await api.get(`/projects/${pid}/tasks/${tid}/comments`)
        const list = asArray(res, 'comments')
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
      if (!this.errors.commentsMutate) this.errors.commentsMutate = {}
      this.errors.commentsMutate[tid] = null
      try {
        // body: string or { text } or { body }
        const payload = typeof body === 'string' ? { body } : ({ body: body?.body ?? body?.text })
        const created = await api.post(`/projects/${pid}/tasks/${tid}/comments`, payload)
        if (!this.commentsByTask[tid]) this.commentsByTask[tid] = []
        this.commentsByTask[tid].push(created)
        return created
      } catch (e) {
        this.errors.commentsMutate[tid] = e?.message || 'Failed to add comment'
        throw e
      }
    },

    async deleteComment(pid, tid, cid) {
      if (!this.errors.commentsMutate) this.errors.commentsMutate = {}
      this.errors.commentsMutate[tid] = null
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

    /* -------- mutations -------- */
    async createTask(pid, payload) {
      this.errors.mutate = null
      try {
        const created = await api.post(`/projects/${pid}/tasks`, payload)
        if (!this.byProject[pid]) this.byProject[pid] = []
        this.byProject[pid].push(created)
        this.byProject[pid] = sortTasks(this.byProject[pid])
        // optimistic progress
        this.progressByProject[pid] = computeProgressLocal(this.byProject[pid])
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
        this.byProject[pid] = sortTasks(list)
        // optimistic progress
        this.progressByProject[pid] = computeProgressLocal(this.byProject[pid])
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
        this.byProject[pid] = sortTasks(list)
        // optimistic progress
        this.progressByProject[pid] = computeProgressLocal(this.byProject[pid])
        return true
      } catch (e) {
        if (removed) list.splice(idx, 0, removed)
        this.errors.mutate = e?.message || 'Failed to delete task'
        throw e
      } finally {
        this.fetchProgress(pid).catch(() => {})
      }
    },

    /* -------- DnD helpers -------- */
    // Move a task into a status column; optional toIndex for ordering within column
    async moveTask(pid, tid, toStatus, toIndex = null) {
      const list = this.byProject[pid] || []
      const idx = list.findIndex(t => t.id === tid)
      if (idx === -1) return null
      const targetStatus = normStatus(toStatus)

      // compute a simple order_index if an index is provided
      let patch = { status: targetStatus }
      if (toIndex !== null) {
        // re-sequence target column so we can insert at toIndex
        const groups = groupByStatus(list)
        const column = sortTasks(groups[targetStatus])
        // insert our task id into this column at the desired position
        const without = column.filter(t => t.id !== tid)
        without.splice(Math.max(0, Math.min(toIndex, without.length)), 0, list[idx])
        // assign sequential order_index (0..n-1)
        await this.setColumnOrder(pid, targetStatus, without.map(t => t.id))
        return true
      }

      // status-only move
      await this.updateTask(pid, tid, patch)
      return true
    },

    // Set the order for a single column; patches order_index + status for each id in order
    async setColumnOrder(pid, status, orderedIds) {
      const targetStatus = normStatus(status)
      for (let i = 0; i < orderedIds.length; i++) {
        const id = orderedIds[i]
        try {
          await this.updateTask(pid, id, { status: targetStatus, order_index: i, sort_index: i })
        } catch {
          // ignore individual failures to keep UI snappy; a later refresh will reconcile
        }
      }
      // ensure store is sorted after resequence
      this.byProject[pid] = sortTasks(this.byProject[pid] || [])
      // optimistic progress refresh
      this.progressByProject[pid] = computeProgressLocal(this.byProject[pid])
      // best-effort authoritative progress
      this.fetchProgress(pid).catch(() => {})
    },
  },
})
