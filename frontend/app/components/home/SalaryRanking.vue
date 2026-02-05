<script setup lang="ts">
import { useApi } from "~/composables/useApi";

const api = useApi();

// Fetch yearly summary data for the latest year
const { data: summaryData, status } = await useAsyncData(
  "salary-ranking",
  async () => {
    const index = await api.getYearlySummaryIndex();
    if (!index.years || index.years.length === 0) return null;

    const latestYear = Math.max(...index.years);
    const response = await api.getYearlySummary({ year: [latestYear] });

    return {
      year: latestYear,
      items: response.items,
    };
  },
  { server: false },
);

// Top by average salary
const topBySalary = computed(() => {
  if (!summaryData.value?.items) return [];

  return [...summaryData.value.items]
    .filter((item) => item.non_manager_salary?.avg_salary != null)
    .sort(
      (a, b) =>
        (b.non_manager_salary?.avg_salary || 0) -
        (a.non_manager_salary?.avg_salary || 0),
    )
    .slice(0, 10)
    .map((item) => ({
      code: item.company_code,
      name: item.company_name,
      salary: item.non_manager_salary?.avg_salary || 0,
    }));
});

// Lowest by average salary (excluding companies with no data)
const bottomBySalary = computed(() => {
  if (!summaryData.value?.items) return [];

  return [...summaryData.value.items]
    .filter(
      (item) =>
        item.non_manager_salary?.avg_salary != null &&
        item.non_manager_salary.avg_salary > 0,
    )
    .sort(
      (a, b) =>
        (a.non_manager_salary?.avg_salary || 0) -
        (b.non_manager_salary?.avg_salary || 0),
    )
    .slice(0, 10)
    .map((item) => ({
      code: item.company_code,
      name: item.company_name,
      salary: item.non_manager_salary?.avg_salary || 0,
    }));
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
            @click="activeTab = 'top'"
            class="px-3 py-1.5 text-xs font-medium rounded-md transition-all"
            :class="
              activeTab === 'top'
                ? 'bg-white dark:bg-slate-700 text-green-600 dark:text-green-400 shadow-sm'
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
      <p class="text-sm text-gray-500 dark:text-slate-400 mt-1">
        {{ summaryData?.year || "-" }} 年度非主管平均薪資
      </p>
    </div>

    <!-- Loading -->
    <div v-if="status === 'pending'" class="p-8 text-center text-gray-400">
      <Icon name="lucide:loader-2" class="w-8 h-8 animate-spin mx-auto mb-2" />
      載入中...
    </div>

    <!-- Top Ranking -->
    <div
      v-else-if="activeTab === 'top'"
      class="divide-y divide-gray-100 dark:divide-slate-800"
    >
      <NuxtLink
        v-for="(item, index) in topBySalary"
        :key="item.code"
        :to="`/companies/${item.code}`"
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
            {{ item.name }}
          </div>
          <div class="text-xs text-gray-500 dark:text-slate-400">
            {{ item.code }}
          </div>
        </div>
        <div class="text-right ml-4">
          <div class="text-lg font-bold text-green-600 dark:text-green-400">
            {{ item.salary.toLocaleString() }}
          </div>
          <div class="text-xs text-gray-400 dark:text-slate-500">仟元</div>
        </div>
      </NuxtLink>
    </div>

    <!-- Bottom Ranking -->
    <div v-else class="divide-y divide-gray-100 dark:divide-slate-800">
      <NuxtLink
        v-for="(item, index) in bottomBySalary"
        :key="item.code"
        :to="`/companies/${item.code}`"
        class="flex items-center px-4 md:px-6 py-3 hover:bg-gray-50 dark:hover:bg-slate-800/50 transition-colors"
      >
        <span
          class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold mr-3 shrink-0 bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400"
        >
          {{ index + 1 }}
        </span>
        <div class="flex-1 min-w-0">
          <div class="font-medium text-gray-900 dark:text-white truncate">
            {{ item.name }}
          </div>
          <div class="text-xs text-gray-500 dark:text-slate-400">
            {{ item.code }}
          </div>
        </div>
        <div class="text-right ml-4">
          <div class="text-lg font-bold text-amber-600 dark:text-amber-400">
            {{ item.salary.toLocaleString() }}
          </div>
          <div class="text-xs text-gray-400 dark:text-slate-500">仟元</div>
        </div>
      </NuxtLink>
    </div>
  </div>
</template>
