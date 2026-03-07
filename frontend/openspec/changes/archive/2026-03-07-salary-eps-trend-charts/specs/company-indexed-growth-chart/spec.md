## ADDED Requirements

### Requirement: 顯示 EPS 與非主管薪資中位數的指數化成長折線圖
公司頁「薪資趨勢」tab 的 `YearlyStats.vue` 中，當 `non_manager_salaries` 至少有兩年同時具有 `eps` 與 `median_salary` 有效值時，SHALL 顯示一張指數化成長折線圖。

計算規則：
- 以第一個 `eps` 與 `median_salary` 皆非 null 的年份為基準年，設為 100
- 其後每年指數 = (當年值 / 基準年值) × 100
- 兩條線：「EPS 指數」（藍色）、「非主管薪資中位數指數」（黃色）
- X 軸為年份，Y 軸為指數值（無單位）

#### Scenario: 有足夠資料時顯示圖表
- **WHEN** `non_manager_salaries` 包含至少 2 年同時有 `eps` 與 `median_salary` 的資料
- **THEN** 圖表顯示，兩條折線皆從基準年的 100 出發

#### Scenario: 基準年之前的 null 年份被略過
- **WHEN** 最早年份的 `eps` 或 `median_salary` 為 null，後續年份有值
- **THEN** 以第一個兩者皆有效的年份為基準，null 年份不畫點

#### Scenario: 資料不足時隱藏圖表
- **WHEN** 同時有 `eps` 與 `median_salary` 的年份少於 2 年
- **THEN** 圖表區塊不顯示（`v-if` 條件為 false）

#### Scenario: static 與 dynamic 模式下行為一致
- **WHEN** `NUXT_PUBLIC_DATA_MODE` 為 `static` 或 `dynamic`
- **THEN** 圖表使用相同的 `non_manager_salaries` prop 資料，呈現結果相同

#### Scenario: Dark mode 下樣式正確
- **WHEN** 使用者切換至深色模式
- **THEN** 圖表背景、座標軸顏色、折線顏色符合 `isDark` 條件分支
