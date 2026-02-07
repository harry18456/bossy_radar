<script setup lang="ts">
import type { LeaderboardsResponse, IndustrySalaryLeaderboardItem } from "~/types/api";

const props = defineProps<{
  data: LeaderboardsResponse | null;
}>();

// Get latest year from salary_by_industry data (find year with actual data)
const latestYear = computed(() => {
  if (!props.data?.salary_by_industry) return null;
  const years = Object.keys(props.data.salary_by_industry)
    .map(Number)
    .sort((a, b) => b - a);
  // Find first year that has actual industry data
  const yearWithData = years.find(year => {
    const yearData = props.data?.salary_by_industry?.[String(year)];
    return yearData && Object.keys(yearData).length > 0;
  });
  return yearWithData || null;
});

// Get available industries for the latest year
const industries = computed(() => {
  if (!latestYear.value || !props.data?.salary_by_industry) return [];
  const yearData = props.data.salary_by_industry[String(latestYear.value)];
  return Object.keys(yearData || {}).sort();
});

// Selected industry
const selectedIndustry = ref<string>("");

// Set default industry when data loads
watch(industries, (newIndustries) => {
  if (newIndustries.length > 0 && !selectedIndustry.value) {
    // Default to 半導體業 if exists, otherwise first industry
    selectedIndustry.value = newIndustries.includes("半導體業") 
      ? "半導體業" 
      : newIndustries[0] || "";
  }
}, { immediate: true });

// Top by median salary in selected industry
const topBySalary = computed(() => {
  if (!latestYear.value || !selectedIndustry.value || !props.data?.salary_by_industry) return [];
  const yearData = props.data.salary_by_industry[String(latestYear.value)];
  const industryData = yearData?.[selectedIndustry.value];
  return industryData?.top_by_median || [];
});

// Bottom by median salary in selected industry  
const bottomBySalary = computed(() => {
  if (!latestYear.value || !selectedIndustry.value || !props.data?.salary_by_industry) return [];
  const yearData = props.data.salary_by_industry[String(latestYear.value)];
  const industryData = yearData?.[selectedIndustry.value];
  return industryData?.bottom_by_median || [];
});

const activeTab = ref<"top" | "bottom">("top");
</script>

