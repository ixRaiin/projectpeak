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
  { path: '/login', name: 'login', component: LoginView, meta: { guestOnly: true } },
  { path: '/register', name: 'register', component: RegisterView, meta: { guestOnly: true } },
  { path: '/', name: 'home', component: HomeView, meta: { requiresAuth: true } },
  { path: '/projects', name: 'projects', component: ProjectsView, meta: { requiresAuth: true } },
  { path: '/projects/:id', name: 'project-detail', component: ProjectDetailView, meta: { requiresAuth: true } },
  { path: '/projects/new', name: 'project-new', component: ProjectAddView, meta: { requiresAuth: true } },
  { path: '/clients', name: 'clients', component: ClientsView, meta: { requiresAuth: true } },
  { path: '/catalog', name: 'catalog', component: CatalogView, meta: { requiresAuth: true } },
  { path: '/categories', name: 'categories', component: CategoriesView, meta: { requiresAuth: true } },
  { path: '/components', name: 'components', component: ComponentsView, meta: { requiresAuth: true } },

  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach(async (to) => {
  const auth = useAuth()
  if (to.meta.requiresAuth && auth.user === null && !auth.loading) {
    await auth.fetchMe()
  }

  if (to.meta.requiresAuth && !auth.user) {
    return { path: '/login', replace: true }
  }
  if (to.meta.guestOnly && auth.user) {
    return { path: '/', replace: true }
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
