<script setup lang="ts">
import { useApi } from '~/composables/useApi'
import { INDUSTRIES } from '~/constants'

const getIndustryLabel = (code: string | null | undefined) => {
  if (!code) return '-'
  return INDUSTRIES[code] || code
}

const route = useRoute()
const api = useApi()
const id = route.params.id as string

const { data: profile, status, error } = await useAsyncData(
  `company-${id}`,
  () => api.getCompanyProfile(id)
)

const company = computed(() => profile.value?.company)

usePageMeta({
  title: company.value?.name || '公司詳情',
  description: company.value ? `${company.value.name} (${company.value.code}) 的薪資福利與違規紀錄。` : undefined
})

const activeTab = ref<'overview' | 'stats' | 'violations' | 'welfare'>('overview')
const violationType = ref<'labor' | 'env'>('labor')

const tabs = [
  { id: 'overview', label: '基本資料' },
  { id: 'stats', label: '薪資趨勢' },
  { id: 'violations', label: '違規紀錄' },
  { id: 'welfare', label: '員工福利' },
] as const

// Watchlist Logic
const watchlistStore = useWatchlistStore()
// Ensure company object is loaded before checking
const isWatched = computed(() => company.value ? watchlistStore.isWatching(company.value.code) : false)

const toggleWatch = () => {
  if (!company.value) return
  watchlistStore.toggleCompany(company.value)
  const { $toast } = useNuxtApp()
  if (isWatched.value) {
    $toast.success(`已加入追蹤: ${company.value.name}`)
  } else {
    $toast.info(`已取消追蹤: ${company.value.name}`)
  }
}
</script>

