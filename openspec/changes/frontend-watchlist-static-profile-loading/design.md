## Context

watchlist 頁面有兩條資料流：(1) 公司卡片 — 經 getCompanies({ company_code, page_size }) 取得追蹤公司基本資料後 hydrate 進 watchlist store；(2) 比較圖表 — 經 getYearlySummary({ company_code, include: ['all'] }) 取得跨年度摘要。前者因 page_size 是不存在的參數而被預設 size=20 截斷；後者因不帶 year 參數而下載全部 17 個年份檔（~42MB）後才在客戶端過濾。公司列表頁另有 limit:12 無人讀取的問題。三者根因都是 params 型別為 any。

後端 exporter（backend/app/services/export_service.py 的 export_yearly_summaries）組裝 YearlySummaryItem 的語意：
- 年份集合 = MOPS 各表的民國年 ∪ 違規 penalty_date 西元年減 1911 ∪ 環境違規同規則。
- violations_year_count / violations_year_fine = 該公司該年（penalty_date 西元年減 1911 等於該年）的筆數與罰額總和；penalty_date 為 null 的列不進任何年度桶。
- violations_total_count / violations_total_fine = 該公司**跨全部年份**的總筆數與總罰額（不是累計到該年）。
- env_violations_* 同上規則。
- employee_benefit / non_manager_salary / welfare_policy / salary_adjustment 以 (company_code, year) 精確配對。
- 某公司某年六種資料來源全空 → 該 (公司, 年) 不產生 item。

現有 public/data/companies/{code}.json（CompanyProfile）已包含組裝所需的全部原始資料：company、violations、environmental_violations、employee_benefits、non_manager_salaries、welfare_policies、salary_adjustments。

## Goals / Non-Goals

**Goals:**

- watchlist 的網路下載量與「追蹤公司數」成正比，與資料集總量脫鉤。
- 追蹤 N 間就完整顯示 N 間（卡片、比較表、各圖表），不再被 20 筆截斷。
- 客戶端組裝的 YearlySummaryItem 與 exporter 產出語意一致，圖表數字不因本次改動而改變。
- 公司列表頁每頁 12 筆於兩種 dataMode 一致。
- API 參數契約型別化，參數名打錯時 TypeScript 編譯失敗。

**Non-Goals:**

- 不改後端 export 格式或新增分片檔。
- 不移除 getYearlySummary / getYearlySummaryIndex API 介面（保留但不再被 watchlist 呼叫）。
- 不處理 L9（非 watchlist 頁面 _companies 為空）、M9（Zod runtime 驗證）、M3（autocomplete debounce）。
- 不動 dynamic 模式後端 API 的回應形狀。

## Decisions

### 比較資料改為平行抓取 per-company profile 並在客戶端組裝

**選擇**：watchlist 以 Promise.allSettled 平行呼叫 api.getCompanyProfile(code)（static 模式讀 companies/{code}.json、dynamic 模式打 profile API），再用新的純函式組裝 YearlySummaryItem[]。

**理由**：兩種 dataMode 都已有 getCompanyProfile，單一程式路徑同時修好兩種模式；下載量 = 追蹤數 × 單檔大小（數十 KB 級），對比現況 42MB 是數量級改善。

**捨棄方案**：(a) 後端新增 yearly-summaries/by-company/{code}.json 分片 — 需改 exporter 並等下次 export，REMEDIATION_PLAN 已確認現有 profile 足夠，不需要；(b) getYearlySummary 帶 year 參數逐年抓 — 仍下載全公司資料，無法與資料集規模脫鉤。

### 組裝邏輯抽為純函式 buildYearlySummaryItems

**選擇**：新增 frontend/app/utils/yearlySummary.ts，輸出 buildYearlySummaryItems(profile: CompanyProfile): YearlySummaryItem[]，嚴格複製 Context 段所列 exporter 語意。

**理由**：語意對等是本 change 的正確性核心（圖表數字不得改變），純函式可單元測試；放 utils 由 Nuxt 自動匯入。

**捨棄方案**：寫在 watchlist.vue 的 useAsyncData 內 — 無法測試、頁面檔膨脹。

### 公司卡片改由 getCompanyCatalog 過濾，繞開分頁契約

**選擇**：watchlist 的卡片資料改為 api.getCompanyCatalog() 取全清單後以追蹤代碼過濾，並映射為卡片所需的 Company 形狀（CompanyCard 僅使用 code、name、market_type、industry、capital、establishment_date、listing_date，皆為 CompanyCatalog 既有欄位）。

**理由**：徹底移除 watchlist 對分頁參數的依賴；dynamic 模式的 catalog 端點無 size 上限 100 問題；static 模式本來就是抓整份 catalog 再過濾（getCompanies 內部即如此），網路成本不變。

**捨棄方案**：改傳 size: watchedCodes.length — 仍受 dynamic 模式 size 上限 100 限制，且契約依賴留在頁面裡。

### 參數契約以 TypeScript 介面收斂

