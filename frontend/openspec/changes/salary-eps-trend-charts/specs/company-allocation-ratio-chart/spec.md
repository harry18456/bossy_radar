## ADDED Requirements

### Requirement: 顯示員工酬勞提撥比率趨勢折線圖
公司頁「薪資趨勢」tab 的 `YearlyStats.vue` 中，當 `salary_adjustments` 至少有一筆同時具有有效 `pretax_net_profit`（> 0）與 `total_allocation_amount` 的資料時，SHALL 顯示提撥比率趨勢折線圖。

計算規則：
- 提撥比率 (%) = `total_allocation_amount / pretax_net_profit × 100`
- 若某年 `pretax_net_profit` 為 null 或 ≤ 0，該年不畫點（顯示缺口）
- Y 軸單位：%，X 軸：年份
- 折線顏色：紫色（`#8b5cf6`）

#### Scenario: 有有效資料時顯示圖表
- **WHEN** `salary_adjustments` 包含至少 1 筆 `pretax_net_profit > 0` 且 `total_allocation_amount` 非 null 的資料
- **THEN** 提撥比率趨勢圖顯示

#### Scenario: 分母為零或 null 時該年略過
- **WHEN** 某年 `pretax_net_profit` 為 null 或 0
- **THEN** 該年不繪製資料點，折線在該年出現缺口

#### Scenario: 所有年份皆無有效資料時隱藏圖表
- **WHEN** 所有 `salary_adjustments` 的 `pretax_net_profit` 皆為 null 或 ≤ 0
- **THEN** 圖表區塊不顯示

#### Scenario: static 與 dynamic 模式下行為一致
- **WHEN** `NUXT_PUBLIC_DATA_MODE` 為 `static` 或 `dynamic`
- **THEN** 圖表使用相同的 `salary_adjustments` prop 資料，計算結果相同

#### Scenario: Tooltip 顯示原始數值輔助說明
- **WHEN** 使用者 hover 某年的資料點
- **THEN** Tooltip 顯示：提撥比率（%）、提撥金額、稅前淨利
