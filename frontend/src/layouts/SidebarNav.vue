<template>
  <aside
    class="h-screen sticky top-0 w-64 bg-[--color-navy] text-white shadow-[var(--shadow-pop)]">
    <div class="px-3 py-4">
      <RouterLink
        to="/"
        class="block px-3 py-2 rounded-[--radius-sm] font-medium hover:bg-white/10 focus-visible:outline-none"
        :class="isActive('/') ? 'bg-[--color-navy-500]' : 'text-white/90'"
        @click="$emit('navigate')">
        🏠 Home
      </RouterLink>

      <nav class="mt-1 space-y-1">
        <NavItem to="/projects" icon="📁" label="Projects" />
        <NavItem to="/clients" icon="👥" label="Clients" />
        <NavItem to="/catalog" icon="📦" label="Catalog" />
        <NavItem to="/components" icon="🧩" label="Components" />
        <NavItem to="/categories" icon="🏷️" label="Categories" />
      </nav>
    </div>
  </aside>
</template>

<script setup>
import { useRoute, RouterLink } from 'vue-router'
const route = useRoute()
defineEmits(['navigate'])

function isActive(path) {
  // Basic startsWith match for section highlight
  return route.path === path || route.path.startsWith(path + '/')
}

// Inline subcomponent for nav links
const NavItem = {
  name: 'NavItem',
  props: { to: { type: String, required: true }, icon: String, label: String },
  components: { RouterLink },
  methods: {
    active(current, target) {
      return current === target || current.startsWith(target + '/')
    }
  },
  computed: {
    activeClass() {
      const current = this.$route.path
      return this.active(current, this.to) ? 'bg-[--color-navy-500] text-white' : 'text-white/90'
    }
  },
  template: `
    <RouterLink
      :to="to"
      class="flex items-center gap-2 px-3 py-2 rounded-[--radius-sm] hover:bg-white/10 focus-visible:outline-none"
      :class="activeClass"
      @click="$emit('navigate')">
      <span class="w-5 text-center">{{ icon }}</span>
      <span class="truncate">{{ label }}</span>
    </RouterLink>
  `
}
</script>
