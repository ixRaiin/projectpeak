<template>
  <header class="sticky top-0 z-40 bg-[--color-surface] border-b border-[--color-border-warm]">
    <div class="page !py-3 flex items-center gap-3">
      <!-- Mobile menu button -->
      <button
        class="md:hidden btn btn-ghost btn-ghost-hover"
        aria-label="Open navigation"
        @click="$emit('toggle-nav')">
        <svg viewBox="0 0 24 24" class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" d="M4 7h16M4 12h16M4 17h16" />
        </svg>
      </button>

      <!-- Brand -->
      <RouterLink to="/" class="text-base font-semibold tracking-tight">
        ProjectPeak
      </RouterLink>

      <div class="flex-1" />

      <!-- Global search (stub) -->
      <div class="hidden sm:flex items-center">
        <input type="search" placeholder="Search…" class="field w-72" aria-label="Global search" />
      </div>

      <!-- User actions -->
      <div class="flex items-center gap-2">
        <RouterLink to="/projects" class="btn btn-ghost btn-ghost-hover">Projects</RouterLink>
        <button class="btn btn-dark btn-dark-hover" @click="onLogout">Logout</button>
      </div>
    </div>
  </header>
</template>

<script setup>
import { RouterLink } from 'vue-router'
// If your auth store name/methods differ, adjust here or leave as a no-op
let auth
try {
  const { useAuth } = await import('@/stores/auth.js')
  auth = useAuth()
} catch { /* optional */ }

async function onLogout() {
  try { await auth?.logout?.() } catch {/* */}
}
</script>
