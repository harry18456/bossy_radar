## 1. 公司頁：EPS vs 薪資指數化成長圖

- [x] 1.1 在 `YearlyStats.vue` 新增 `indexedGrowthData` computed：過濾出同時有 `eps` 與 `median_salary` 的年份，計算指數（基準年=100），回傳 Chart.js Line 格式
- [x] 1.2 在 `YearlyStats.vue` 新增 `hasIndexedData` computed：同時有效年份數 ≥ 2 時為 true
- [x] 1.3 在 `YearlyStats.vue` 的 grid 中加入指數化成長圖區塊（`v-if="hasIndexedData"`），使用 `<Line>` 元件，藍色 EPS 線 + 黃色薪資中位數線
- [x] 1.4 設定雙座標軸 tooltip，hover 時顯示「EPS 指數：X」與「薪資中位數指數：X」，加上基準年標注說明文字

## 2. 公司頁：員工酬勞提撥比率趨勢圖

- [x] 2.1 在 `YearlyStats.vue` 新增 `allocationRatioData` computed：從 `sortedAdjustments` 計算每年 `total_allocation_amount / pretax_net_profit * 100`，`pretax_net_profit` ≤ 0 或 null 的年份值設為 null（Chart.js 自動跳過空點）
- [x] 2.2 在 `YearlyStats.vue` 新增 `hasAllocationRatioData` computed：至少一年比率可計算時為 true
- [x] 2.3 在 `YearlyStats.vue` 的 grid 中加入提撥比率趨勢圖區塊（`v-if="hasAllocationRatioData"`），使用紫色 `<Line>` 元件，Y 軸 label 為 `%`
- [x] 2.4 設定 tooltip callback，hover 時顯示：提撥比率(%)、提撥金額（格式化）、稅前淨利（格式化）

## 3. 追蹤清單：新增 WatchlistTrendChart 元件

- [x] 3.1 建立 `app/components/watchlist/TrendChart.vue`，props：`data: YearlySummaryItem[]`（全年份全公司）
- [x] 3.2 在元件中計算每間公司的指數化中位數薪資：找出所有公司共同最早有效年份作為基準，各公司各年份指數 = `median_salary / 基準年該公司 median_salary * 100`
- [x] 3.3 每間公司產生一條折線，從固定顏色陣列循環取色，Legend 顯示公司名稱
- [x] 3.4 實作 `hasData` computed（≥ 2 個不同年份有 `median_salary`）與 `isSingleCompany` computed，單公司時顯示提示文字
- [x] 3.5 設定 dark mode 支援（`useDark()`）、responsive、tooltip 顯示公司名 + 薪資中位數指數

## 4. 追蹤清單：整合 TrendChart 至 watchlist 頁

- [x] 4.1 在 `watchlist.vue` 的「綜合比較」section 中，`<WatchlistRadarChart>` 之後插入 `<WatchlistTrendChart :data="allComparisonData ?? []" />`
- [x] 4.2 確認 `allComparisonData` 型別為 `YearlySummaryItem[]`，element 含 `non_manager_salary.median_salary`，確保 TS 型別正確

## 5. 驗證

- [ ] 5.1 以 `NUXT_PUBLIC_DATA_MODE=static` 啟動開發伺服器，確認三張圖表正常顯示且資料正確
- [ ] 5.2 以 `NUXT_PUBLIC_DATA_MODE=dynamic` 啟動開發伺服器，確認三張圖表行為與 static 模式一致
- [ ] 5.3 驗證 dark mode 切換下三張圖的顏色正確
- [x] 5.4 確認資料為 null 的邊界情況：缺 `eps`、缺 `pretax_net_profit`、追蹤清單只有一間公司
