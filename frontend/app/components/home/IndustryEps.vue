<script setup lang="ts">
import type { LeaderboardsResponse, IndustrySalaryLeaderboardItem } from "~/types/api";

const props = defineProps<{
  data: LeaderboardsResponse | null;
}>();

// Get latest year from salary_by_industry data (find year with actual data)
const latestYear = computed(() => {
  if (!props.data?.salary_by_industry) {
    console.log("No salary_by_industry in data", props.data);
    return null;
  }
  const years = Object.keys(props.data.salary_by_industry)
    .map(Number)
    .sort((a, b) => b - a);

  console.log("Available years in salary_by_industry:", years);
  
  // Find first year that has actual industry EPS data
  const yearWithData = years.find(year => {
    const yearData = props.data?.salary_by_industry?.[String(year)];
    console.log(`Checking year ${year} for EPS data...`, yearData);
    // Check if any industry has top_by_eps data
    const hasData = yearData && Object.values(yearData).some(industry => {
      const hasEps = industry.top_by_eps?.length > 0;
      if (hasEps) console.log("Found EPS data in industry:", industry);
      return hasEps;
    });
    return hasData;
  });

  console.log("Found year with EPS data:", yearWithData);
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

// Top by EPS in selected industry
const topByEps = computed(() => {
  if (!latestYear.value || !selectedIndustry.value || !props.data?.salary_by_industry) return [];
  const yearData = props.data.salary_by_industry[String(latestYear.value)];
  const industryData = yearData?.[selectedIndustry.value];
  return industryData?.top_by_eps || [];
});

// Bottom by EPS in selected industry  
const bottomByEps = computed(() => {
  if (!latestYear.value || !selectedIndustry.value || !props.data?.salary_by_industry) return [];
  const yearData = props.data.salary_by_industry[String(latestYear.value)];
  const industryData = yearData?.[selectedIndustry.value];
  return industryData?.bottom_by_eps || [];
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
          <Icon name="lucide:trending-up" class="w-5 h-5 mr-2 text-purple-500" />
          產業 EPS 排行
        </h3>

        <!-- Tab Toggle -->
        <div class="flex bg-gray-100 dark:bg-slate-800 rounded-lg p-0.5 w-fit">
          <button
            @click="activeTab = 'top'"
            class="px-3 py-1.5 text-xs font-medium rounded-md transition-all"
            :class="
              activeTab === 'top'
                ? 'bg-white dark:bg-slate-700 text-purple-600 dark:text-purple-400 shadow-sm'
                : 'text-gray-500 dark:text-slate-400 hover:text-gray-700'
            "
          >
            最高 EPS
          </button>
          <button
            @click="activeTab = 'bottom'"
            class="px-3 py-1.5 text-xs font-medium rounded-md transition-all"
            :class="
              activeTab === 'bottom'
                ? 'bg-white dark:bg-slate-700 text-slate-600 dark:text-slate-400 shadow-sm'
                : 'text-gray-500 dark:text-slate-400 hover:text-gray-700'
            "
          >
            最低 EPS
          </button>
        </div>
      </div>
      
      <!-- Industry Selector -->
      <div class="mt-3 flex items-center gap-2">
        <span class="text-sm text-gray-500 dark:text-slate-400">產業：</span>
        <select
          v-model="selectedIndustry"
          class="text-sm bg-gray-100 dark:bg-slate-800 border-none rounded-lg px-3 py-1.5 text-gray-700 dark:text-slate-300 focus:ring-2 focus:ring-purple-500"
        >
          <option v-for="industry in industries" :key="industry" :value="industry">
            {{ industry }}
          </option>
        </select>
        <span class="text-xs text-gray-400 dark:text-slate-500">
          {{ latestYear }} 年度
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
        v-for="(item, index) in topByEps"
        :key="item.company_code"
        :to="`/companies/${item.company_code}`"
        class="flex items-center px-4 md:px-6 py-3 hover:bg-gray-50 dark:hover:bg-slate-800/50 transition-colors"
      >
        <span
          class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold mr-3 shrink-0"
          :class="[
            index === 0
              ? 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400'
              : index === 1
                ? 'bg-fuchsia-100 text-fuchsia-700 dark:bg-fuchsia-900/30 dark:text-fuchsia-400'
                : index === 2
                  ? 'bg-pink-100 text-pink-700 dark:bg-pink-900/30 dark:text-pink-400'
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
          <div class="text-lg font-bold text-purple-600 dark:text-purple-400">
            {{ item.eps?.toFixed(2) }}
          </div>
          <div class="text-xs text-gray-400 dark:text-slate-500">元</div>
        </div>
      </NuxtLink>
      <div
        v-if="data && topByEps.length === 0"
        class="p-8 text-center text-gray-400"
      >
        無 EPS 資料
      </div>
    </div>

    <!-- Bottom Ranking -->
    <div v-else class="divide-y divide-gray-100 dark:divide-slate-800">
      <NuxtLink
        v-for="(item, index) in bottomByEps"
        :key="item.company_code"
        :to="`/companies/${item.company_code}`"
        class="flex items-center px-4 md:px-6 py-3 hover:bg-gray-50 dark:hover:bg-slate-800/50 transition-colors"
      >
        <span
          class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold mr-3 shrink-0 bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-400"
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
          <div class="text-lg font-bold text-slate-600 dark:text-slate-400">
            {{ item.eps?.toFixed(2) }}
          </div>
          <div class="text-xs text-gray-400 dark:text-slate-500">元</div>
        </div>
      </NuxtLink>
      <div
        v-if="data && bottomByEps.length === 0"
        class="p-8 text-center text-gray-400"
      >
        無 EPS 資料
      </div>
    </div>
  </div>
</template>
