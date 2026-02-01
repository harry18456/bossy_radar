<script setup lang="ts">
import { Toaster } from "vue-sonner";
</script>

<template>
  <div
    class="min-h-screen flex flex-col bg-gray-50 dark:bg-slate-950 text-gray-900 dark:text-slate-50 transition-colors duration-300 relative"
  >
    <HomeBackground />
    <div class="relative z-10 flex flex-col min-h-screen">
      <!-- Header -->
      <!-- Header -->
      <CommonAppHeader />

      <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-1 w-full">
        <!-- Top Ad (Always show on Default/Inner Layout) -->
        <CommonAdSenseUnit slotKey="top" adFormat="horizontal" class="mb-8" />

        <slot />

        <!-- Bottom Ad (Always show on Default/Inner Layout) -->
        <CommonAdSenseUnit
          slotKey="bottom"
          adFormat="horizontal"
          class="mt-8"
        />
      </main>

      <CommonAppFooter />

      <Toaster position="top-right" richColors />
    </div>
  </div>
</template>