**選擇**：types/api.ts 新增 CompanyListParams（page、size、name、sort、industry、market_type、company_code）與 YearlySummaryParams（year、company_code、include），static 與 dynamic 的 getCompanies / getYearlySummary 簽名同時套用；companies 列表頁 limit:12 改 size:12。

**理由**：M11 指出 params:any 是 H1/M1 編譯通過的根因；兩個實作共用同一介面，參數漂移變成編譯錯誤。

**捨棄方案**：只改呼叫端參數名不加型別 — 無法防止再發。

### 引入 vitest 建立前端單元測試基礎

**選擇**：新增 vitest devDependency、frontend/vitest.config.ts（設定 ~ 別名指向 app/）、frontend/tests/unit/yearlySummary.spec.ts，package.json 加 test script，CI 在 lint 後執行 npm run test。

**理由**：組裝函式語意規則多（民國/西元轉換、null penalty_date、空年略過、total 非累計），無測試保護等同把 exporter 的正確性風險複製到前端。

**捨棄方案**：不加測試 — 違反專案測試要求；用 @nuxt/test-utils 全家桶 — 對純函式過重。

### watchlist store persist 註解修正

**選擇**：移除 stores/watchlist.ts 中「SSR 會自動 fallback 到 cookies」的不實註解（FRONTEND_AUDIT L10），改為據實描述僅 client localStorage。

**理由**：REMEDIATION_PLAN 規定 low 項須隨對應 change 處理，不得默默丟棄。

## Implementation Contract

**行為**：

1. 追蹤 N 間公司開啟 /watchlist 時，瀏覽器對年度資料的請求為 N 個 companies/{code}.json（或 dynamic 模式 N 個 profile API 呼叫）加一份 company-catalog.json；不得出現對 yearly-summaries/{year}.json 的任何請求。
2. 追蹤 25 間公司時，卡片區顯示 25 張卡片、比較表顯示 25 列；header 的「共追蹤 N 間」與實際顯示數一致。
3. buildYearlySummaryItems 對同一公司產出的每年 violations_year_count、violations_year_fine、violations_total_count、violations_total_fine、env_violations_*、non_manager_salary 等欄位值，與現行 public/data/yearly-summaries/{year}.json 內同公司同年的對應項完全相等（無資料年份同樣不產生 item）。
4. 任一公司 profile 抓取失敗時，其餘公司照常顯示，失敗公司沿用既有 fallback 列（計數 0、薪資 undefined）呈現於比較表；不得整頁空白或丟出未捕捉錯誤。
5. /companies 列表頁每頁顯示 12 筆，static 與 dynamic 模式一致。
6. 對 getCompanies 傳入 page_size 或 limit 等非契約參數名時，TypeScript 編譯（npx nuxi typecheck 或編輯器 tsc）必須報錯。

**介面 / 資料形狀**：

- buildYearlySummaryItems(profile: CompanyProfile): YearlySummaryItem[] — 輸出依 year 降冪排序。
- CompanyListParams：{ page?: number; size?: number; name?: string; sort?: string; industry?: string[] | string; market_type?: string[] | string; company_code?: string[] | string }。
- YearlySummaryParams：{ year?: number[] | number; company_code?: string[] | string; include?: string[] }。

**失敗模式**：

- 單一 profile 抓取失敗：Promise.allSettled 收集，僅該公司缺資料；fetchJson 既有 toast 錯誤提示維持不變。
- catalog 抓取失敗：useAsyncData error 狀態，沿用頁面既有錯誤/空狀態呈現。

**驗收**：

- npm run test 通過（含 exporter 語意對等測試：以實際 profile JSON 固定樣本對照對應 yearly-summaries 年檔內容）。
- npm run generate 成功（failOnError:true 下）。
- 本地 preview 與 production 部署後，以瀏覽器開 /watchlist（追蹤多間公司、含一間超過 20 的情境）檢查 Network 無 yearly-summaries 請求、console 零錯誤。
- /companies 頁面實際顯示 12 筆/頁。

**範圍邊界**：

- In scope：watchlist.vue、companies/index.vue、useStaticApi.ts、useApi.ts、types/api.ts、stores/watchlist.ts 註解、yearlySummary util 與其測試、vitest 設定、CI test 步驟、audit/remediation 文件勾選。
- Out of scope：後端任何檔案、export 格式、getYearlySummary 介面移除、L9/M9/M3。

## Risks / Trade-offs

- [追蹤數很大（如 50+）時平行請求數多] → 單檔僅數十 KB、瀏覽器自動排隊（HTTP/2 多工）；仍遠優於 42MB。必要時後續可加並發上限，不在本次範圍。
- [客戶端組裝與 exporter 語意日後漂移] → 單元測試以實際 export 樣本固定對照；後續 change 3（backend-atomic-static-export）抽共用函式時，本測試可續作回歸保護。
- [CompanyCatalog 映射為 Company 缺 last_updated 等欄位] → CompanyCard 實際只用 catalog 既有欄位；映射函式型別上以 Partial 補齊並避免 as any，缺欄位不影響卡片顯示。
- [vitest 與 Nuxt 自動匯入差異] → 測試只針對純函式，util 檔內以明確 import 撰寫，不依賴自動匯入魔法。
