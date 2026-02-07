<script setup lang="ts">
import type { LeaderboardsResponse, ViolationLeaderboardItem } from "~/types/api";

const props = defineProps<{
  data: LeaderboardsResponse | null;
}>();

// Get latest year data
const latestYear = computed(() => props.data?.latest_year);

// Top violators by count (from violation_yearly for latest year)
const topByCount = computed(() => {
  if (!props.data?.latest_year) return [];
  const yearData = props.data.violation_yearly?.[String(props.data.latest_year)];
  return yearData?.top_by_count || [];
});

// Top violators by fine amount
const topByFine = computed(() => {
  if (!props.data?.latest_year) return [];
  const yearData = props.data.violation_yearly?.[String(props.data.latest_year)];
  return yearData?.top_by_fine || [];
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
          <Icon name="lucide:alert-triangle" class="w-5 h-5 mr-2 text-red-500" />
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
        {{ latestYear || "-" }} 年度違規統計
      </p>
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
          <div class="h-3 bg-gray-100 dark:bg-slate-800 rounded w-16 animate-pulse"></div>
        </div>
      </div>
    </div>

    <!-- By Count -->
    <div
      v-else-if="activeTab === 'count'"
      class="divide-y divide-gray-100 dark:divide-slate-800"
    >
      <NuxtLink
        v-for="(item, index) in topByCount"
        :key="item.company_code"
        :to="`/companies/${item.company_code}`"
        class="flex items-center px-4 md:px-6 py-3 hover:bg-gray-50 dark:hover:bg-slate-800/50 transition-colors"
      >
        <span
          class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold mr-3 shrink-0"
          :class="[
            index === 0
              ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
              : index === 1
                ? 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400'
                : index === 2
                  ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
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
          <div class="text-lg font-bold text-red-600 dark:text-red-400">
            {{ item.total_count }}
          </div>
          <div class="text-xs text-gray-400 dark:text-slate-500">
            勞{{ item.labor_count }} / 環{{ item.env_count }}
          </div>
        </div>
      </NuxtLink>
      <div
        v-if="data && topByCount.length === 0"
        class="p-8 text-center text-gray-400"
      >
        無違規資料
      </div>
    </div>

    <!-- By Fine -->
    <div v-else class="divide-y divide-gray-100 dark:divide-slate-800">
      <NuxtLink
        v-for="(item, index) in topByFine"
        :key="item.company_code"
        :to="`/companies/${item.company_code}`"
        class="flex items-center px-4 md:px-6 py-3 hover:bg-gray-50 dark:hover:bg-slate-800/50 transition-colors"
      >
        <span
          class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold mr-3 shrink-0"
          :class="[
            index === 0
              ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
              : index === 1
                ? 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400'
                : index === 2
                  ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
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
          <div class="text-lg font-bold text-red-600 dark:text-red-400">
            {{ item.total_fine.toLocaleString() }}
          </div>
          <div class="text-xs text-gray-400 dark:text-slate-500">元</div>
        </div>
      </NuxtLink>
      <div v-if="data && topByFine.length === 0" class="p-8 text-center text-gray-400">
        無違規資料
      </div>
    </div>
  </div>
</template>
