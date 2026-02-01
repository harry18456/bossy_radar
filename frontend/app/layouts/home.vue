<script setup lang="ts">
import { Toaster } from 'vue-sonner'

// Home Layout: Pure layout without any AdSense logic or placeholders.
// This ensures separate logic from content pages.
</script>

<template>
  <div class="min-h-screen flex flex-col bg-gray-50 dark:bg-slate-950 text-gray-900 dark:text-slate-50 transition-colors duration-300 relative">
    <HomeBackground />
    <div class="relative z-10 flex flex-col min-h-screen">
    <!-- Header -->
    <!-- Header -->
    <CommonAppHeader />

    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-1 w-full">
      <!-- No Ads here -->
      <slot />
      <!-- No Ads here -->
    </main>

    <CommonAppFooter />
    
    <Toaster position="top-right" richColors />
    </div>
  </div>
</template>
