import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '@/views/LoginView.vue'
import RegisterView from '@/views/RegisterView.vue'
import { useAuth } from '@/stores/auth'

const HomeView = () => import('@/views/HomeView.vue')
const ProjectsView = () => import('@/views/ProjectsView.vue')
const ClientsView = () => import('@/views/ClientsView.vue')
const CatalogView = () => import('@/views/CatalogView.vue')
const ComponentsView = () => import('@/views/ComponentsView.vue')
const CategoriesView = () => import('@/views/CategoriesView.vue')

const routes = [
  { path: '/login', component: LoginView, meta: { guestOnly: true } },
  { path: '/register', component: RegisterView, meta: { guestOnly: true } },
  { path: '/clients', component: ClientsView, meta: { requiresAuth: true } },
  { path: '/projects', component: ProjectsView, meta: { requiresAuth: true } },
  { path: '/projects/:id', component: () => import('@/views/ProjectDetailView.vue'), meta: { requiresAuth: true } },
  { path: '/catalog', component: CatalogView, meta: { requiresAuth: true } },
  { path: '/categories', component: ComponentsView, meta: { requiresAuth: true } },
  { path: '/components', component: CategoriesView, meta: { requiresAuth: true } },
  { path: '/', component: HomeView, meta: { requiresAuth: true } },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach(async (to) => {
  const auth = useAuth()
  if (auth.user === null && !auth.loading) await auth.fetchMe()
  if (to.meta.requiresAuth && !auth.user) return '/login'
  if (to.meta.guestOnly && auth.user) return '/'
  return true
})

export default router
