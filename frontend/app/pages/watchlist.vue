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
const { data: allComparisonData, status, refresh } = await useAsyncData(
  'watchlist-comparison',
  async () => {
    if (companies.value.length === 0) return []
    
    const codes = companies.value.map(c => c.code)
    
    // Fetch data for these companies
    const response = await api.getYearlySummary({
      company_code: codes,
      include: ['all'] 
    })
    
    // Client-side filter to ensure we ONLY have data for companies currently in the watchlist
    // (useful if the API returns more than requested or if we're using cached data)
    return response.items.filter(item => codes.includes(item.company_code))
  },
  {
    watch: [companies],
    immediate: true
  }
)

// Computed: Available years
const availableYears = computed(() => {
  if (!allComparisonData.value) return []
  const years = new Set(allComparisonData.value.map(item => item.year))
  return Array.from(years).sort((a, b) => b - a)
})

// State: Selected Year
const selectedYear = ref<number | null>(null)

// Set default year when data loads
watch(availableYears, (years) => {
  if (years.length > 0 && !selectedYear.value) {
    selectedYear.value = years[0] ?? null
  }
}, { immediate: true })

const sortedComparison = computed(() => {
  if (!allComparisonData.value || !selectedYear.value) return []
  
  const currentCodes = companies.value.map(c => c.code)
  
  // Filter by selected year AND current watchlist, then sort by code
  return allComparisonData.value
    .filter(item => item.year === selectedYear.value && currentCodes.includes(item.company_code))
    .sort((a, b) => a.company_code.localeCompare(b.company_code))
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
      
      <div v-if="companies.length > 0" class="flex gap-4">
        <button 
          @click="clearWatchlist"
          class="text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 px-4 py-2 rounded-lg transition-colors text-sm font-medium"
        >
          清空清單
        </button>
      </div>
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
          <CompanyCard 
            v-for="company in companies" 
            :key="company.code" 
            :company="company" 
          />
        </div>
      </section>

      <!-- Comparison Section -->
      <section v-if="sortedComparison.length > 0">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-xl font-bold text-gray-900 dark:text-white flex items-center">
            <Icon name="lucide:bar-chart-2" class="w-5 h-5 mr-2" />
            薪資比較 ({{ selectedYear }}年)
          </h2>
          
          <!-- Year Selector -->
          <div class="flex items-center space-x-2">
            <label for="year-select" class="text-sm font-medium text-gray-700 dark:text-slate-300">年份：</label>
            <select 
              id="year-select"
              v-model="selectedYear"
              class="block w-32 rounded-md border-gray-300 dark:border-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm bg-white dark:bg-slate-800 dark:text-white"
            >
              <option v-for="year in availableYears" :key="year" :value="year">
                {{ year }}年
              </option>
            </select>
          </div>
        </div>
        
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
                  勞動違規
                </th>
                <th scope="col" class="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-slate-400 uppercase tracking-wider">
                  環保違規
                </th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200 dark:divide-slate-800">
              <tr v-for="item in sortedComparison" :key="item.company_code" class="hover:bg-gray-50 dark:hover:bg-slate-800/50 transition-colors">
                <td class="px-6 py-4 whitespace-nowrap sticky left-0 bg-white dark:bg-slate-900 group-hover:bg-gray-50 dark:group-hover:bg-slate-800/50">
                  <div class="flex items-center">
                    <div class="text-sm font-medium text-gray-900 dark:text-white">{{ item.company_name }}</div>
                    <div class="ml-2 text-xs text-gray-500 dark:text-slate-400">{{ item.company_code }}</div>
                    <NuxtLink :to="`/companies/${item.company_code}`" class="ml-2 text-blue-500 hover:text-blue-700">
                      <Icon name="lucide:external-link" class="w-3.5 h-3.5" />
                    </NuxtLink>
                  </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium text-green-600 dark:text-green-400">
                  {{ item.non_manager_salary?.avg_salary ? formatCurrency(item.non_manager_salary.avg_salary) : '-' }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium text-yellow-600 dark:text-yellow-400">
                  {{ item.non_manager_salary?.median_salary ? formatCurrency(item.non_manager_salary.median_salary) : '-' }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900 dark:text-white">
                  {{ item.non_manager_salary?.eps ?? '-' }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm" :class="(item.violations_year_count || 0) > 0 ? 'text-red-500 font-bold' : 'text-gray-400'">
                  {{ item.violations_year_count || 0 }}
                  <span v-if="item.violations_total_count" class="text-xs font-normal text-gray-400 ml-1">
                     (累計 {{ item.violations_total_count }})
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm" :class="(item.env_violations_year_count || 0) > 0 ? 'text-red-600 font-bold' : 'text-gray-400'">
                  {{ item.env_violations_year_count || 0 }}
                   <span v-if="item.env_violations_total_count" class="text-xs font-normal text-gray-400 ml-1">
                     (累計 {{ item.env_violations_total_count }})
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <p class="mt-2 text-xs text-gray-500 dark:text-slate-400 text-right">
          * 資料來源：{{ selectedYear }}年度公開資訊 (若無資料顯示為 -)
        </p>
      </section>
      
      <div v-else-if="companies.length > 0 && status !== 'pending'" class="text-center py-12 bg-white dark:bg-slate-900 rounded-xl border border-gray-200 dark:border-slate-800">
          <p class="text-gray-500 dark:text-slate-400">無法取得比較資料，請稍後再試。</p>
      </div>
    </div>
  </div>
</template>
