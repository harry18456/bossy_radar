<script setup lang="ts">
import { useApi } from "~/composables/useApi";
import type { LeaderboardsResponse } from "~/types/api";

definePageMeta({
  layout: "home",
});

usePageMeta({
  title: "Bossy Radar",
  description: "台灣上市櫃公司薪資福利與違規紀錄查詢",
});

// Inject structured data for SEO (WebSite + Organization)
const { injectWebSiteSchema, injectOrganizationSchema } = useStructuredData();
injectWebSiteSchema();
injectOrganizationSchema();

// Fetch leaderboards data once at page level
const api = useApi();
const { data: leaderboardData } = await useAsyncData<LeaderboardsResponse>(
  "home-leaderboards",
  () => api.getLeaderboards(),
  { server: false }
);
</script>

<template>
  <div class="space-y-16">
    <!-- Hero Section -->
    <div
      class="relative z-10 flex flex-col items-center justify-center min-h-[40vh] text-center"
    >
      <h1 class="text-4xl font-bold text-gray-900 dark:text-white mb-4">
        慣老闘雷達
        <span class="text-2xl text-gray-500 font-normal">(Bossy Radar)</span>
      </h1>
      <p class="text-xl text-gray-500 dark:text-slate-400 mb-8 max-w-2xl">
        透明化職場資訊，避開慣老闆。<br />
        查詢上市櫃公司薪資福利與違規紀錄。
      </p>

      <div class="flex gap-4">
        <NuxtLink
          to="/companies"
          class="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
        >
          搜尋公司
        </NuxtLink>
        <NuxtLink
          to="/watchlist"
          class="px-6 py-3 bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 text-gray-900 dark:text-white rounded-lg font-medium hover:bg-gray-50 dark:hover:bg-slate-700 transition-colors"
        >
          我的收藏
        </NuxtLink>
      </div>
    </div>

    <!-- Latest Year Leaderboards Section -->
    <section class="max-w-6xl mx-auto">
      <h2 class="text-xl font-bold text-gray-900 dark:text-white mb-6 flex items-center">
        <Icon name="lucide:calendar" class="w-5 h-5 mr-2 text-blue-500" />
        最新年度排行
      </h2>
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <ClientOnly>
          <HomeViolationLeaderboard :data="leaderboardData || null" />
          <template #fallback>
            <div
              class="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-xl p-8 text-center"
            >
              <div class="animate-pulse space-y-4">
                <div class="h-6 bg-gray-200 dark:bg-slate-700 rounded w-1/3 mx-auto"></div>
                <div class="h-4 bg-gray-200 dark:bg-slate-700 rounded w-1/2 mx-auto"></div>
              </div>
            </div>
          </template>
        </ClientOnly>

        <ClientOnly>
          <HomeSalaryRanking :data="leaderboardData || null" />
          <template #fallback>
            <div
              class="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-xl p-8 text-center"
            >
              <div class="animate-pulse space-y-4">
                <div class="h-6 bg-gray-200 dark:bg-slate-700 rounded w-1/3 mx-auto"></div>
                <div class="h-4 bg-gray-200 dark:bg-slate-700 rounded w-1/2 mx-auto"></div>
              </div>
            </div>
          </template>
        </ClientOnly>
      </div>
    </section>

    <!-- More Statistics Section -->
    <section class="max-w-6xl mx-auto">
      <h2 class="text-xl font-bold text-gray-900 dark:text-white mb-6 flex items-center">
        <Icon name="lucide:bar-chart-3" class="w-5 h-5 mr-2 text-purple-500" />
        更多統計資料
      </h2>
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <ClientOnly>
          <HomeAllTimeViolation :data="leaderboardData || null" />
          <template #fallback>
            <div
              class="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-xl p-8 text-center"
            >
              <div class="animate-pulse space-y-4">
                <div class="h-6 bg-gray-200 dark:bg-slate-700 rounded w-1/3 mx-auto"></div>
                <div class="h-4 bg-gray-200 dark:bg-slate-700 rounded w-1/2 mx-auto"></div>
              </div>
            </div>
          </template>
        </ClientOnly>

        <ClientOnly>
          <HomeIndustryEps :data="leaderboardData || null" />
          <template #fallback>
            <div
              class="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-xl p-8 text-center"
            >
              <div class="animate-pulse space-y-4">
                <div class="h-6 bg-gray-200 dark:bg-slate-700 rounded w-1/3 mx-auto"></div>
                <div class="h-4 bg-gray-200 dark:bg-slate-700 rounded w-1/2 mx-auto"></div>
              </div>
            </div>
          </template>
        </ClientOnly>

        <ClientOnly>
          <HomeIndustrySalary :data="leaderboardData || null" />
          <template #fallback>
            <div
              class="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-xl p-8 text-center"
            >
              <div class="animate-pulse space-y-4">
                <div class="h-6 bg-gray-200 dark:bg-slate-700 rounded w-1/3 mx-auto"></div>
                <div class="h-4 bg-gray-200 dark:bg-slate-700 rounded w-1/2 mx-auto"></div>
              </div>
            </div>
          </template>
        </ClientOnly>
      </div>
    </section>
  </div>
</template>
