<script setup lang="ts">
import { useApi } from '~/composables/useApi'
import { useCompanyFilters } from '~/composables/useCompanyFilters'

usePageMeta({
  title: '搜尋公司',
  description: '查詢台灣上市櫃公司薪資福利與違規紀錄，透明化職場資訊。'
})

const {
  filters,
  name,
  sort,
  page,
  updateFilter,
  resetFilters
} = useCompanyFilters()

const api = useApi()

// Computed parameters for API to ensure reactivity is tracked precisely
const queryParams = computed(() => ({
  industry: [...(filters.industry || [])],
  market_type: [...(filters.market_type || [])],
  name: name.value,
  sort: sort.value,
  page: page.value,
  limit: 12
}))

// Use useAsyncData with specific watcher on the computed params
// Key includes stringified params to ensure unique caching/hydration and force update
const { data, status, error, refresh } = await useAsyncData(
  () => `companies-list-${JSON.stringify(queryParams.value)}`,
  () => api.getCompanies(queryParams.value),
  {
    watch: [queryParams],
    deep: true
  }
)

const companies = computed(() => data.value?.items || [])
const total = computed(() => data.value?.total || 0)
const totalPages = computed(() => data.value?.total_pages || 1)

// Handle page change
const handlePageChange = (newPage: number) => {
  page.value = newPage
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

// Sidebar open state for mobile
const isSidebarOpen = ref(false)
</script>

<template>
  <div class="container mx-auto px-4 py-8">
    <div class="flex flex-col lg:flex-row gap-8">
      <!-- Mobile Filter Toggle -->
      <button 
        @click="isSidebarOpen = !isSidebarOpen"
        class="lg:hidden flex items-center justify-center w-full py-3 bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-lg shadow-sm font-medium text-gray-700 dark:text-slate-200"
      >
        <Icon name="lucide:filter" class="w-5 h-5 mr-2" />
        {{ isSidebarOpen ? '收合篩選' : '顯示篩選條件' }}
      </button>

      <!-- Sidebar (Filters) -->
      <aside 
        class="lg:w-1/4 flex-shrink-0 transition-all duration-300"
        :class="[isSidebarOpen ? 'block' : 'hidden lg:block']"
      >
        <div class="lg:sticky lg:top-8 space-y-6">
          <CompanyFilterBar 
            v-model:search="name"
            :filters="filters"
            @update:filter="updateFilter"
            @reset="resetFilters"
          />
        </div>
      </aside>

      <!-- Main Content -->
      <main class="lg:w-3/4 flex-grow">
        <!-- Results Header & Sort -->
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4">
          <h1 class="text-xl font-bold text-gray-900 dark:text-white">
            搜尋結果
            <span class="ml-2 text-sm font-normal text-gray-500 dark:text-slate-400">
              (共 {{ total }} 筆)
            </span>
          </h1>

          <div class="flex items-center space-x-2">
            <label for="sort" class="text-sm font-medium text-gray-700 dark:text-slate-300">排序：</label>
            <select 
              id="sort" 
              v-model="sort"
              class="form-select text-sm border-gray-300 dark:border-slate-700 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-slate-900 text-gray-900 dark:text-white"
            >
              <option value="">預設排序</option>
              <option value="-capital">資本額 (高到低)</option>
              <option value="capital">資本額 (低到高)</option>
              <option value="-listing_date">上市日期 (新到舊)</option>
              <option value="listing_date">上市日期 (舊到新)</option>
              <option value="-establishment_date">成立日期 (新到舊)</option>
              <option value="establishment_date">成立日期 (舊到新)</option>
            </select>
          </div>
        </div>

        <!-- Loading State -->
        <div v-if="status === 'pending'" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div v-for="n in 6" :key="n" class="bg-white dark:bg-slate-900 rounded-xl p-6 border border-gray-200 dark:border-slate-800 shadow-sm animate-pulse h-48"></div>
        </div>

        <!-- Error State -->
        <div v-else-if="error" class="text-center py-12 bg-red-50 dark:bg-red-900/10 rounded-xl border border-red-100 dark:border-red-900/30">
          <p class="text-red-600 dark:text-red-400 mb-2">發生錯誤，無法載入資料</p>
          <button 
            @click="refresh()" 
            class="text-sm font-medium text-blue-600 dark:text-blue-400 hover:underline"
          >
            重試
          </button>
        </div>

        <!-- Empty State -->
        <div v-else-if="companies.length === 0" class="text-center py-24 bg-white dark:bg-slate-900 rounded-xl border border-gray-200 dark:border-slate-800 border-dashed">
          <Icon name="lucide:search-x" class="w-16 h-16 text-gray-300 dark:text-slate-600 mx-auto mb-4" />
          <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">找不到符合的公司</h3>
          <p class="text-gray-500 dark:text-slate-400 mb-6">請嘗試調整篩選條件或關鍵字</p>
          <button 
            @click="resetFilters"
            class="px-4 py-2 bg-gray-100 dark:bg-slate-800 text-gray-700 dark:text-slate-300 rounded-lg hover:bg-gray-200 dark:hover:bg-slate-700 transition-colors"
          >
            清除所有篩選
          </button>
        </div>

        <!-- Data Grid -->
        <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6 mb-8">
          <CompanyCard 
            v-for="company in companies" 
            :key="company.code" 
            :company="company" 
          />
        </div>

        <!-- Pagination -->
        <div v-if="totalPages > 1" class="flex justify-center mt-8">
          <CommonPagination 
            :current="page" 
            :total="totalPages" 
            @change="handlePageChange" 
          />
        </div>
      </main>
    </div>
  </div>
</template>
