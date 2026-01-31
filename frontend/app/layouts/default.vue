<script setup lang="ts">
import { Toaster } from 'vue-sonner'
</script>

<template>
  <div class="min-h-screen flex flex-col bg-gray-50 dark:bg-slate-950 text-gray-900 dark:text-slate-50 transition-colors duration-300 relative">
    <HomeBackground />
    <div class="relative z-10 flex flex-col min-h-screen">
    <!-- Header -->
    <header class="border-b border-gray-200 dark:border-slate-800 bg-white/70 dark:bg-slate-900/70 backdrop-blur-md sticky top-0 z-50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div class="flex items-center space-x-3">
          <NuxtLink to="/" class="text-xl font-bold bg-gradient-to-r from-blue-600 to-cyan-500 bg-clip-text text-transparent">
            慣老闆雷達 (Bossy Radar)
          </NuxtLink>
        </div>
        
        <div class="flex items-center space-x-2">
          <NuxtLink 
            to="/watchlist" 
            class="group p-2 rounded-md hover:bg-gray-100 dark:hover:bg-slate-800 text-gray-600 dark:text-slate-400 transition-colors"
            title="追蹤清單"
          >
            <div class="relative w-5 h-5">
              <Icon name="lucide:heart" class="absolute inset-0 w-5 h-5 transition-opacity group-hover:opacity-0" />
              <Icon name="heroicons:heart-20-solid" class="absolute inset-0 w-5 h-5 text-red-500 opacity-0 transition-opacity group-hover:opacity-100" />
            </div>
          </NuxtLink>
          <CommonThemeToggle />
        </div>
      </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-1 w-full">
      <!-- Top Ad (Always show on Default/Inner Layout) -->
      <CommonAdSenseUnit slotKey="top" adFormat="horizontal" class="mb-8" />
      
      <slot />

      <!-- Bottom Ad (Always show on Default/Inner Layout) -->
      <CommonAdSenseUnit slotKey="bottom" adFormat="horizontal" class="mt-8" />
    </main>

    <CommonAppFooter />
    
    <Toaster position="top-right" richColors />
    </div>
  </div>
</template>
