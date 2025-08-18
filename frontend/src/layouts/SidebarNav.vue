<template>
  <aside
    class="h-screen sticky top-0 w-64 text-white shadow-[var(--shadow-pop)]"
    style="background-color: var(--color-navy) !important;"
  >
    <div class="px-3 py-4">
      <RouterLink
        to="/"
        class="block px-3 py-2 rounded-[--radius-sm] font-medium hover:bg-white/10 focus-visible:outline-none"
        :class="linkClass('/')"
        @click="$emit('navigate')">
        🏠 Home
      </RouterLink>

      <nav class="mt-1 space-y-1">
        <RouterLink
          v-for="item in items"
          :key="item.to"
          :to="item.to"
          class="flex items-center gap-2 px-3 py-2 rounded-[--radius-sm] hover:bg-white/10 focus-visible:outline-none"
          :class="linkClass(item.to)"
          @click="$emit('navigate')">
          <span class="w-5 text-center">{{ item.icon }}</span>
          <span class="truncate">{{ item.label }}</span>
        </RouterLink>
      </nav>
    </div>
  </aside>
</template>

<script setup>
import { useRoute, RouterLink } from 'vue-router'
const route = useRoute()
defineEmits(['navigate'])

const items = [
  { to: '/projects',   icon: '📁', label: 'Projects' },
  { to: '/clients',    icon: '👥', label: 'Clients' },
  { to: '/catalog',    icon: '📦', label: 'Catalog' },
  { to: '/components', icon: '🧩', label: 'Components' },
  { to: '/categories', icon: '🏷️', label: 'Categories' },
]

function linkClass(path) {
  const active = route.path === path || route.path.startsWith(path + '/')
  return active ? 'bg-white/10 text-white' : 'text-white/90'
}
</script>
