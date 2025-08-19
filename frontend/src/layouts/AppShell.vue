<template>
  <div class="min-h-screen flex">
    <!-- Sidebar (always visible on desktop) -->
    <SidebarNav />

    <!-- Content column -->
    <div class="flex-1 min-w-0 flex flex-col">
      <HeaderBar @toggle-nav="mobileOpen = true" />

      <!-- Tighter spacing -->
      <main class="page !px-4 !py-4 md:!px-6 md:!py-6">
        <router-view />
      </main>
    </div>

    <!-- Mobile sidebar drawer -->
    <teleport to="body">
      <div v-if="mobileOpen" class="fixed inset-0 z-50 md:hidden">
        <div class="absolute inset-0 bg-black/40" @click="mobileOpen = false" />
        <div class="absolute inset-y-0 left-0 w-[84vw] max-w-[20rem]">
          <SidebarNav @navigate="mobileOpen = false" />
        </div>
      </div>
    </teleport>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import HeaderBar from './HeaderBar.vue'
import SidebarNav from './SidebarNav.vue'

const mobileOpen = ref(false)
</script>
