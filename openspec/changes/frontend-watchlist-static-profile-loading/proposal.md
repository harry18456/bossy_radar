## Why

追蹤清單（watchlist）頁面目前把**全部年度摘要 JSON（實測 ~42MB、17 個年份檔序列下載）**載入瀏覽器，只為了顯示少數幾間追蹤公司的比較資料；行動裝置會出現數秒主執行緒凍結甚至 OOM，且成本隨資料集成長（FRONTEND_AUDIT C1/M2）。同時存在兩個分頁參數契約 bug：watchlist 傳了不存在的 page_size 參數，追蹤超過 20 間公司時資料被靜默截斷成 20 筆（H1）；公司列表頁傳 limit:12 但兩種模式都不讀，實際每頁顯示 20 筆（M1）。根因是 API 參數型別為 any，參數名打錯完全無編譯訊號（M11）。

## What Changes

- **watchlist 比較資料改讀 per-company profile**：移除對 getYearlySummary 無年份全量載入的呼叫，改為平行抓取每間追蹤公司的 companies/{code}.json（static）或 profile API（dynamic），下載量與追蹤數成正比而非與資料集成正比。
- **新增純函式組裝年度摘要**：新增 utils 純函式，由 CompanyProfile 組裝出與後端 exporter 相同語意的 YearlySummaryItem 陣列（MOPS 民國年、違規 penalty_date 西元年減 1911、年度計數/罰額、跨年總計、無資料年份略過）。
- **watchlist 公司卡片改由 catalog 過濾**：移除 getCompanies({ company_code, page_size }) 呼叫，改用 getCompanyCatalog() 取得全清單後以追蹤代碼過濾，徹底繞開分頁契約且不受 dynamic 模式 size 上限 100 限制；追蹤幾間就顯示幾間，不再截斷成 20。
- **公司列表頁參數修正**：companies 列表頁的 limit:12 改為 size:12，兩種模式每頁一致顯示 12 筆。
- **參數契約型別化**：在 types/api.ts 新增 CompanyListParams 與 YearlySummaryParams 介面，套用到 static 與 dynamic 兩個 getCompanies / getYearlySummary 實作與所有呼叫端，杜絕參數名再漂移。
- **單一公司 profile 抓取失敗不得空白整頁**：以 Promise.allSettled 收集成功項，失敗公司顯示既有的 fallback 列。
- **修正 watchlist store 的 persist 註解**（FRONTEND_AUDIT L10，低風險順手項）：移除謊稱有 SSR cookie fallback 的註解。
- **建立前端單元測試基礎**：新增 vitest（devDependency）與組裝函式的單元測試，驗證與 exporter 的語意對等；CI 增加測試步驟。

## Non-Goals

- 不改後端 export 格式、不新增 yearly-summaries/by-company 分片（現有 companies/{code}.json 已含所需資料，REMEDIATION_PLAN 已確認）。
- 不移除 useStaticApi.getYearlySummary 與 getYearlySummaryIndex 既有 API 介面（無其他呼叫端，但留待後續清理，避免本次範圍膨脹）。
- 不處理 FRONTEND_AUDIT L9（_companies 在非 watchlist 頁面為空）：屬行為增強，與本次正確性修復無關。
- 不為全部 API 回應加 Zod runtime schema 驗證（M9，獨立議題）。
- 不調整 autocomplete debounce（M3，獨立議題）。

## Capabilities

### New Capabilities

- `frontend-watchlist-data-loading`: watchlist 頁面的資料載入行為 — 下載量與追蹤數成正比、不截斷追蹤清單、客戶端組裝的年度摘要與後端 exporter 語意一致、單一公司失敗不影響整頁。
- `frontend-company-list-pagination`: 公司列表頁分頁契約 — 每頁 12 筆於 static 與 dynamic 模式一致生效、API 參數以型別化介面約束。

### Modified Capabilities

(none)

## Impact

- Affected specs: frontend-watchlist-data-loading（新增）、frontend-company-list-pagination（新增）
- Affected code:
  - New:
    - frontend/app/utils/yearlySummary.ts
    - frontend/tests/unit/yearlySummary.spec.ts
    - frontend/vitest.config.ts
  - Modified:
    - frontend/app/pages/watchlist.vue
    - frontend/app/pages/companies/index.vue
    - frontend/app/composables/useStaticApi.ts
    - frontend/app/composables/useApi.ts
    - frontend/app/types/api.ts
    - frontend/app/stores/watchlist.ts
    - frontend/package.json
    - .github/workflows/ci.yml
    - docs/FRONTEND_AUDIT.md
    - docs/REMEDIATION_PLAN.md
  - Removed: (none)