<template>
  <div
    class="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-xl shadow-sm overflow-hidden"
  >
    <div class="p-4 md:p-6 border-b border-gray-200 dark:border-slate-800">
      <div class="flex flex-col gap-3">
        <h3
          class="text-lg font-bold text-gray-900 dark:text-white flex items-center"
        >
          <Icon name="lucide:building-2" class="w-5 h-5 mr-2 text-blue-500" />
          產業薪資排行 (中位數)
        </h3>

        <!-- Tab Toggle -->
        <div class="flex bg-gray-100 dark:bg-slate-800 rounded-lg p-0.5 w-fit">
          <button
            @click="activeTab = 'top'"
            class="px-3 py-1.5 text-xs font-medium rounded-md transition-all"
            :class="
              activeTab === 'top'
                ? 'bg-white dark:bg-slate-700 text-blue-600 dark:text-blue-400 shadow-sm'
                : 'text-gray-500 dark:text-slate-400 hover:text-gray-700'
            "
          >
            最高薪
          </button>
          <button
            @click="activeTab = 'bottom'"
            class="px-3 py-1.5 text-xs font-medium rounded-md transition-all"
            :class="
              activeTab === 'bottom'
                ? 'bg-white dark:bg-slate-700 text-amber-600 dark:text-amber-400 shadow-sm'
                : 'text-gray-500 dark:text-slate-400 hover:text-gray-700'
            "
          >
            最低薪
          </button>
        </div>
      </div>
      
      <!-- Industry Selector -->
      <div class="mt-3 flex items-center gap-2">
        <span class="text-sm text-gray-500 dark:text-slate-400">產業：</span>
        <select
          v-model="selectedIndustry"
          class="text-sm bg-gray-100 dark:bg-slate-800 border-none rounded-lg px-3 py-1.5 text-gray-700 dark:text-slate-300 focus:ring-2 focus:ring-blue-500"
        >
          <option v-for="industry in industries" :key="industry" :value="industry">
            {{ industry }}
          </option>
        </select>
        <span class="text-xs text-gray-400 dark:text-slate-500">
          {{ latestYear }} 年度中位數
        </span>
      </div>
    </div>

    <!-- Loading state when data is null -->
    <div v-if="!data" class="divide-y divide-gray-100 dark:divide-slate-800">
      <div v-for="i in 5" :key="i" class="flex items-center px-4 md:px-6 py-3">
        <div class="w-6 h-6 rounded-full bg-gray-200 dark:bg-slate-700 animate-pulse mr-3"></div>
        <div class="flex-1">
          <div class="h-4 bg-gray-200 dark:bg-slate-700 rounded w-2/3 mb-2 animate-pulse"></div>
          <div class="h-3 bg-gray-100 dark:bg-slate-800 rounded w-1/4 animate-pulse"></div>
        </div>
        <div class="text-right ml-4">
          <div class="h-5 bg-gray-200 dark:bg-slate-700 rounded w-12 mb-1 animate-pulse"></div>
          <div class="h-3 bg-gray-100 dark:bg-slate-800 rounded w-10 animate-pulse"></div>
        </div>
      </div>
    </div>

    <!-- Top Ranking -->
    <div
      v-else-if="activeTab === 'top'"
      class="divide-y divide-gray-100 dark:divide-slate-800"
    >
      <NuxtLink
        v-for="(item, index) in topBySalary"
        :key="item.company_code"
        :to="`/companies/${item.company_code}`"
        class="flex items-center px-4 md:px-6 py-3 hover:bg-gray-50 dark:hover:bg-slate-800/50 transition-colors"
      >
        <span
          class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold mr-3 shrink-0"
          :class="[
            index === 0
              ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
              : index === 1
                ? 'bg-cyan-100 text-cyan-700 dark:bg-cyan-900/30 dark:text-cyan-400'
                : index === 2
                  ? 'bg-teal-100 text-teal-700 dark:bg-teal-900/30 dark:text-teal-400'
                  : 'bg-gray-50 text-gray-500 dark:bg-slate-800 dark:text-slate-400',
          ]"
        >
          {{ index + 1 }}
        </span>
        <div class="flex-1 min-w-0">
          <div class="font-medium text-gray-900 dark:text-white truncate">
            {{ item.company_name }}
          </div>
          <div class="text-xs text-gray-500 dark:text-slate-400">
            {{ item.company_code }}
          </div>
        </div>
        <div class="text-right ml-4">
          <div class="text-lg font-bold text-blue-600 dark:text-blue-400">
            {{ item.median_salary?.toLocaleString() }}
          </div>
          <div class="text-xs text-gray-400 dark:text-slate-500">仟元</div>
        </div>
      </NuxtLink>
      <div
        v-if="data && topBySalary.length === 0"
        class="p-8 text-center text-gray-400"
      >
        無薪資資料
      </div>
    </div>

    <!-- Bottom Ranking -->
    <div v-else class="divide-y divide-gray-100 dark:divide-slate-800">
      <NuxtLink
        v-for="(item, index) in bottomBySalary"
        :key="item.company_code"
        :to="`/companies/${item.company_code}`"
        class="flex items-center px-4 md:px-6 py-3 hover:bg-gray-50 dark:hover:bg-slate-800/50 transition-colors"
      >
        <span
          class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold mr-3 shrink-0 bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400"
        >
          {{ index + 1 }}
        </span>
        <div class="flex-1 min-w-0">
          <div class="font-medium text-gray-900 dark:text-white truncate">
            {{ item.company_name }}
          </div>
          <div class="text-xs text-gray-500 dark:text-slate-400">
            {{ item.company_code }}
          </div>
        </div>
        <div class="text-right ml-4">
          <div class="text-lg font-bold text-amber-600 dark:text-amber-400">
            {{ item.median_salary?.toLocaleString() }}
          </div>
          <div class="text-xs text-gray-400 dark:text-slate-500">仟元</div>
        </div>
      </NuxtLink>
      <div
        v-if="data && bottomBySalary.length === 0"
        class="p-8 text-center text-gray-400"
      >
        無薪資資料
      </div>
    </div>
  </div>
</template>
