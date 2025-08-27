// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import { useAuth } from '@/stores/auth'
import LoginView from '@/views/LoginView.vue'
import RegisterView from '@/views/RegisterView.vue'

const HomeView = () => import('@/views/HomeView.vue')
const ProjectsView = () => import('@/views/ProjectsView.vue')
const ClientsView = () => import('@/views/ClientsView.vue')
const CatalogView = () => import('@/views/CatalogView.vue')
const ComponentsView = () => import('@/views/ComponentsView.vue')
const CategoriesView = () => import('@/views/CategoriesView.vue')
const ProjectDetailView = () => import('@/views/ProjectDetailView.vue')
const ProjectAddView = () => import('@/views/AddProjectView.vue')

const routes = [
  // Auth (guest-only) — mark with layout:'auth' so chrome is hidden
  { path: '/login',    name: 'login',    component: LoginView,    meta: { guestOnly: true, layout: 'auth' } },
  { path: '/register', name: 'register', component: RegisterView, meta: { guestOnly: true, layout: 'auth' } },

  // App (protected)
  { path: '/',                name: 'home',            component: HomeView,          meta: { requiresAuth: true } },
  { path: '/projects',        name: 'projects',        component: ProjectsView,      meta: { requiresAuth: true } },
  { path: '/projects/new',    name: 'project-new',     component: ProjectAddView,    meta: { requiresAuth: true } },
  { path: '/projects/:id',    name: 'project-detail',  component: ProjectDetailView, meta: { requiresAuth: true } },
  { path: '/clients',         name: 'clients',         component: ClientsView,       meta: { requiresAuth: true } },
  { path: '/catalog',         name: 'catalog',         component: CatalogView,       meta: { requiresAuth: true } },
  { path: '/categories',      name: 'categories',      component: CategoriesView,    meta: { requiresAuth: true } },
  { path: '/components',      name: 'components',      component: ComponentsView,    meta: { requiresAuth: true } },

  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach(async (to) => {
  const auth = useAuth()

  // Consider either a loaded user OR a stored token as "maybe authed"
  const token = auth.token || localStorage.getItem('token') || null
  const hasUser = !!auth.user
  const isAuthed = hasUser || !!token

  // Lazy-load user if you have a token but no user yet
  if (!hasUser && token && !auth.loading) {
    try { await auth.fetchMe() } catch {/* ignore */ }
  }

  // Final check after possible fetch
  const authedNow = !!useAuth().user || !!token

  // Block protected routes
  if (to.meta.requiresAuth && !authedNow) {
    return { name: 'login', query: { redirect: to.fullPath }, replace: true }
  }

  // Prevent reaching /login or /register when already authed
  if (to.meta.guestOnly && authedNow) {
    return { name: 'home', replace: true }
  }

  return true
})

router.onError((err, to) => {
  const msg = String(err?.message || err)
  if (/(dynamic imported module|Loading chunk|error loading dynamically imported module)/i.test(msg)) {
    window.location.href = '/login'
  } else {
    console.error('Router error:', err, 'while navigating to', to?.fullPath)
  }
})

export default router
