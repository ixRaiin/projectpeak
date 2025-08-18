<template>
  <div class="min-h-screen flex">
    <!-- Desktop sidebar -->
    <SideNav class="hidden md:block" />

    <!-- Content column -->
    <div class="flex-1 min-w-0 flex flex-col">
      <HeaderBar @toggle-nav="mobileOpen = true" />

      <main class="page">
        <router-view />
      </main>
    </div>

    <!-- Mobile sidebar drawer -->
    <teleport to="body">
      <div v-if="mobileOpen" class="fixed inset-0 z-50 md:hidden">
        <div class="absolute inset-0 bg-black/40" @click="mobileOpen = false" />
        <div class="absolute inset-y-0 left-0 w-[84vw] max-w-[20rem]">
          <SideNav @navigate="mobileOpen = false" />
        </div>
      </div>
    </teleport>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import HeaderBar from '@/layouts/HeaderBar.vue'
import SideNav from '@/layouts/SidebarNav.vue'
const mobileOpen = ref(false)
</script>


