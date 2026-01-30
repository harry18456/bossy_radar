<script setup lang="ts">
import type { Company } from '~/types/api'
import { INDUSTRIES, MARKET_TYPES } from '~/constants'

const props = defineProps<{
  company: Company
}>()

// Helper to map market type value to label
const getMarketTypeLabel = (value: string) => {
  const type = MARKET_TYPES.find(t => t.value === value)
  return type?.label || value
}

// Helper to map industry logic (if it's a code, map it; otherwise show as is)
// Note: Currently API likely returns the name directly, but just in case
const getIndustryLabel = (value: string | null | undefined) => {
  if (!value) return '-'
  // If value is a key in INDUSTRIES (e.g. "01"), return the name
  if (value in INDUSTRIES) {
    return INDUSTRIES[value]
  }
  return value
}

const watchlistStore = useWatchlistStore()
const isWatched = computed(() => watchlistStore.isWatching(props.company.code))

const toggleWatch = (e: Event) => {
  e.preventDefault() // Prevent link navigation
  e.stopPropagation()
  
  watchlistStore.toggleCompany(props.company)
  
  const { $toast } = useNuxtApp()
  if (isWatched.value) {
    $toast.success(`已加入追蹤: ${props.company.name}`)
  } else {
    $toast.info(`已取消追蹤: ${props.company.name}`)
  }
}
</script>

<template>
  <NuxtLink
    :to="`/companies/${company.code}`"
    class="group relative block p-6 bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-xl transition-all duration-300 hover:shadow-lg dark:hover:shadow-slate-900/50 hover:-translate-y-1"
  >
    <div class="flex justify-between items-start mb-4">
      <div>
        <div class="flex items-center space-x-2 mb-1">
          <span class="text-xs font-medium px-2 py-0.5 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300">
            {{ company.code }}
          </span>
          <span 
            v-if="company.market_type"
            class="text-xs font-medium px-2 py-0.5 rounded-full bg-gray-100 dark:bg-slate-800 text-gray-600 dark:text-slate-400"
          >
            {{ getMarketTypeLabel(company.market_type) }}
          </span>
        </div>
        <h3 class="text-lg font-bold text-gray-900 dark:text-slate-50 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
          {{ company.name }}
        </h3>
      </div>
      
      <ClientOnly>
        <button
          @click="toggleWatch"
          class="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-slate-800 transition-colors z-10"
          :class="isWatched ? 'text-red-500' : 'text-gray-400 dark:text-slate-500 hover:text-red-500 dark:hover:text-red-400'"
          aria-label="Toggle watchlist"
        >
          <Icon 
            :name="isWatched ? 'heroicons:heart-20-solid' : 'lucide:heart'" 
            class="w-6 h-6"
            :class="isWatched ? 'text-red-500' : 'text-gray-400 dark:text-slate-500'"
          />
        </button>
      </ClientOnly>
    </div>

    <div class="space-y-2 text-sm text-gray-500 dark:text-slate-400">
      <div class="flex items-center justify-between">
        <span>產業類別</span>
        <span class="font-medium text-gray-900 dark:text-slate-200">{{ getIndustryLabel(company.industry) }}</span>
      </div>
      <div class="flex items-center justify-between">
        <span>資本額</span>
        <span class="font-medium text-gray-900 dark:text-slate-200">
          {{ company.capital ? `$${formatCurrency(Math.floor(company.capital / 1000000))}M` : '-' }}
        </span>

      </div>
      <div class="flex items-center justify-between">
        <span>成立日期</span>
        <span class="font-medium text-gray-900 dark:text-slate-200">
          {{ formatDate(company.establishment_date) }}
        </span>
      </div>
      <div v-if="company.listing_date" class="flex items-center justify-between">
        <span>上市日期</span>
        <span class="font-medium text-gray-900 dark:text-slate-200">
          {{ formatDate(company.listing_date) }}
        </span>
      </div>
    </div>
  </NuxtLink>
</template>
