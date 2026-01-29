<script setup lang="ts">
import { Toaster } from 'vue-sonner'
</script>

<template>
  <div class="min-h-screen bg-gray-50 text-gray-900">
    <slot />
    <Toaster position="top-right" richColors />
  </div>
</template>
