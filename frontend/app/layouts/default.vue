<script setup lang="ts">
import { Toaster } from 'vue-sonner'

const route = useRoute()

// Fix: AdSense Auto Ads (Anchor) assigns padding to body. 
// When causing SPA navigation to Home (no ads), this padding remains, leaving blank space.
// We force remove it when entering Home.
watch(() => route.path, (newPath) => {
  if (newPath === '/' && import.meta.client) {
    // Aggressive cleanup for AdSense "Auto Ads" residues
    const cleanup = () => {
      // Safety check: Stop if we navigated away from Home
      if (route.path !== '/') return

       // 1. Remove padding/margin from body AND html
      document.body.style.removeProperty('padding-bottom')
      document.body.style.removeProperty('padding-top')
      document.body.style.removeProperty('margin-bottom')
      document.documentElement.style.removeProperty('padding-bottom')
      document.documentElement.style.removeProperty('margin-bottom')
      document.documentElement.style.removeProperty('height') // Reset if modified

      // 2. Hide specific AdSense containers that might be "invisible" but taking space
      // Only target auto-ads, NOT manually placed units (which have specific IDs usually)
      const adContainers = document.querySelectorAll('.google-auto-placed, .adsbygoogle-noablate')
      adContainers.forEach((el) => {
        (el as HTMLElement).style.display = 'none';
        (el as HTMLElement).style.height = '0';
        (el as HTMLElement).style.overflow = 'hidden';
      })
      
      // 3. Reset __nuxt height if forced
      const nuxtApp = document.getElementById('__nuxt')
      if (nuxtApp) {
         nuxtApp.style.removeProperty('height')
         nuxtApp.style.height = '100%' // Force it back to full height
      }
    }

    // Run immediately and repeatedly for a few seconds to fight race conditions
    cleanup()
    const interval = setInterval(() => {
      if (route.path !== '/') {
        clearInterval(interval)
        return
      }
      cleanup()
    }, 200)
    
    // Stop eventually
    setTimeout(() => clearInterval(interval), 2000)
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
