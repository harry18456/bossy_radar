<script setup lang="ts">
import { useTransition, TransitionPresets } from '@vueuse/core'

const props = defineProps<{
  value: number
  duration?: number
}>()

const source = ref(0)
const output = useTransition(source, {
  duration: props.duration ?? 1500,
  transition: TransitionPresets.easeOutExpo,
})

// Update source when prop changes, or on mount
watch(() => props.value, (n) => {
  source.value = n
}, { immediate: true })

const formatted = computed(() => {
  // Round to integer for display
  const val = Math.round(output.value)
  return new Intl.NumberFormat('en-US').format(val)
})
</script>

<template>
  <span>{{ formatted }}</span>
</template>
