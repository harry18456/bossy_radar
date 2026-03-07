## Why

目前公司頁的「薪資趨勢」tab 和追蹤清單頁的比較圖表都只呈現單一年份截面或分開的趨勢，無法一眼看出「獲利成長 vs 薪資成長」的相對落差。這是勞資談判中最核心的數據論點，也是求職者評估公司誠意的關鍵指標。

## What Changes

- **新增**：公司頁「薪資趨勢」tab — EPS vs 非主管薪資 **指數化成長折線圖**（以第一個有資料的年份為基準 100，呈現相對成長倍數）
- **新增**：公司頁「薪資趨勢」tab — **員工酬勞提撥比率趨勢圖**（`total_allocation_amount / pretax_net_profit × 100`，可視化分潤佔獲利的比例是否縮水）
- **新增**：追蹤清單頁 — **多公司跨年指數化趨勢圖**（同一圖上比較多間公司的中位數薪資指數化成長，不受 `selectedYear` 控制）

## Capabilities

### New Capabilities

- `company-indexed-growth-chart`: 公司頁指數化成長圖，將 EPS 與非主管薪資中位數在同一座標軸上指數化，直觀呈現相對成長差距
- `company-allocation-ratio-chart`: 公司頁員工酬勞提撥比率趨勢，前端計算提撥金額佔稅前淨利的百分比並繪製折線圖
- `watchlist-multi-company-trend`: 追蹤清單跨年多公司薪資指數化趨勢圖，利用已存在的 `allComparisonData`（全年份）繪製

### Modified Capabilities

（無現有 spec 需修改）

## Impact

- **修改檔案**：`app/components/company/YearlyStats.vue`（加入兩個新圖表區塊）
- **新增檔案**：`app/components/watchlist/TrendChart.vue`（新元件）
- **修改檔案**：`app/pages/watchlist.vue`（插入新元件）
- **不需要改動 API**：所需資料（`eps`、`median_salary`、`pretax_net_profit`、`total_allocation_amount`）在 static 和 dynamic 兩種模式下均已存在於現有 response
- **無新依賴**：使用已有的 `vue-chartjs` + `chart.js`
