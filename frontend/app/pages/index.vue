<script setup lang="ts">
definePageMeta({
  layout: 'home'
})

usePageMeta({
  title: 'Bossy Radar',
  description: '台灣上市櫃公司薪資福利與違規紀錄查詢'
})
</script>

<template>
  <div class="flex flex-col items-center justify-center min-h-[60vh] text-center">
    <h1 class="text-4xl font-bold text-gray-900 dark:text-white mb-4">

      慣老闆雷達 <span class="text-2xl text-gray-500 font-normal">(Bossy Radar)</span>
    </h1>
    <p class="text-xl text-gray-500 dark:text-slate-400 mb-8 max-w-2xl">
      透明化職場資訊，避開慣老闆。<br>
      首頁與各項分析、免責聲明等網頁規劃中，請先前往公司列表搜尋。<br>
      <span class="text-sm text-red-400 mt-2 block">(目前數據仍有可能有錯誤，持續修復中)</span>
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
</template>
