<script setup lang="ts">
import { useIntersectionObserver } from '@vueuse/core'

const props = defineProps<{
  adSlot?: string,
  adFormat?: string,
  adLayoutKey?: string,
  slotKey?: 'top' | 'bottom'
}>()

const config = useRuntimeConfig()
// Get Client ID from runtime config
const adClient = config.public.googleAdSense?.id
// Resolve slot ID: prioritize slotKey (from config), fallback to adSlot prop
const currentAdSlot = computed(() => {
  if (props.slotKey && config.public.googleAdSense?.slots?.[props.slotKey]) {
    return config.public.googleAdSense.slots[props.slotKey]
  }
  return props.adSlot
})

const isDev = import.meta.dev

const adElement = ref<HTMLElement | null>(null)

onMounted(() => {
  if (!isDev && adClient) {
    let retryCount = 0
    const maxRetries = 5
    
    const pushAd = () => {
      // Ensure element exists and hasn't been pushed yet
      if (adElement.value && !adElement.value.getAttribute('data-adsbygoogle-status')) {
        try {
          // Check visibility (offsetParent is null if display:none) and width
          if (adElement.value.offsetParent === null || adElement.value.offsetWidth === 0) {
            console.warn(`[AdSense] Ad container hidden or 0 width (Attempt ${retryCount + 1}/${maxRetries}). Retrying...`)
            if (retryCount < maxRetries) {
              retryCount++
              setTimeout(pushAd, 500)
              return
            }
            return
          }

          // @ts-ignore
          (window.adsbygoogle = window.adsbygoogle || []).push({});
        } catch (e: any) {
          // Ignore "All 'ins' elements..." error (already loaded)
          if (e?.message?.includes('All \'ins\' elements')) {
             // pass
          } else {
            console.error('[AdSense] Unexpected error:', e);
          }
        }
      }
    }

    // Lazy load using Intersection Observer
    const { stop } = useIntersectionObserver(
      adElement,
      async ([{ isIntersecting }]) => {
        if (isIntersecting) {
          stop()
          await nextTick()
          requestAnimationFrame(() => {
            pushAd()
          })
        }
      },
      {
        rootMargin: '200px' // Load when ad is 200px away from viewport
      }
    )
  }
})
</script>

<template>
  <!-- Ad Container: Prevents CLS -->
  <div class="ad-unit w-full my-6 overflow-hidden bg-gray-50 dark:bg-slate-800/50 rounded-lg text-center flex items-center justify-center border border-dashed border-gray-200 dark:border-slate-700/50" style="min-height: 100px;">
    
    <!-- Dev / No Client ID Placeholder -->
    <div v-if="isDev || !adClient" class="text-xs text-gray-400 p-4 text-center">
      <p class="font-bold mb-1">Google AdSense</p>
      <p class="text-[10px]">(Ads will appear here in production)</p>
      <p v-if="!adClient" class="text-[10px] text-red-400 mt-1">Missing Client ID</p>
    </div>
    
    <!-- Production Ad Code -->
    <ClientOnly v-else>
      <ins ref="adElement"
           class="adsbygoogle"
           style="display:block; width: 100%; min-height: 100px; text-align: center;"
           :data-ad-client="adClient"
           :data-ad-slot="currentAdSlot"
           :data-ad-format="adFormat || 'auto'"
           :data-full-width-responsive="true"
           :data-ad-layout-key="adLayoutKey"></ins>
    </ClientOnly>
  </div>
</template>

<style scoped>
.ad-unit {
  min-height: 100px;
}
</style>
