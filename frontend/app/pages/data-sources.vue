<script setup lang="ts">
useHead({
  title: '資料來源與說明 - 慣老闆雷達',
  meta: [
    { name: 'description', content: '慣老闆雷達 (Bossy Radar) 的資料來源、整合邏輯與免責聲明。' },
    { name: 'robots', content: 'noindex, follow' }
  ]
})

definePageMeta({
  layout: 'home'
})
</script>

<template>
  <div class="max-w-4xl mx-auto py-12 px-4 sm:px-6 lg:px-8">
    <div class="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-gray-100 dark:border-slate-800 p-8 sm:p-12">
      <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-8">資料來源與說明</h1>
      
      <div class="prose prose-slate dark:prose-invert max-w-none space-y-8">
        <!-- 專案簡介 -->
        <section>
          <p class="text-lg text-gray-600 dark:text-slate-300">
            <strong>慣老闆雷達 (Bossy Radar)</strong> 致力於整合政府公開數據，揭露企業的勞動違規紀錄與薪資福利狀況，期盼透過資訊透明化，建立一個更具勞權意識的職場環境。
          </p>
        </section>

        <!-- 1. 資料來源 -->
        <section>
          <h2 class="text-xl font-semibold text-gray-800 dark:text-slate-200 mb-4 flex items-center gap-2">
            <Icon name="lucide:database" class="w-5 h-5 text-blue-500" />
            資料來源 (Data Sources)
          </h2>
          <div class="space-y-4">
            <div>
              <h3 class="font-medium text-gray-900 dark:text-white">1. 公司基本資料</h3>
              <div class="text-gray-600 dark:text-slate-400 text-sm mt-1 space-y-1">
                <p>
                  <strong>資料權管單位</strong>：<a href="https://www.twse.com.tw/" target="_blank" rel="noopener" class="text-blue-600 hover:underline">台灣證券交易所 (TWSE)</a> 與 <a href="https://www.tpex.org.tw/" target="_blank" rel="noopener" class="text-blue-600 hover:underline">證券櫃檯買賣中心 (TPEX)</a>。
                </p>
                <p>
                  <strong>技術來源平台</strong>：<a href="https://mopsov.twse.com.tw/mops/web/t187sb03" target="_blank" rel="noopener" class="text-blue-600 hover:underline">公開資訊觀測站 (MOPS) 開放資料平台</a>。
                </p>
                <ul class="list-disc pl-5 mt-2">
                  <li><strong>TWSE</strong>：負責上市公司 (SII)。</li>
                  <li><strong>TPEX</strong>：負責上櫃公司 (OTC)、興櫃公司 (Emerging) 與公開發行公司 (Public)。</li>
                </ul>
                <p class="mt-2">
                  本站整合上述四類公司之基本資訊（代號、名稱、產業別、董事長等），資料源自 MOPS 開放資料之 CSV 檔案。
                </p>
              </div>
            </div>

            <div>
              <h3 class="font-medium text-gray-900 dark:text-white">2. 財務與薪資福利資料</h3>
              <p class="text-gray-600 dark:text-slate-400 text-sm mt-1">
                來源：<a href="https://mopsov.twse.com.tw/" target="_blank" rel="noopener" class="text-blue-600 hover:underline">公開資訊觀測站 (MOPS)</a>。
                <br>本站針對每一間上市公司，爬取並彙整了以下詳細數據：
              </p>
              <ul class="list-disc pl-5 mt-2 space-y-2 text-sm text-gray-600 dark:text-slate-400">
                <li>
                  <strong>全體員工福利與薪資 (t100sb14)</strong>：
                  <span class="block mt-0.5 text-xs text-gray-500 dark:text-slate-500">
                    包含「員工福利費用」、「員工薪資費用」、「員工人數」、「平均福利」、「平均薪資」以及每股盈餘 (EPS)。這是財務報告附註揭露的年度彙總。
                  </span>
                </li>
                <li>
                  <strong>非主管職務之全時員工薪資 (t100sb15)</strong>：
                  <span class="block mt-0.5 text-xs text-gray-500 dark:text-slate-500">
                    排除高階主管後的基層員工統計。關鍵指標包含「薪資總額」、「全時員工人數」、「平均薪資」以及反映實質所得分布的<strong>「中位數薪資」</strong>。
                  </span>
                </li>
                <li>
                  <strong>福利政策與調薪情形 (t100sb13)</strong>：
                  <span class="block mt-0.5 text-xs text-gray-500 dark:text-slate-500">
                    公司自我揭露的福利措施，包含「預計調薪幅度」、「實際調薪幅度」以及各學歷（高中、大學、碩士）從業人員的「起薪標準」。
                  </span>
                </li>
                <li>
                  <strong>基層員工調整薪資 (t222sb01)</strong>：
                  <span class="block mt-0.5 text-xs text-gray-500 dark:text-slate-500">
                    (113年起適用) 揭露年度稅前淨利、員工酬勞提撥比率及實際提撥情形。
                  </span>
                </li>
              </ul>
            </div>

            <div>
              <h3 class="font-medium text-gray-900 dark:text-white">3. 勞工違規紀錄</h3>
              <div class="text-gray-600 dark:text-slate-400 text-sm mt-1 space-y-1">
                <p>
                  <strong>來源</strong>：<a href="https://data.gov.tw/" target="_blank" rel="noopener" class="text-blue-600 hover:underline">政府資料開放平臺 (Data.gov.tw)</a>。
                </p>
                <p>
                  <strong>技術來源平台</strong>：<a href="https://apiservice.mol.gov.tw/OdService/download/A17000000J-030225-QDf" target="_blank" rel="noopener" class="text-blue-600 hover:underline">勞動部 Open Data API</a>。
                </p>
                <p class="text-xs text-slate-500 dark:text-slate-500">
                  (註：政府亦設有官方的 <a href="https://announcement.mol.gov.tw/" target="_blank" rel="noopener" class="text-blue-600 hover:underline">違反勞動法令事業單位（雇主）查詢系統</a> 供民眾查詢)
                </p>
                <p class="mt-2">
                  本站彙整了以下主要法規之裁罰紀錄：
                </p>
              </div>
              <ul class="list-disc pl-5 mt-2 space-y-1 text-sm text-gray-600 dark:text-slate-400">
                <li><strong>勞動基準法</strong>：如超時工作、未給付加班費、未依規定給予休假等。</li>
                <li><strong>性別工作平等法</strong>：如性別歧視、性騷擾防治措施不足等。</li>
                <li><strong>職業安全衛生法</strong>：如工作場所安全設施不足、未進行教育訓練等。</li>
                <li><strong>勞工退休金條例</strong> & <strong>勞工保險條例</strong>：如未依規定提繳退休金或投保.</li>
                <li><strong>就業服務法</strong>：如不實徵才廣告、非法解僱等.</li>
                <li><strong>其他相關法規</strong>：包含中高齡者及高齡者就業促進法、工會法等.</li>
              </ul>
            </div>

            <div>
              <h3 class="font-medium text-gray-900 dark:text-white">4. 環境違規紀錄 (新增)</h3>
              <div class="text-gray-600 dark:text-slate-400 text-sm mt-1 space-y-1">
                <p>
                  <strong>來源</strong>：<a href="https://data.moenv.gov.tw" target="_blank" rel="noopener" class="text-blue-600 hover:underline">環境部環境資料開放平臺</a>。
                </p>
                <p>
                  <strong>技術來源平台</strong>：<a href="https://data.moenv.gov.tw/dataset/detail/EMS_P_46" target="_blank" rel="noopener" class="text-blue-600 hover:underline">列管事業污染源裁處資料 (EMS_P_46)</a>。
                </p>
                <p class="mt-2">
                  本站彙整了以下環境保護相關法規之裁罰紀錄：
                </p>
                <ul class="list-disc pl-5 mt-2 space-y-1">
                  <li><strong>空氣污染防制法</strong>：如排放污染物超過標準、未依規定操作防制設備等。</li>
                  <li><strong>水污染防治法</strong>：如違規排放廢水、未取得排放許可等。</li>
                  <li><strong>廢棄物清理法</strong>：如非法棄置廢棄物、未依規定申報廢棄物流向等。</li>
                  <li><strong>毒性及關注化學物質管理法</strong>等其他相關環保法規。</li>
                </ul>
                <p class="mt-2 text-xs text-blue-600 dark:text-blue-400">
                  💡 <strong>特點</strong>：此資料集包含「統一編號」，本站透過統編進行<strong>精確比對</strong>，確保資料關聯之準確性。
                </p>
              </div>
            </div>
          </div>
        </section>

        <hr class="border-gray-100 dark:border-slate-800" />

        <!-- 2. 資料整合邏輯 -->
        <section>
          <h2 class="text-xl font-semibold text-gray-800 dark:text-slate-200 mb-4 flex items-center gap-2">
            <Icon name="lucide:git-merge" class="w-5 h-5 text-purple-500" />
            資料比對邏輯 (Data Matching)
          </h2>
          <div class="bg-gray-50 dark:bg-slate-800/50 rounded-lg p-5 text-sm text-gray-600 dark:text-slate-400 space-y-3">
            <p>
              由於政府開放資料中，違規紀錄通常僅提供「公司名稱」而無「統一編號」，因此本站必須進行資料比對（Fuzzy Matching）將違規紀錄連結至特定的上市櫃公司。我們採用以下多層次比對邏輯：
            </p>
            <ol class="list-decimal pl-5 space-y-2">
              <li>
                <strong>統編精確比對 (Exact Match)</strong>：針對環保裁罰等包含「統一編號」的資料，本站直接以統編進行 100% 精確關聯。
              </li>
              <li>
                <strong>精確名稱比對</strong>：若無統編，則比對違規紀錄的公司全名與上市櫃公司名稱是否完全一致。
              </li>
              <li>
                <strong>分公司與模糊比對</strong>：針對分公司或廠區（例如：「某某科技股份有限公司新竹廠」），我們會嘗試比對其總公司名稱。
              </li>
              <li>
                <strong>負責人輔助確認</strong>：在名稱相似度高但不完全相同時，會參考「負責人/董事長」姓名進行二次確認，以降低誤判率。
              </li>
            </ol>
            <p class="text-amber-600 dark:text-amber-500 flex items-start gap-2 mt-4">
              <Icon name="lucide:alert-triangle" class="w-4 h-4 mt-0.5 shrink-0" />
              <span>
                <strong>限制說明：</strong> 儘管我們已盡力優化比對演算法，但受限於原始資料格式與同名公司等因素，<strong>系統仍可能存在誤判或漏接的情況</strong>。
              </span>
            </p>
          </div>
        </section>

        <hr class="border-gray-100 dark:border-slate-800" />

        <!-- 3. 免責聲明 -->
        <section>
          <h2 class="text-xl font-semibold text-gray-800 dark:text-slate-200 mb-4 flex items-center gap-2">
            <Icon name="lucide:shield-alert" class="w-5 h-5 text-red-500" />
            免責聲明 (Disclaimer)
          </h2>
          <div class="space-y-3 text-gray-600 dark:text-slate-300">
            <p>
              1. 本網站所提供之資訊皆彙整自政府公開資料，<strong>僅供參考用途</strong>。
            </p>
            <p>
              2. 本網站<strong>不保證</strong>資料之即時性、完整性與 100% 準確性。實際違法與處分情形，應以勞動部及各縣市勞工局之正式公告為準。
            </p>
            <p>
              3. 使用者應自行判斷資訊之正確性，本網站不負擔因使用本站資訊而產生之任何直接或間接損失。
            </p>
          </div>
        </section>

        <!-- 4. 聯絡資訊 -->
        <section class="bg-blue-50 dark:bg-blue-900/10 rounded-xl p-6 border border-blue-100 dark:border-blue-900/20">
          <h2 class="text-lg font-semibold text-blue-800 dark:text-blue-300 mb-2 flex items-center gap-2">
            <Icon name="lucide:mail" class="w-5 h-5" />
            錯誤回報與聯絡
          </h2>
          <p class="text-blue-700 dark:text-blue-400 text-sm mb-3">
            如果您發現本站資料有誤，或是比對結果不正確（例如將 A 公司的違規誤植為 B 公司），歡迎來信指正，我們將儘速處理。
          </p>
          <a href="mailto:harry18456@gmail.com" class="inline-flex items-center gap-2 text-blue-600 dark:text-blue-400 font-medium hover:underline">
            harry18456@gmail.com
          </a>
        </section>

      </div>
    </div>
  </div>
</template>
