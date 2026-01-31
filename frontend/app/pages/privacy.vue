<script setup lang="ts">
useHead({
  title: '隱私權政策 - 慣老闆雷達',
  meta: [
    { name: 'description', content: '慣老闆雷達 (Bossy Radar) 的隱私權政策，說明我們如何收集、使用與保護您的資料。' },
    { name: 'robots', content: 'noindex, follow' } // Privacy policy usually doesn't need to be indexed for SEO rank, but follow is okay.
  ]
})

definePageMeta({
  layout: 'home'
})
</script>

<template>
  <div class="max-w-4xl mx-auto py-12 px-4 sm:px-6 lg:px-8">
    <div class="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-gray-100 dark:border-slate-800 p-8 sm:p-12">
      <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-8">隱私權政策</h1>
      
      <div class="prose prose-slate dark:prose-invert max-w-none space-y-8">
        <section>
          <p class="text-gray-600 dark:text-slate-300">
            歡迎使用「慣老闆雷達 (Bossy Radar)」（以下簡稱本網站）。為了讓您能夠安心使用本網站的各項服務與資訊，特此向您說明本網站的隱私權保護政策，以保障您的權益，請您詳閱下列內容：
          </p>
        </section>

        <section>
          <h2 class="text-xl font-semibold text-gray-800 dark:text-slate-200 mb-4">一、隱私權保護政策的適用範圍</h2>
          <p class="text-gray-600 dark:text-slate-300">
            隱私權保護政策內容，包括本網站如何處理在您使用網站服務時收集到的個人識別資料。本隱私權保護政策不適用於本網站以外的相關連結網站，也不適用於非本網站所委託或參與管理的人員。
          </p>
        </section>

        <section>
          <h2 class="text-xl font-semibold text-gray-800 dark:text-slate-200 mb-4">二、資料的收集與使用 (Cookie 與 Local Storage)</h2>
          <p class="text-gray-600 dark:text-slate-300">
            本網站會使用 Cookie 及 Local Storage 技術，以便於提供更適合使用者個人需要的服務。Cookie 是網站伺服器用來和使用者瀏覽器進行溝通的一種技術，它可能在使用者的電腦中隨機儲存字串，用以辨識區別使用者。
          </p>
          <ul class="list-disc pl-5 mt-2 space-y-1 text-gray-600 dark:text-slate-300">
            <li><strong>系統運作必要：</strong> 我們使用 Local Storage 儲存您的偏好設定（如深色/淺色模式、追蹤清單等）。</li>
            <li><strong>分析與流量統計：</strong> 我們使用 Google Analytics 4 (GA4) 來分析網站流量，以優化使用者體驗。</li>
            <li><strong>廣告投放：</strong> 我們使用 Google AdSense 服務來顯示廣告。</li>
          </ul>
        </section>

        <section>
          <h2 class="text-xl font-semibold text-gray-800 dark:text-slate-200 mb-4">三、Google Analytics 4 (GA4) 聲明</h2>
          <p class="text-gray-600 dark:text-slate-300">
            本網站使用 Google Analytics 4 進行流量分析。GA4 可能會收集您的 IP 位址、瀏覽器類型、作業系統、造訪時間等資訊，但這些資料均已進行匿名化處理，本網站無法透過這些數據識別特定的個人。Google 把這些資訊是為了評估您對網站的使用，編制網站活動報告。
          </p>
        </section>

        <section>
          <h2 class="text-xl font-semibold text-gray-800 dark:text-slate-200 mb-4">四、Google AdSense 與 DoubleClick DART Cookie</h2>
          <div class="text-gray-600 dark:text-slate-300 space-y-4">
            <p>
              本網站使用 Google AdSense 服務投放廣告。Google 作為第三方供應商，會使用 Cookie 來依據使用者過往造訪本網站或其他網站的紀錄，向使用者投放廣告。
            </p>
            <p>
              Google 使用 DoubleClick DART Cookie，可讓 Google 及其合作夥伴根據用戶造訪本網站和/或網際網路上其他網站的紀錄，對用戶投放合適的廣告。
            </p>
            <p>
              您可以前往 <a href="https://myadcenter.google.com/" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:underline">Google 廣告中心</a> 選擇停用個人化廣告。
            </p>
          </div>
        </section>

        <section>
          <h2 class="text-xl font-semibold text-gray-800 dark:text-slate-200 mb-4">五、資料之保護</h2>
          <p class="text-gray-600 dark:text-slate-300">
            本網站採用 SSL (Secure Sockets Layer) 加密技術來傳輸資料，確保您的連線安全。網站託管於國際知名雲端服務平台 (Vercel)，利用其建置的防火牆與安全防護機制來保護網站運作安全。
          </p>
        </section>

        <section>
          <h2 class="text-xl font-semibold text-gray-800 dark:text-slate-200 mb-4">六、隱私權政策之修正</h2>
          <p class="text-gray-600 dark:text-slate-300">
            本網站隱私權保護政策將因應需求隨時進行修正，修正後的條款將刊登於網站上。
          </p>
          <p class="mt-4 text-sm text-gray-500">
            最後更新日期：2026 年 1 月 31 日
          </p>
        </section>
      </div>
    </div>
  </div>
</template>
