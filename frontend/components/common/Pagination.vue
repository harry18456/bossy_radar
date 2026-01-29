<script setup lang="ts">
interface Props {
  current: number
  total: number
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'change', page: number): void
}>()

// Calculate visible page range (e.g., current +/- 2)
const visiblePages = computed(() => {
  const delta = 2
  const range: (number | string)[] = []
  const rangeWithDots: (number | string)[] = []
  let l: number | null = null

  for (let i = 1; i <= props.total; i++) {
    if (i === 1 || i === props.total || (i >= props.current - delta && i <= props.current + delta)) {
      range.push(i)
    }
  }

  for (const i of range) {
    if (l) {
      if (typeof i === 'number' && i - l === 2) {
        rangeWithDots.push(l + 1)
      } else if (typeof i === 'number' && i - l !== 1) {
        rangeWithDots.push('...')
      }
    }
    rangeWithDots.push(i)
    l = typeof i === 'number' ? i : null
  }

  return rangeWithDots
})
</script>

<template>
  <nav class="flex items-center justify-center space-x-2" aria-label="Pagination">
    <!-- Previous Button -->
    <button
      @click="emit('change', current - 1)"
      :disabled="current === 1"
      class="p-2 rounded-md border border-gray-300 bg-white text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
      aria-label="Previous page"
    >
      <Icon name="lucide:chevron-left" class="w-5 h-5" />
    </button>

    <!-- Page Numbers -->
    <template v-for="(page, index) in visiblePages" :key="index">
      <span v-if="page === '...'" class="px-4 py-2 text-gray-400">...</span>
      <button
        v-else
        @click="emit('change', page as number)"
        :class="[
          'px-4 py-2 rounded-md border text-sm font-medium transition-colors',
          current === page
            ? 'bg-blue-600 text-white border-blue-600'
            : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
        ]"
      >
        {{ page }}
      </button>
    </template>

    <!-- Next Button -->
    <button
      @click="emit('change', current + 1)"
      :disabled="current === total"
      class="p-2 rounded-md border border-gray-300 bg-white text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
      aria-label="Next page"
    >
      <Icon name="lucide:chevron-right" class="w-5 h-5" />
    </button>
  </nav>
</template>
