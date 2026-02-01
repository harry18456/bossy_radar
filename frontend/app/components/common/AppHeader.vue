<script setup lang="ts">
// Common App Header Component
// Extracted from layouts/default.vue to be reused across layouts.
</script>

<template>
  <header
    class="border-b border-gray-200 dark:border-slate-800 bg-white/70 dark:bg-slate-900/70 backdrop-blur-md sticky top-0 z-50"
  >
    <div
      class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between"
    >
      <div class="flex items-center space-x-3">
        <NuxtLink
          to="/"
          class="text-xl font-bold bg-gradient-to-r from-blue-600 to-cyan-500 bg-clip-text text-transparent"
        >
          慣老闆雷達 (Bossy Radar)
        </NuxtLink>
      </div>

      <div class="flex items-center space-x-3">
        <NuxtLink
          to="/watchlist"
          class="group p-2 rounded-md hover:bg-gray-100 dark:hover:bg-slate-800 text-gray-600 dark:text-slate-400 transition-colors"
          title="追蹤清單"
        >
          <div class="relative w-5 h-5">
            <Icon
              name="lucide:heart"
              class="absolute inset-0 w-5 h-5 transition-opacity group-hover:opacity-0"
            />
            <Icon
              name="heroicons:heart-20-solid"
              class="absolute inset-0 w-5 h-5 text-red-500 opacity-0 transition-opacity group-hover:opacity-100"
            />
          </div>
        </NuxtLink>

        <!-- Separator -->
        <span class="text-gray-300 dark:text-gray-700 select-none">|</span>

        <!-- Back to Brand Home (Eraser) -->
        <a
          href="https://www.eraser.tw"
          class="group p-2 rounded-md hover:bg-gray-100 dark:hover:bg-slate-800 text-gray-600 dark:text-slate-400 hover:text-sky-500 dark:hover:text-sky-400 transition-colors"
          title="回品牌首頁"
        >
          <div class="relative w-5 h-5 flex items-center justify-center">
            <Icon
              name="heroicons:arrow-left-start-on-rectangle"
              class="w-5 h-5 transition-colors"
            />
          </div>
        </a>

        <CommonThemeToggle />
      </div>
    </div>
  </header>
</template>
