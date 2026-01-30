<script setup lang="ts">
const colorMode = useColorMode()

const toggleColorMode = () => {
  colorMode.preference = colorMode.value === 'dark' ? 'light' : 'dark'
}
</script>

<template>
  <button
    @click="toggleColorMode"
    class="group p-2 rounded-md transition-all duration-300 hover:bg-gray-100 dark:hover:bg-slate-800 text-gray-500 dark:text-slate-400 hover:text-blue-600 dark:hover:text-yellow-400"
    aria-label="Toggle Dark Mode"
  >
    <ClientOnly>
      <div class="relative w-5 h-5 flex items-center justify-center">
        <!-- Sun Icon (Light Mode) -->
        <Icon 
          v-if="colorMode.value === 'light'"
          name="lucide:sun" 
          class="w-5 h-5 transition-all duration-500 group-hover:rotate-90 group-hover:scale-110" 
        />
        <!-- Moon Icon (Dark Mode) -->
        <Icon 
          v-else
          name="lucide:moon" 
          class="w-5 h-5 transition-all duration-500 group-hover:-rotate-12 group-hover:scale-110" 
        />
      </div>
      <template #fallback>
        <div class="w-5 h-5" />
      </template>
    </ClientOnly>
  </button>
</template>
