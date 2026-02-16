<script setup lang="ts">
import type { LeaderboardsResponse, SalaryLeaderboardItem } from "~/types/api";

const props = defineProps<{
  data: LeaderboardsResponse | null;
}>();

// Get latest year from salary data (find max year key that has actual data)
const latestSalaryYear = computed(() => {
  if (!props.data?.salary) return null;
  const years = Object.keys(props.data.salary)
    .map(Number)
    .sort((a, b) => b - a);
  // Find first year that has actual data (non-empty top_by_median)
  const yearWithData = years.find(year => {
    const yearData = props.data?.salary?.[String(year)];
    return yearData?.top_by_median && yearData.top_by_median.length > 0;
  });
  return yearWithData || null;
});

// Top by median salary
const topBySalary = computed(() => {
  if (!latestSalaryYear.value) return [];
  const yearData = props.data?.salary?.[String(latestSalaryYear.value)];
  return yearData?.top_by_median || [];
});

// Bottom by median salary
const bottomBySalary = computed(() => {
  if (!latestSalaryYear.value) return [];
  const yearData = props.data?.salary?.[String(latestSalaryYear.value)];
  return yearData?.bottom_by_median || [];
});

const activeTab = ref<"top" | "bottom">("top");
</script>

<template>
  <div
    class="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-xl shadow-sm overflow-hidden"
  >
    <div class="p-4 md:p-6 border-b border-gray-200 dark:border-slate-800">
      <div class="flex items-center justify-between">
        <h3
          class="text-lg font-bold text-gray-900 dark:text-white flex items-center"
        >
          <Icon name="lucide:medal" class="w-5 h-5 mr-2 text-green-500" />
          薪資排行榜
        </h3>

        <!-- Tab Toggle -->
        <div class="flex bg-gray-100 dark:bg-slate-800 rounded-lg p-0.5">
          <button
            class="px-3 py-1.5 text-xs font-medium rounded-md transition-all"
            :class="
              activeTab === 'top'
                ? 'bg-white dark:bg-slate-700 text-green-600 dark:text-green-400 shadow-sm'
                : 'text-gray-500 dark:text-slate-400 hover:text-gray-700'
            "
            @click="activeTab = 'top'"
          >
            最高薪
          </button>
          <button
            class="px-3 py-1.5 text-xs font-medium rounded-md transition-all"
            :class="
              activeTab === 'bottom'
                ? 'bg-white dark:bg-slate-700 text-amber-600 dark:text-amber-400 shadow-sm'
                : 'text-gray-500 dark:text-slate-400 hover:text-gray-700'
            "
            @click="activeTab = 'bottom'"
          >
            最低薪
          </button>
        </div>
      </div>
      <p class="text-sm text-gray-500 dark:text-slate-400 mt-1">
        {{ latestSalaryYear || "-" }} 年度非主管中位數薪資
      </p>
    </div>

    <!-- Loading state when data is null -->
    <div v-if="!data" class="divide-y divide-gray-100 dark:divide-slate-800">
      <div v-for="i in 5" :key="i" class="flex items-center px-4 md:px-6 py-3">
        <div class="w-6 h-6 rounded-full bg-gray-200 dark:bg-slate-700 animate-pulse mr-3"/>
        <div class="flex-1">
          <div class="h-4 bg-gray-200 dark:bg-slate-700 rounded w-2/3 mb-2 animate-pulse"/>
          <div class="h-3 bg-gray-100 dark:bg-slate-800 rounded w-1/4 animate-pulse"/>
        </div>
        <div class="text-right ml-4">
          <div class="h-5 bg-gray-200 dark:bg-slate-700 rounded w-12 mb-1 animate-pulse"/>
          <div class="h-3 bg-gray-100 dark:bg-slate-800 rounded w-10 animate-pulse"/>
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
              ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
              : index === 1
                ? 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300'
                : index === 2
                  ? 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400'
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
          <div class="text-lg font-bold text-green-600 dark:text-green-400">
            {{ item.median_salary.toLocaleString() }}
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
            {{ item.median_salary.toLocaleString() }}
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
