<script setup lang="ts">
import { useCompanyStore } from '~/stores/company'
import type { CompanyCatalog } from '~/types/api'
import { onClickOutside } from '@vueuse/core'
import { INDUSTRIES, MARKET_TYPES } from '~/constants'

const props = defineProps<{
  modelValue: string | null | undefined
  industryFilter?: string[]
  marketFilter?: string[]
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
  (e: 'select', company: CompanyCatalog): void
  (e: 'search', value: string): void
}>()

const companyStore = useCompanyStore()
const isOpen = ref(false)
const inputRef = ref<HTMLInputElement | null>(null)
const selectedIndex = ref(-1)

// Initialize catalog on mount
onMounted(() => {
  companyStore.fetchCatalog()
})

const getMarketLabel = (type: string) => {
  return MARKET_TYPES.find(m => m.value === type)?.label || type
}

const getIndustryLabel = (code: string | null | undefined) => {
  if (!code) return ''
  return INDUSTRIES[code] || code
}

const query = computed({
  get: () => props.modelValue || '',
  set: (val) => emit('update:modelValue', val)
})

const suggestions = computed(() => {
  if (!query.value || query.value.length < 1) return []
  
  const q = query.value.toLowerCase()
  return companyStore.catalog
    .filter(c => {
      // Basic text search match
      const isMatch = c.code.includes(q) || 
                      c.name.toLowerCase().includes(q) || 
                      (c.abbreviation && c.abbreviation.toLowerCase().includes(q))
      
      if (!isMatch) return false

      // Filter by market_type if selected
      if (props.marketFilter && props.marketFilter.length > 0) {
        if (!props.marketFilter.includes(c.market_type)) return false
      }

      // Filter by industry if selected
      if (props.industryFilter && props.industryFilter.length > 0) {
        if (!c.industry || !props.industryFilter.includes(c.industry)) return false
      }

      return true
    })
    .sort((a, b) => {
      // Priority 1: Exact code match
      if (a.code === q) return -1
      if (b.code === q) return 1
      
      // Priority 2: Starts with code
      if (a.code.startsWith(q) && !b.code.startsWith(q)) return -1
      if (!a.code.startsWith(q) && b.code.startsWith(q)) return 1
      
      // Priority 3: Starts with name/abbreviation
      const aStarts = a.name.startsWith(q) || (a.abbreviation && a.abbreviation.startsWith(q))
      const bStarts = b.name.startsWith(q) || (b.abbreviation && b.abbreviation.startsWith(q))
      if (aStarts && !bStarts) return -1
      if (!aStarts && bStarts) return 1
      
      return 0
    })
    .slice(0, 10) // Limit to 10 results for performance
})

const isSelecting = ref(false)

const selectCompany = (company: CompanyCatalog) => {
  isSelecting.value = true
  emit('update:modelValue', company.name)
  emit('select', company)
  emit('search', company.name)
  isOpen.value = false
  selectedIndex.value = -1
  // Reset flag after a tick to allow future typing to open suggestions
  nextTick(() => {
    isSelecting.value = false
  })
}

const handleKeyDown = (e: KeyboardEvent) => {
  if (e.key === 'Enter') {
    e.preventDefault()
    if (isOpen.value && selectedIndex.value >= 0 && suggestions.value[selectedIndex.value]) {
      selectCompany(suggestions.value[selectedIndex.value] as CompanyCatalog)
    } else if (isOpen.value && suggestions.value.length > 0 && suggestions.value[0]) {
      selectCompany(suggestions.value[0] as CompanyCatalog)
    } else {
      emit('search', query.value)
      isOpen.value = false
    }
    return
  }

  if (!isOpen.value) {
    if (e.key === 'ArrowDown' && suggestions.value.length > 0) {
      isOpen.value = true
    }
    return
  }

  switch (e.key) {
    case 'ArrowDown':
      e.preventDefault()
      selectedIndex.value = (selectedIndex.value + 1) % suggestions.value.length
      break
    case 'ArrowUp':
      e.preventDefault()
      selectedIndex.value = (selectedIndex.value - 1 + suggestions.value.length) % suggestions.value.length
      break
    case 'Escape':
      isOpen.value = false
      selectedIndex.value = -1
      break
  }
}

// Close when clicking outside
const containerRef = ref<HTMLElement | null>(null)
onClickOutside(containerRef, () => {
  isOpen.value = false
})

watch(query, () => {
  if (isSelecting.value) return
  
  if (query.value.length >= 1) {
    isOpen.value = true
    selectedIndex.value = -1
  } else {
    isOpen.value = false
  }
})
</script>

<template>
  <div ref="containerRef" class="relative">
    <div class="relative">
      <input
        ref="inputRef"
        v-model="query"
        type="text"
        placeholder="搜尋公司代號或名稱..."
        class="w-full pl-10 pr-4 py-2 bg-white dark:bg-slate-900 border border-gray-300 dark:border-slate-700 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:text-white transition-all"
        @keydown="handleKeyDown"
        @focus="isOpen = query.length >= 1"
      />
      <Icon name="lucide:search" class="absolute left-3 top-2.5 w-5 h-5 text-gray-400" />
      
      <!-- Loading indicator -->
      <div v-if="companyStore.isLoading" class="absolute right-3 top-2.5">
        <Icon name="lucide:loader-2" class="w-5 h-5 text-blue-500 animate-spin" />
      </div>
    </div>

    <!-- Autocomplete Dropdown -->
    <Transition
      enter-active-class="transition duration-100 ease-out"
      enter-from-class="transform scale-95 opacity-0"
      enter-to-class="transform scale-100 opacity-100"
      leave-active-class="transition duration-75 ease-in"
      leave-from-class="transform scale-100 opacity-100"
      leave-to-class="transform scale-95 opacity-0"
    >
      <div
        v-if="isOpen && suggestions.length > 0"
        class="absolute z-50 w-full mt-1 bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-lg shadow-xl max-h-80 overflow-y-auto custom-scrollbar"
      >
        <ul class="py-1">
          <li
            v-for="(company, index) in suggestions"
            :key="company.code"
            @click="selectCompany(company)"
            @mouseenter="selectedIndex = index"
            class="px-4 py-3 cursor-pointer transition-colors flex items-center justify-between"
            :class="[
              selectedIndex === index ? 'bg-blue-50 dark:bg-blue-900/20' : ''
            ]"
          >
            <div class="flex flex-col">
              <span class="text-sm font-bold text-gray-900 dark:text-white">
                {{ company.name }}
              </span>
              <span class="text-xs text-gray-500 dark:text-slate-400">
                {{ company.abbreviation || company.name }}
              </span>
            </div>
            <div class="flex items-center space-x-2">
              <span class="text-[10px] px-1.5 py-0.5 rounded border border-blue-200 dark:border-blue-900/30 text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/10">
                {{ getMarketLabel(company.market_type) }}
              </span>
              <span v-if="company.industry" class="text-[10px] px-1.5 py-0.5 rounded border border-teal-200 dark:border-teal-900/30 text-teal-600 dark:text-teal-400 bg-teal-50 dark:bg-teal-900/10">
                {{ getIndustryLabel(company.industry) }}
              </span>
              <span class="text-xs font-mono font-medium px-2 py-0.5 rounded bg-gray-100 dark:bg-slate-800 text-gray-600 dark:text-slate-400">
                {{ company.code }}
              </span>
            </div>
          </li>
        </ul>
      </div>
    </Transition>
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
