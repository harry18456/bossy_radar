## 1. 測試基礎與失敗測試（RED）

- [x] 1.1 引入 vitest 建立前端單元測試基礎：frontend/package.json 加入 vitest devDependency 與 "test": "vitest run" script、新增 frontend/vitest.config.ts（~ 別名指向 app/）。驗證：在 frontend/ 執行 npm run test 可啟動 vitest（暫無測試或 placeholder 通過皆可）。
- [x] 1.2 撰寫 buildYearlySummaryItems 的失敗單元測試 frontend/tests/unit/yearlySummary.spec.ts，覆蓋 spec「Client-assembled yearly summary SHALL match exporter semantics」全部情境：民國/西元年轉換（2024→113）、total 為跨全年總計而非累計、null penalty_date 不進年度桶但計入 total、六來源全空年份不產 item、year 降冪排序，並以 frontend/public/data/companies/ 下真實 profile 樣本對照 frontend/public/data/yearly-summaries/ 同公司同年欄位值相等。驗證：npm run test 此時失敗（util 尚未實作）。

## 2. 年度摘要組裝純函式（GREEN）

- [x] 2.1 依 design「組裝邏輯抽為純函式 buildYearlySummaryItems」實作 frontend/app/utils/yearlySummary.ts：buildYearlySummaryItems(profile: CompanyProfile): YearlySummaryItem[]，嚴格複製 exporter 語意（design Context 段所列規則）。驗證：npm run test 全數通過。

## 3. watchlist 頁面改造

- [x] 3.1 依 design「比較資料改為平行抓取 per-company profile 並在客戶端組裝」改寫 frontend/app/pages/watchlist.vue 的比較資料 useAsyncData：以 Promise.allSettled 平行呼叫 api.getCompanyProfile 後用 buildYearlySummaryItems 組裝，移除 getYearlySummary 呼叫；滿足 spec「Watchlist data download SHALL scale with watchlist size」與「A failed profile fetch SHALL NOT blank the watchlist」。驗證：dev server 開 /watchlist 追蹤 3 間公司，Network 面板僅見 3 個 companies/{code}.json 加 catalog、零個 yearly-summaries 請求；以 DevTools 把其中一個 profile 請求 block 後重載，其餘公司照常顯示且 console 無未捕捉錯誤。
- [x] 3.2 依 design「公司卡片改由 getCompanyCatalog 過濾，繞開分頁契約」改寫卡片資料來源：getCompanyCatalog() 取回後以追蹤代碼過濾並映射為 CompanyCard 所需欄位，移除 getCompanies({ company_code, page_size }) 呼叫；滿足 spec「Watchlist SHALL display every watched company」。驗證：dev server 追蹤 25 間公司，卡片區 25 張、比較表 25 列、header 計數 25。
- [x] 3.3 [P] 依 design「watchlist store persist 註解修正」修正 frontend/app/stores/watchlist.ts 的 persist 註解，據實描述僅 client localStorage、無 SSR cookie fallback。驗證：內容檢視，註解不再提及 cookies。

## 4. 參數契約

- [x] 4.1 [P] 修正 frontend/app/pages/companies/index.vue 的 queryParams 由 limit:12 改 size:12；滿足 spec「Companies list page SHALL show 12 items per page in both data modes」。驗證：dev server 開 /companies，每頁恰 12 張卡片、分頁總頁數以 12 計算。
- [x] 4.2 依 design「參數契約以 TypeScript 介面收斂」在 frontend/app/types/api.ts 新增 CompanyListParams 與 YearlySummaryParams，套用至 useStaticApi.ts 與 useApi.ts 的 getCompanies / getYearlySummary 簽名（移除 params?: any）；滿足 spec「Company list API parameters SHALL be statically typed」。驗證：暫時在任一呼叫端傳 page_size 觸發 tsc 編譯錯誤（確認防護生效後移除探針），npx nuxi typecheck 或編輯 hook 的 tsc 通過。

## 5. CI 與文件同步

- [x] 5.1 .github/workflows/ci.yml 前端 job 在 lint 後新增 npm run test 步驟，使 yearlySummary 語意對等測試成為 PR gate。驗證：workflow 檔內容檢視 + 本地 npm run test 通過。
- [x] 5.2 [P] 同步勾選 docs/FRONTEND_AUDIT.md（C1、H1、M1、M2、L10）與 docs/REMEDIATION_PLAN.md（change 2 標記完成）。驗證：內容檢視，勾選與實際完成項一致。

## 6. 端到端驗證

- [x] 6.1 本地 SSG 驗證：cd frontend && npm run generate 成功（failOnError:true 下零 prerender 錯誤），npx serve 或 nuxi preview 起本地站，瀏覽器開 /watchlist（含追蹤超過 20 間情境）與 /companies，console 零錯誤、Network 無 yearly-summaries 請求、每頁 12 筆。驗證：瀏覽器 console 與 Network 面板實測紀錄。
- [ ] 6.2 production 驗證：commit 並 push 部署 Vercel 後，瀏覽器開 production /watchlist 與 /companies，重複 6.1 檢查項，console 零錯誤。驗證：production 網址實測紀錄。
