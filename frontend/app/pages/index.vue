<script setup lang="ts">
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
</script>

<template>
  <div class="space-y-16">
    <!-- Hero Section -->
    <div
      class="relative z-10 flex flex-col items-center justify-center min-h-[40vh] text-center"
    >
      <h1 class="text-4xl font-bold text-gray-900 dark:text-white mb-4">
        慣老闆雷達
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

    <!-- Leaderboard Section -->
    <div class="max-w-2xl mx-auto">
      <ClientOnly>
        <HomeViolationLeaderboard />
        <template #fallback>
          <div
            class="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-xl p-8 text-center"
          >
            <div class="animate-pulse space-y-4">
              <div
                class="h-6 bg-gray-200 dark:bg-slate-700 rounded w-1/3 mx-auto"
              ></div>
              <div
                class="h-4 bg-gray-200 dark:bg-slate-700 rounded w-1/2 mx-auto"
              ></div>
            </div>
          </div>
        </template>
      </ClientOnly>
    </div>
  </div>
</template>
