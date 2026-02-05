<script setup lang="ts">
import { useApi } from "~/composables/useApi";

const api = useApi();

// Fetch yearly summary data for the latest year
const { data: summaryData, status } = await useAsyncData(
  "violation-leaderboard",
  async () => {
    // Get available years
    const index = await api.getYearlySummaryIndex();
    if (!index.years || index.years.length === 0) return null;

    // Get latest year data
    const latestYear = Math.max(...index.years);
    const response = await api.getYearlySummary({ year: [latestYear] });

    return {
      year: latestYear,
      items: response.items,
    };
  },
  { server: false },
);

// Top violators by count
const topByCount = computed(() => {
  if (!summaryData.value?.items) return [];

  return [...summaryData.value.items]
    .map((item) => ({
      code: item.company_code,
      name: item.company_name,
      labor: item.violations_total_count || 0,
      env: item.env_violations_total_count || 0,
      total:
        (item.violations_total_count || 0) +
        (item.env_violations_total_count || 0),
    }))
    .filter((item) => item.total > 0)
    .sort((a, b) => b.total - a.total)
    .slice(0, 10);
});

// Top violators by fine amount
const topByFine = computed(() => {
  if (!summaryData.value?.items) return [];

  return [...summaryData.value.items]
    .map((item) => ({
      code: item.company_code,
      name: item.company_name,
      labor: item.violations_total_fine || 0,
      env: item.env_violations_total_fine || 0,
      total:
        (item.violations_total_fine || 0) +
        (item.env_violations_total_fine || 0),
    }))
    .filter((item) => item.total > 0)
    .sort((a, b) => b.total - a.total)
    .slice(0, 10);
});

const activeTab = ref<"count" | "fine">("count");
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
          <Icon name="lucide:trophy" class="w-5 h-5 mr-2 text-red-500" />
          違規排行榜
        </h3>

        <!-- Tab Toggle -->
        <div class="flex bg-gray-100 dark:bg-slate-800 rounded-lg p-0.5">
          <button
            @click="activeTab = 'count'"
            class="px-3 py-1.5 text-xs font-medium rounded-md transition-all"
            :class="
              activeTab === 'count'
                ? 'bg-white dark:bg-slate-700 text-red-600 dark:text-red-400 shadow-sm'
                : 'text-gray-500 dark:text-slate-400 hover:text-gray-700'
            "
          >
            違規次數
          </button>
          <button
            @click="activeTab = 'fine'"
            class="px-3 py-1.5 text-xs font-medium rounded-md transition-all"
            :class="
              activeTab === 'fine'
                ? 'bg-white dark:bg-slate-700 text-red-600 dark:text-red-400 shadow-sm'
                : 'text-gray-500 dark:text-slate-400 hover:text-gray-700'
            "
          >
            罰鍰金額
          </button>
        </div>
      </div>
      <p class="text-sm text-gray-500 dark:text-slate-400 mt-1">
        累計至 {{ summaryData?.year || "-" }} 年度
      </p>
    </div>

    <!-- Loading -->
    <div v-if="status === 'pending'" class="p-8 text-center text-gray-400">
      <Icon name="lucide:loader-2" class="w-8 h-8 animate-spin mx-auto mb-2" />
      載入中...
    </div>

    <!-- Count Ranking -->
    <div
      v-else-if="activeTab === 'count'"
      class="divide-y divide-gray-100 dark:divide-slate-800"
    >
      <NuxtLink
        v-for="(item, index) in topByCount"
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
          <div class="text-lg font-bold text-red-600 dark:text-red-400">
            {{ item.total }}
          </div>
          <div class="text-xs text-gray-400 dark:text-slate-500">
            勞{{ item.labor }} / 環{{ item.env }}
          </div>
        </div>
      </NuxtLink>

      <div v-if="topByCount.length === 0" class="p-8 text-center text-gray-400">
        無違規資料
      </div>
    </div>

    <!-- Fine Ranking -->
    <div v-else class="divide-y divide-gray-100 dark:divide-slate-800">
      <NuxtLink
        v-for="(item, index) in topByFine"
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
          <div class="text-lg font-bold text-red-600 dark:text-red-400">
            {{ (item.total / 10000).toFixed(0) }} 萬
          </div>
          <div class="text-xs text-gray-400 dark:text-slate-500">
            勞{{ (item.labor / 10000).toFixed(0) }}萬 / 環{{
              (item.env / 10000).toFixed(0)
            }}萬
          </div>
        </div>
      </NuxtLink>

      <div v-if="topByFine.length === 0" class="p-8 text-center text-gray-400">
        無違規資料
      </div>
    </div>
  </div>
</template>
