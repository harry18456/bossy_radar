<script setup lang="ts">
import { useApi } from '~/composables/useApi'
import { useWatchlistStore } from '~/stores/watchlist'
import type { YearlySummaryItem } from '~/types/api'

usePageMeta({
  title: '追蹤清單',
  description: '您追蹤的公司列表與薪資比較。'
})

const watchlistStore = useWatchlistStore()
const api = useApi()

// Get watched companies
const companies = computed(() => watchlistStore.companies)

// Comparison Data
// We only fetch when there are companies to watch
const { data: comparisonData, status, refresh } = await useAsyncData(
  'watchlist-comparison',
  async () => {
    if (companies.value.length === 0) return []
    
    // Get latest year summary for these companies
    const codes = companies.value.map(c => c.code)
    // We assume we want the latest data, let's try getting data without year filter first to see what we get,
    // or better, typically we want the last 3 years? Or just one. 
    // Let's get "last available year". Since API needs year or returns all, we can ask for specific recent years if needed.
    // However, getYearlySummary returns a list.
    
    // Strategy: Fetch all data for these companies, then we find the latest year common to them or just show latest for each.
    // To optimization, maybe just fetch? The API might return a lot if we don't filter year.
    // Let's try fetching 112 (2023) and 111 (2022) as default recent years often available.
    // Or just 112 (2023). Let's hardcode 112 for now or make it selectable in future.
    // Actually, let's fetch without year filter but specific companies, it shouldn't be too huge if watchlist is small.
    // But safely, let's filter year=112 (2023).
    const recentYear = 112
    
    const response = await api.getYearlySummary({
      company_code: codes,
      year: [recentYear], 
      include: ['all'] // Get everything for comparison
    })
    
    return response.items
  },
  {
    watch: [companies], // Refetch if watchlist changes
    immediate: true
  }
)

const sortedComparison = computed(() => {
  if (!comparisonData.value) return []
  // Sort by code
  return [...comparisonData.value].sort((a, b) => a.company_code.localeCompare(b.company_code))
})

const clearWatchlist = () => {
  if (confirm('確定要清空所有追蹤清單嗎？')) {
    watchlistStore.$reset()
  }
}
</script>

<template>
  <div class="space-y-12">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white mb-2">我的追蹤清單</h1>
        <p class="text-gray-500 dark:text-slate-400">
          共追蹤 {{ companies.length }} 間公司
        </p>
      </div>
      
      <button 
        v-if="companies.length > 0"
        @click="clearWatchlist"
        class="text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 px-4 py-2 rounded-lg transition-colors text-sm font-medium"
      >
        清空清單
      </button>
    </div>

    <!-- Empty State -->
    <div v-if="companies.length === 0" class="text-center py-24 bg-white dark:bg-slate-900 rounded-xl border border-gray-200 dark:border-slate-800 border-dashed">
      <Icon name="lucide:heart-off" class="w-16 h-16 text-gray-300 dark:text-slate-600 mx-auto mb-4" />
      <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">清單是空的</h3>
      <p class="text-gray-500 dark:text-slate-400 mb-6">快去搜尋並加入感興趣的公司吧！</p>
      <NuxtLink 
        to="/companies"
        class="inline-flex items-center px-6 py-3 rounded-lg bg-blue-600 hover:bg-blue-700 text-white transition-colors"
      >
        前往搜尋
        <Icon name="lucide:arrow-right" class="w-4 h-4 ml-2" />
      </NuxtLink>
    </div>

    <div v-else class="space-y-12">
      <!-- Grid View -->
      <section>
        <h2 class="text-xl font-bold text-gray-900 dark:text-white mb-6 flex items-center">
          <Icon name="lucide:grid" class="w-5 h-5 mr-2" />
          公司列表
        </h2>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <CompanyCompanyCard 
            v-for="company in companies" 
            :key="company.code" 
            :company="company" 
          />
        </div>
      </section>

      <!-- Comparison Section -->
      <section v-if="comparisonData && comparisonData.length > 0">
        <h2 class="text-xl font-bold text-gray-900 dark:text-white mb-6 flex items-center">
          <Icon name="lucide:bar-chart-2" class="w-5 h-5 mr-2" />
          薪資比較 (112年)
        </h2>
        
        <div class="overflow-x-auto bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-xl shadow-sm">
          <table class="min-w-full divide-y divide-gray-200 dark:divide-slate-800">
            <thead class="bg-gray-50 dark:bg-slate-800">
              <tr>
                <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-slate-400 uppercase tracking-wider sticky left-0 bg-gray-50 dark:bg-slate-800 z-10">
                  公司名稱
                </th>
                <th scope="col" class="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-slate-400 uppercase tracking-wider">
                  非主管平均薪資
                </th>
                <th scope="col" class="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-slate-400 uppercase tracking-wider">
                  非主管中位數
                </th>
                <th scope="col" class="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-slate-400 uppercase tracking-wider">
                  EPS
                </th>
                <th scope="col" class="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-slate-400 uppercase tracking-wider">
                  違規次數
                </th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200 dark:divide-slate-800">
              <tr v-for="item in sortedComparison" :key="item.company_code" class="hover:bg-gray-50 dark:hover:bg-slate-800/50 transition-colors">
                <td class="px-6 py-4 whitespace-nowrap sticky left-0 bg-white dark:bg-slate-900 group-hover:bg-gray-50 dark:group-hover:bg-slate-800/50">
                  <div class="flex items-center">
                    <div class="text-sm font-medium text-gray-900 dark:text-white">{{ item.company_name }}</div>
                    <div class="ml-2 text-xs text-gray-500 dark:text-slate-400">{{ item.company_code }}</div>
                  </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium text-green-600 dark:text-green-400">
                  {{ formatCurrency(item.avg_salary_non_manager) }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium text-yellow-600 dark:text-yellow-400">
                  {{ formatCurrency(item.median_salary_non_manager) }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900 dark:text-white">
                  {{ item.eps }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm" :class="item.violation_count > 0 ? 'text-red-500 font-bold' : 'text-gray-400'">
                  {{ item.violation_count }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <p class="mt-2 text-xs text-gray-500 dark:text-slate-400 text-right">
          * 資料來源：112年度財報 (若無資料顯示為 0 或 -)
        </p>
      </section>
    </div>
  </div>
</template>
