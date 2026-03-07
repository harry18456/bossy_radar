## Context

前端目前使用 `vue-chartjs` + `chart.js`，公司頁 `YearlyStats.vue` 與追蹤清單頁的圖表元件均已建立。

資料層採雙模式：
- **static 模式**：從 `public/data/companies/{code}.json`（`CompanyProfile`）與 `public/data/yearly-summaries/{year}.json`（`YearlySummaryItem[]`）讀取，SSG 友善
- **dynamic 模式**：呼叫 FastAPI `/api/v1/companies/{code}/profile` 與 `/api/v1/companies/yearly-summary`

兩種模式的 response 結構相同，不需要任何 API 修改。

## Goals / Non-Goals

**Goals:**
- 在公司頁「薪資趨勢」tab 加入「EPS vs 薪資指數化成長」和「提撥比率趨勢」兩張圖
- 在追蹤清單頁加入「多公司薪資指數化趨勢」折線圖（跨年，不受 `selectedYear` 控制）
- static / dynamic 兩種模式行為一致
- 圖表遵循既有的 dark mode、responsive 慣例

**Non-Goals:**
- 不修改任何 API 或靜態 JSON 匯出邏輯
- 不加入新的第三方套件
- 不在公司頁加入多公司比較（那是追蹤清單的職責）

## Decisions

### 決策一：指數化計算在前端完成

**選擇**：前端從原始 `eps` / `median_salary` 數值自行計算指數（以第一個有效年份為基準 100）。

**理由**：
- 後端已提供原始數值，多一次計算不需要 API roundtrip
- 基準年的選取邏輯（第一個非 null 的年份）在前端 computed 中最容易控制
- static 模式下尤其重要——避免需要重新匯出靜態 JSON

**捨棄方案**：後端預先算好指數值——會讓 API 與展示邏輯耦合，且 static export 須重新產生。

### 決策二：追蹤清單跨年圖使用已有的 `allComparisonData`

**選擇**：`TrendChart.vue` 接收 `allComparisonData`（`YearlySummaryItem[]`，所有公司、所有年份）作為 prop，不新增任何 API 呼叫。

**理由**：
- `watchlist.vue` 已在載入時 fetch 全年份資料並存在 `allComparisonData`
- 追蹤清單頁不需要 `selectedYear`（跨年趨勢本來就要顯示全部年份）
- 無額外網路請求，效能最優

### 決策三：提撥比率由前端計算

**選擇**：`pretax_net_profit` 與 `total_allocation_amount` 皆為數值，前端直接計算 `ratio = (amount / profit) * 100`。

**理由**：
- `SalaryAdjustment.actual_allocation_ratio` 欄位為 string（如 `"3.5%"`），格式不統一，需要 parse，不如直接算數值版本
- 兩個原始欄位都已在 `CompanyProfile.salary_adjustments[]` 中

## Risks / Trade-offs

- **[資料缺漏]** 早年資料可能無 `eps` 或 `median_salary`，指數化基準年需往後移 → 前端略過 null 值，從第一個兩者皆有效的年份開始計算
- **[提撥比率分母為零]** `pretax_net_profit` 可能為 null 或 0 → 前端跳過該年份，不畫點
- **[追蹤清單只有一間公司]** 指數化趨勢圖意義減少 → 圖仍顯示，但加上提示「加入更多公司以比較趨勢」
- **[圖表數量增加導致頁面過長]** → 公司頁的兩張新圖沿用 `lg:col-span-2` grid，整合進既有 layout 不另加 section title

## Migration Plan

純前端新增，無 DB/API 異動，不需要 migration。直接合併即可。
