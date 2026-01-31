<script setup lang="ts">
import { Toaster } from 'vue-sonner'

const route = useRoute()

// Fix: AdSense Auto Ads (Anchor) assigns padding to body. 
// When causing SPA navigation to Home (no ads), this padding remains, leaving blank space.
// We force remove it when entering Home.
watch(() => route.path, (newPath) => {
  if (newPath === '/' && import.meta.client) {
    // Small delay to ensure AdSense script doesn't re-apply it immediately if it was racing
    setTimeout(() => {
      document.body.style.removeProperty('padding-bottom')
      document.body.style.removeProperty('padding-top')
      // Optional: Hide any auto-placed ads container if standard logic doesn't catch them
      const autoAds = document.getElementsByClassName('google-auto-placed')
      for (const ad of autoAds) {
        (ad as HTMLElement).style.display = 'none'
      }
    }, 100)
  }
})
</script>


<template>
  <div class="min-h-screen flex flex-col bg-gray-50 dark:bg-slate-950 text-gray-900 dark:text-slate-50 transition-colors duration-300">
    <!-- Header -->
    <header class="border-b border-gray-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md sticky top-0 z-50">
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
      <!-- Top Ad -->
      <CommonAdSenseUnit v-if="route.path !== '/'" slotKey="top" adFormat="horizontal" class="mb-8" />
      
      <slot />

      <!-- Bottom Ad -->
      <CommonAdSenseUnit v-if="route.path !== '/'" slotKey="bottom" adFormat="horizontal" class="mt-8" />
    </main>

    <CommonAppFooter />
    
    <Toaster position="top-right" richColors />
  </div>
</template>
