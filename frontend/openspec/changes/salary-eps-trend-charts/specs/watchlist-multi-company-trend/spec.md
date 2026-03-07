## ADDED Requirements

### Requirement: 追蹤清單顯示多公司薪資中位數指數化跨年趨勢圖
追蹤清單頁（`watchlist.vue`）中，當追蹤公司數 ≥ 1 且 `allComparisonData` 包含至少 2 個不同年份的有效 `median_salary` 資料時，SHALL 在現有「綜合比較」區塊的最後顯示 `WatchlistTrendChart` 元件。

計算規則：
- 以所有追蹤公司中最早出現 `median_salary` 有效值的年份為「共同基準年」，設為 100
- 每間公司各自一條折線，顏色不同
- 若某公司某年無 `median_salary`，該年該公司不畫點
- X 軸：年份（升冪），Y 軸：指數值（無單位）
- 圖表不受 `selectedYear` 影響，永遠顯示所有年份

#### Scenario: 有足夠資料時顯示圖表
- **WHEN** 追蹤清單 ≥ 1 間公司，且 `allComparisonData` 中有 ≥ 2 個不同年份含有效 `median_salary`
- **THEN** `WatchlistTrendChart` 元件顯示，每間公司一條折線

#### Scenario: 只有一個年份資料時隱藏
- **WHEN** 所有資料集中在同一年份（或僅一年有 `median_salary`）
- **THEN** 圖表不顯示

#### Scenario: 某公司特定年份缺資料時折線出現缺口
- **WHEN** 公司 A 在 2021 年無 `median_salary`，2020 和 2022 有
- **THEN** 公司 A 的折線在 2021 出現斷點，2020 和 2022 正常連線

#### Scenario: 切換 selectedYear 不影響趨勢圖
- **WHEN** 使用者變更年份選擇器
- **THEN** `WatchlistTrendChart` 的顯示內容不變（不依賴 `selectedYear`）

#### Scenario: 清單僅一間公司時仍顯示並提示
- **WHEN** 追蹤清單只有 1 間公司且有跨年資料
- **THEN** 圖表顯示該公司折線，並附加提示文字「加入更多公司以進行趨勢比較」

#### Scenario: static 與 dynamic 模式下行為一致
- **WHEN** `NUXT_PUBLIC_DATA_MODE` 為 `static` 或 `dynamic`
- **THEN** 元件使用相同的 `allComparisonData` prop，`YearlySummaryItem.non_manager_salary.median_salary` 在兩種模式下皆可存取
