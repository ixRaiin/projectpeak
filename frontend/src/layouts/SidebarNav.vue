<template>
  <aside
    class="w-64 h-screen sticky top-0 text-white shadow-[var(--shadow-pop)]"
    style="background-color: var(--color-navy) !important;"
    role="navigation"
    aria-label="Primary"
  >
    <div class="h-full flex flex-col">
      <!-- Brand -->
      <div class="flex items-center gap-3 px-4 py-5 border-b border-white/10">
        <img src="/projectpeak.png" alt="ProjectPeak logo" class="w-8 h-8" />
        <span class="text-lg font-semibold tracking-tight">ProjectPeak</span>
      </div>

      <!-- Scrollable nav -->
      <div class="px-3 py-4 flex-1 overflow-y-auto">
        <nav class="space-y-1">
          <RouterLink
            v-for="item in navItems"
            :key="item.to"
            :to="item.to"
            class="flex items-center gap-5 px-3 py-5 rounded-[--radius-sm] font-extrabold hover:bg-white/10 focus-visible:outline-none"
            :class="linkClass(item.to)"
            @click="$emit('navigate')"
          >
            <component :is="item.iconComponent" class="w-5 h-5" />
            <span class="truncate">{{ item.label }}</span>
          </RouterLink>
        </nav>
      </div>

      <!-- Footer -->
      <div class="mt-auto px-3 py-3 border-t border-white/10">
        <div class="px-3 py-2 rounded-[--radius-sm] text-white/80 text-sm truncate">
          {{ userLabel }}
        </div>
        <button
          @click="doLogout"
          class="flex items-center gap-2 px-3 py-2 w-full rounded-[--radius-sm] hover:bg-white/10 focus-visible:outline-none text-white/90"
        >
          <LogOut class="w-5 h-5" />
          <span>Logout</span>
        </button>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import { useAuth } from '@/stores/auth'
import { h } from 'vue'
import { Home, Folder, Users, Package, LogOut } from 'lucide-vue-next'

defineEmits(['navigate'])

const route = useRoute()
const router = useRouter()
const auth = useAuth()

const baseItems = [
  { to: '/',        iconComponent: Home,    label: 'Home' },
  { to: '/projects', iconComponent: Folder, label: 'Projects' },
  { to: '/clients',  iconComponent: Users,  label: 'Clients' },
  { to: '/catalog',  iconComponent: Package, label: 'Catalog' },
]

const navItems = computed(() => baseItems)

function linkClass(path) {
  const active = route.path === path || route.path.startsWith(path + '/')
  return active ? 'bg-white/10 text-white' : 'text-white/90'
}

const userLabel = computed(() => auth?.user?.name || auth?.user?.email || 'Signed in')

onMounted(() => {
  const hasToken = !!auth?.token || !!localStorage.getItem('token')
  if (!hasToken) router.replace('/login')
})

async function onLogout() {
  try { await auth.logout() } catch {/* handle error if needed */ }
  router.replace('/login')
}
</script>