<template>
  <div>
    <!-- Loading State -->
    <div v-if="status === 'pending'" class="animate-pulse space-y-8">
      <div class="h-32 bg-gray-200 dark:bg-slate-800 rounded-xl"></div>
      <div class="h-64 bg-gray-200 dark:bg-slate-800 rounded-xl"></div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="text-center py-20">
      <Icon name="lucide:alert-triangle" class="w-16 h-16 text-red-500 mx-auto mb-4" />
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white mb-2">找不到此公司資料</h1>
      <p class="text-gray-500 dark:text-slate-400 mb-6">請確認公司代號是否正確</p>
      <NuxtLink 
        to="/"
        class="text-blue-600 dark:text-blue-400 hover:underline"
      >
        回首頁
      </NuxtLink>
    </div>

    <!-- Main Content -->
    <div v-else-if="profile && company" class="space-y-8">
      <!-- Header -->
      <div class="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-xl p-4 md:p-8 shadow-sm relative overflow-hidden">
        <!-- Decoration background -->
        <div class="absolute top-0 right-0 w-64 h-64 bg-blue-50 dark:bg-blue-900/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2"></div>

        <div class="relative z-10 flex flex-col md:flex-row md:items-start justify-between gap-6">
          <div>
            <div class="flex items-center space-x-3 mb-2">
              <span class="text-2xl font-bold text-gray-900 dark:text-white">{{ company.name }}</span>
              <span class="text-sm font-medium px-2.5 py-0.5 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300">
                {{ company.code }}
              </span>
            </div>
            <div class="flex flex-wrap items-center gap-4 text-sm text-gray-500 dark:text-slate-400">
              <span class="flex items-center">
                <Icon name="lucide:building-2" class="w-4 h-4 mr-1" />
                {{ getIndustryLabel(company.industry) }}
              </span>
              <span class="flex items-center">
                <Icon name="lucide:map-pin" class="w-4 h-4 mr-1" />
                {{ company.address || '無地址資訊' }}
              </span>
              <a 
                v-if="company.website"
                :href="company.website" 
                target="_blank" 
                rel="noopener noreferrer"
                class="flex items-center text-blue-600 dark:text-blue-400 hover:underline"
              >
                <Icon name="lucide:globe" class="w-4 h-4 mr-1" />
                官方網站
              </a>
            </div>
          </div>

          <div class="flex items-center space-x-3">
            <button
              @click="toggleWatch"
              class="flex items-center px-4 py-2 rounded-lg border transition-all duration-200"
              :class="isWatched 
                ? 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800 text-red-600 dark:text-red-400' 
                : 'bg-white dark:bg-slate-800 border-gray-200 dark:border-slate-700 text-gray-600 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-700'"
            >
              <Icon 
                :name="isWatched ? 'heroicons:heart-20-solid' : 'lucide:heart'" 
                class="w-5 h-5 mr-2" 
                :class="isWatched ? 'text-red-500' : ''"
              />
              {{ isWatched ? '取消追蹤' : '加入追蹤' }}
            </button>
          </div>
        </div>
      </div>

      <!-- Tabs -->
      <div class="bg-gray-100 dark:bg-slate-800 p-1 rounded-xl flex md:bg-transparent md:dark:bg-transparent md:p-0 md:rounded-none md:border-b md:border-gray-200 md:dark:border-slate-800">
        <nav class="flex w-full md:w-auto md:space-x-8 overflow-hidden" aria-label="Tabs">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            @click="activeTab = tab.id"
            :class="[
              activeTab === tab.id
                ? 'bg-white dark:bg-slate-700 shadow-sm text-blue-600 dark:text-blue-400 md:bg-transparent md:dark:bg-transparent md:shadow-none md:border-blue-500 md:border-b-2'
                : 'text-gray-500 dark:text-slate-400 hover:text-gray-700 dark:hover:text-slate-300 md:border-transparent md:border-b-2 md:hover:border-gray-300',
              'flex-1 text-center py-2 md:py-4 px-1 font-medium text-xs md:text-sm transition-all rounded-lg md:rounded-none cursor-pointer'
            ]"
          >
            {{ tab.label }}
          </button>
        </nav>
      </div>

      <!-- Tab Content -->
      <div class="min-h-[400px]">
        <!-- Overview Tab -->
        <div v-if="activeTab === 'overview'" class="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-xl p-4 md:p-6">
          <h3 class="text-lg font-bold text-gray-900 dark:text-white mb-6">公司基本資料</h3>
          <dl class="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-4 md:gap-y-8">
            <div>
              <dt class="text-sm font-medium text-gray-500 dark:text-slate-400">董事長</dt>
              <dd class="mt-1 text-sm text-gray-900 dark:text-white">{{ company.chairman || '-' }}</dd>
            </div>
            <div>
              <dt class="text-sm font-medium text-gray-500 dark:text-slate-400">總經理</dt>
              <dd class="mt-1 text-sm text-gray-900 dark:text-white">{{ company.manager || '-' }}</dd>
            </div>
            <div>
              <dt class="text-sm font-medium text-gray-500 dark:text-slate-400">統一編號</dt>
              <dd class="mt-1 text-sm text-gray-900 dark:text-white">{{ company.tax_id || '-' }}</dd>
            </div>
            <div>
              <dt class="text-sm font-medium text-gray-500 dark:text-slate-400">成立日期</dt>
              <dd class="mt-1 text-sm text-gray-900 dark:text-white">{{ formatDate(company.establishment_date) }}</dd>
            </div>
             <div>
              <dt class="text-sm font-medium text-gray-500 dark:text-slate-400">上市日期</dt>
              <dd class="mt-1 text-sm text-gray-900 dark:text-white">{{ formatDate(company.listing_date) }}</dd>
            </div>
             <div>
              <dt class="text-sm font-medium text-gray-500 dark:text-slate-400">實收資本額</dt>
              <dd class="mt-1 text-sm text-gray-900 dark:text-white">{{ company.capital ? `$${formatCurrency(company.capital)}` : '-' }}</dd>
            </div>
          </dl>
        </div>

        <!-- Stats Tab -->
        <div v-else-if="activeTab === 'stats'">
           <div v-if="profile.non_manager_salaries && profile.non_manager_salaries.length > 0">
              <CompanyYearlyStats :stats="profile.non_manager_salaries" />
           </div>
           <div v-else class="text-center py-12 bg-white dark:bg-slate-900 rounded-xl border border-gray-200 dark:border-slate-800">
             <p class="text-gray-500 dark:text-slate-400">暫無薪資統計資料</p>
           </div>
        </div>

        <!-- Violations Tab -->
        <div v-else-if="activeTab === 'violations'">
          <div class="mb-4 bg-gray-50 dark:bg-slate-800/50 p-1 rounded-lg inline-flex">
             <button 
               @click="violationType = 'labor'"
               :class="violationType === 'labor' ? 'bg-white dark:bg-slate-700 shadow-sm text-blue-600 dark:text-blue-400 font-medium' : 'text-gray-500 dark:text-slate-400 hover:text-gray-700 dark:hover:text-slate-200'"
               class="px-4 py-2 rounded-md text-sm transition-all"
             >
               勞動違規 ({{ profile.violations?.length || 0 }})
             </button>
             <button 
               @click="violationType = 'env'"
               :class="violationType === 'env' ? 'bg-white dark:bg-slate-700 shadow-sm text-green-600 dark:text-green-400 font-medium' : 'text-gray-500 dark:text-slate-400 hover:text-gray-700 dark:hover:text-slate-200'"
               class="px-4 py-2 rounded-md text-sm transition-all"
             >
               環保裁罰 ({{ profile.environmental_violations?.length || 0 }})
             </button>
          </div>

          <!-- Labor Violations -->
          <div v-if="violationType === 'labor'">
            <div v-if="profile.violations && profile.violations.length > 0">
               <!-- Desktop Table -->
               <div class="hidden md:block overflow-hidden bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-xl">
                 <table class="min-w-full divide-y divide-gray-200 dark:divide-slate-800">
                   <thead class="bg-gray-50 dark:bg-slate-800">
                     <tr>
                       <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-slate-400 uppercase tracking-wider">處分日期</th>
                       <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-slate-400 uppercase tracking-wider">主管機關</th>
                        <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-slate-400 uppercase tracking-wider">違反法規</th>
                       <th scope="col" class="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-slate-400 uppercase tracking-wider">罰鍰金額</th>
                     </tr>
                   </thead>
                   <tbody class="bg-white dark:bg-slate-900 divide-y divide-gray-200 dark:divide-slate-800">
                     <tr v-for="v in profile.violations" :key="v.id" class="hover:bg-gray-50 dark:hover:bg-slate-800/50 transition-colors">
                       <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                         {{ formatDate(v.penalty_date) }}
                       </td>
                       <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-slate-400">
                         {{ v.authority }}
                       </td>
                        <td class="px-6 py-4 text-sm text-gray-900 dark:text-white">
                          <div class="font-medium mb-1">{{ v.law_article }}</div>
                          <p v-if="v.violation_content" class="text-gray-500 dark:text-slate-400 text-xs whitespace-pre-wrap leading-relaxed">
                            {{ v.violation_content }}
                          </p>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-right font-medium">
                          <span v-if="v.fine_amount > 0" class="text-red-600 dark:text-red-400">
                            {{ formatCurrency(v.fine_amount) }}
                          </span>
                          <span v-else class="text-gray-400 dark:text-slate-500 font-normal">
                            -
                          </span>
                        </td>
                     </tr>
                   </tbody>
                 </table>
               </div>

               <!-- Mobile Cards -->
               <div class="md:hidden space-y-4">
                 <div v-for="v in profile.violations" :key="v.id" class="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-xl p-4 shadow-sm">
                   <div class="flex justify-between items-start mb-3">
                     <span class="text-xs text-gray-500 dark:text-slate-400">{{ formatDate(v.penalty_date) }}</span>
                     <span v-if="v.fine_amount > 0" class="text-sm font-bold text-red-600 dark:text-red-400">
                       {{ formatCurrency(v.fine_amount) }}
                     </span>
                     <span v-else class="text-xs text-gray-400">-</span>
                   </div>
                   <div class="mb-2">
                     <div class="text-xs font-semibold text-blue-600 dark:text-blue-400 mb-1">{{ v.authority }}</div>
                     <div class="text-sm font-bold text-gray-900 dark:text-white">{{ v.law_article }}</div>
                   </div>
                   <p v-if="v.violation_content" class="text-xs text-gray-600 dark:text-slate-400 bg-gray-50 dark:bg-slate-800/50 p-2 rounded-lg leading-relaxed mt-2">
                     {{ v.violation_content }}
                   </p>
                 </div>
               </div>
            </div>
             <div v-else class="text-center py-24 bg-white dark:bg-slate-900 rounded-xl border border-gray-200 dark:border-slate-800 border-dashed">
               <Icon name="lucide:check-circle" class="w-16 h-16 text-green-500 mx-auto mb-4" />
               <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">無勞動違規紀錄</h3>
               <p class="text-gray-500 dark:text-slate-400">這是一間守法的公司（資料來源內未發現違規）</p>
             </div>
          </div>

          <!-- Environmental Violations -->
          <div v-if="violationType === 'env'">
            <div v-if="profile.environmental_violations && profile.environmental_violations.length > 0">
               <!-- Desktop Table -->
               <div class="hidden md:block overflow-hidden bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-xl">
                 <table class="min-w-full divide-y divide-gray-200 dark:divide-slate-800">
                   <thead class="bg-gray-50 dark:bg-slate-800">
                     <tr>
                       <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-slate-400 uppercase tracking-wider">處分日期</th>
                       <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-slate-400 uppercase tracking-wider">處分字號</th>
                        <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-slate-400 uppercase tracking-wider">違反法規 / 事由</th>
                       <th scope="col" class="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-slate-400 uppercase tracking-wider">處分金額</th>
                     </tr>
                   </thead>
                   <tbody class="bg-white dark:bg-slate-900 divide-y divide-gray-200 dark:divide-slate-800">
                     <tr v-for="ev in profile.environmental_violations" :key="ev.id" class="hover:bg-gray-50 dark:hover:bg-slate-800/50 transition-colors">
                       <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                         {{ formatDate(ev.penalty_date) }}
                       </td>
                       <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-slate-400">
                         {{ ev.disposition_no }}
                         <div class="text-xs text-gray-400 mt-0.5">{{ ev.authority }}</div>
                       </td>
                        <td class="px-6 py-4 text-sm text-gray-900 dark:text-white">
                          <div class="font-medium mb-1 text-green-700 dark:text-green-400">{{ ev.law_article }}</div>
                          <p v-if="ev.violation_reason" class="text-gray-500 dark:text-slate-400 text-xs whitespace-pre-wrap leading-relaxed">
                            {{ ev.violation_reason }}
                          </p>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-right font-medium">
                          <span v-if="ev.fine_amount > 0" class="text-red-600 dark:text-red-400">
                            {{ formatCurrency(ev.fine_amount) }}
                          </span>
                          <span v-else class="text-gray-400 dark:text-slate-500 font-normal">
                            -
                          </span>
                        </td>
                     </tr>
                   </tbody>
                 </table>
               </div>

               <!-- Mobile Cards -->
               <div class="md:hidden space-y-4">
                 <div v-for="ev in profile.environmental_violations" :key="ev.id" class="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-xl p-4 shadow-sm">
                   <div class="flex justify-between items-start mb-3">
                     <span class="text-xs text-gray-500 dark:text-slate-400">{{ formatDate(ev.penalty_date) }}</span>
                     <span v-if="ev.fine_amount > 0" class="text-sm font-bold text-red-600 dark:text-red-400">
                       {{ formatCurrency(ev.fine_amount) }}
                     </span>
                     <span v-else class="text-xs text-gray-400">-</span>
                   </div>
                   <div class="mb-2">
                     <div class="text-xs font-semibold text-green-600 dark:text-green-400 mb-1">{{ ev.authority }} ({{ ev.disposition_no }})</div>
                     <div class="text-sm font-bold text-gray-900 dark:text-white">{{ ev.law_article }}</div>
                   </div>
                   <p v-if="ev.violation_reason" class="text-xs text-gray-600 dark:text-slate-400 bg-gray-50 dark:bg-slate-800/50 p-2 rounded-lg leading-relaxed mt-2">
                     {{ ev.violation_reason }}
                   </p>
                 </div>
               </div>
            </div>
             <div v-else class="text-center py-24 bg-white dark:bg-slate-900 rounded-xl border border-gray-200 dark:border-slate-800 border-dashed">
               <Icon name="lucide:leaf" class="w-16 h-16 text-green-500 mx-auto mb-4" />
               <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">無環保裁罰紀錄</h3>
               <p class="text-gray-500 dark:text-slate-400">感謝公司對環境保護的努力（資料來源內未發現違規）</p>
             </div>
          </div>
        </div>

        <!-- Welfare Tab -->
        <div v-else-if="activeTab === 'welfare'">
          <div class="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-xl p-4 md:p-6">
             <div v-if="profile.welfare_policies && profile.welfare_policies.length > 0">
               <div v-for="policy in profile.welfare_policies" :key="policy.id" class="prose dark:prose-invert max-w-none">
                 <h4 class="font-bold mb-2">{{ policy.year }}年 福利政策</h4>
                 <div class="whitespace-pre-line text-sm text-gray-700 dark:text-slate-300">{{ policy.actual_salary_increase_note || '無詳細內容' }}</div>
               </div>
             </div>
             <div v-else class="text-center py-12">
               <p class="text-gray-500 dark:text-slate-400">暫無員工福利資料</p>
             </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
