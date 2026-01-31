<script setup lang="ts">
import { INDUSTRY_OPTIONS, MARKET_TYPES } from '~/constants'
import type { CompanyFilters } from '~/composables/useCompanyFilters'

const props = defineProps<{
  filters: CompanyFilters
}>()

const isExpanded = ref(true)

// Local state for search to prevent live query
const localSearchName = ref(props.filters.name || '')
watch(() => props.filters.name, (newVal) => {
  localSearchName.value = newVal || ''
})

const handleSearch = (val: string) => {
  props.filters.name = val
}

// Helper for multi-select checkboxes
const toggleIndustry = (value: string) => {
  if (!props.filters.industry) props.filters.industry = []
  const index = props.filters.industry.indexOf(value)
  if (index === -1) {
    props.filters.industry.push(value)
  } else {
    props.filters.industry.splice(index, 1)
  }
}

const toggleMarket = (value: string) => {
  if (!props.filters.market_type) props.filters.market_type = []
  const index = props.filters.market_type.indexOf(value)
  if (index === -1) {
    props.filters.market_type.push(value)
  } else {
    props.filters.market_type.splice(index, 1)
  }
}
</script>

<template>
  <div class="space-y-8">
    <!-- Search Input (Autocomplete) -->
    <div>
      <div class="flex items-center justify-between mb-2">
        <label for="search" class="block text-sm font-medium text-gray-700 dark:text-slate-300">關鍵字搜尋</label>
        <button 
          v-if="localSearchName || filters.name"
          @click="() => { localSearchName = ''; filters.name = '' }"
          class="text-xs text-gray-500 hover:text-red-500 transition-colors"
        >
          清空
        </button>
      </div>
      <div class="relative group">
        <CompanyAutocomplete 
          v-model="localSearchName"
          :industry-filter="filters.industry"
          :market-filter="filters.market_type"
          @search="handleSearch"
        />
        <button 
          @click="handleSearch(localSearchName)"
          class="absolute right-3 top-2.5 p-1 rounded-md text-gray-400 hover:text-blue-500 hover:bg-gray-100 dark:hover:bg-slate-800 transition-all"
          title="執行搜尋"
        >
          <Icon name="lucide:arrow-right" class="w-4 h-4" />
        </button>
      </div>
    </div>

    <!-- Market Type Filter -->
    <div>
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-sm font-semibold text-gray-900 dark:text-white">市場類別</h3>
        <button 
          v-if="(filters.market_type?.length || 0) > 0"
          @click="filters.market_type = []"
          class="text-xs text-gray-500 hover:text-red-500 transition-colors"
        >
          清空
        </button>
      </div>
      <div class="space-y-2">
        <label 
          v-for="type in MARKET_TYPES" 
          :key="type.value"
          class="flex items-center space-x-2 cursor-pointer group"
        >
          <input 
            type="checkbox" 
            :value="type.value" 
            :checked="filters.market_type?.includes(type.value)"
            @change="toggleMarket(type.value)"
            class="w-4 h-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500 dark:bg-slate-900 dark:border-slate-700"
          />
          <span class="text-sm text-gray-600 dark:text-slate-400 group-hover:text-gray-900 dark:group-hover:text-white transition-colors">
            {{ type.label }}
          </span>
        </label>
      </div>
    </div>

    <!-- Industry Filter -->
    <div>
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-sm font-semibold text-gray-900 dark:text-white">產業類別</h3>
        <div class="flex items-center space-x-3">
          <button 
            v-if="(filters.industry?.length || 0) > 0"
            @click="filters.industry = []"
            class="text-xs text-gray-500 hover:text-red-500 transition-colors"
          >
            清空
          </button>
          <button 
            @click="isExpanded = !isExpanded"
            class="text-xs text-blue-600 dark:text-blue-400 hover:underline"
          >
            {{ isExpanded ? '收合' : '展開' }}
          </button>
        </div>
      </div>
      
      <div 
        class="space-y-2 pr-2 custom-scrollbar transition-all duration-300 ease-in-out overflow-hidden"
        :class="isExpanded ? 'max-h-[60vh] overflow-y-auto mt-4' : 'max-h-0'"
      >
        <label 
          v-for="option in INDUSTRY_OPTIONS" 
          :key="option.value"
          class="flex items-center space-x-2 cursor-pointer group"
        >
          <input 
            type="checkbox" 
            :value="option.value" 
            :checked="filters.industry?.includes(option.value)"
            @change="toggleIndustry(option.value)"
            class="w-4 h-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500 dark:bg-slate-900 dark:border-slate-700"
          />
          <span class="text-sm text-gray-600 dark:text-slate-400 group-hover:text-gray-900 dark:group-hover:text-white transition-colors">
            {{ option.label }}
          </span>
        </label>
      </div>
    </div>
  </div>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: #cbd5e1;
  border-radius: 4px;
}
.dark .custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: #475569;
}
</style>
