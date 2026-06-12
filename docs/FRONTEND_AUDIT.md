# Bossy Radar 前端稽核報告

> 產出日期：2026-06-07
> 方法：8 個面向平行深讀 → 每個 critical/high/medium 發現派獨立 agent 對抗式驗證（讀真實程式碼嘗試反駁，部分實跑 Node/V8、unhead 序列化、真實 JSON 檔驗證）→ 跨面向綜整。
> 規模：51 個 agent、664 次工具呼叫。
> 結果：**57 個發現，49 個成立、8 個被推翻**（誤報率 14%，其中包含一個被誤判為 critical 的 XSS）。
>
> 嚴重度為「對抗式驗證後的調整值」(adjusted_severity)，可能低於初判。
> 勾選框供逐項處理追蹤。範圍：`frontend/app/**` + 設定檔（已排除 `.agent/` vendored 檔）。

---

## 🔁 第二輪複查（2026-06-10）

> 對照當前程式碼重新對抗式驗證。`frontend-ssg-correctness-and-headers`（commit `fc6478b`）已實作並 archive。

**已修復（fc6478b，待重新部署生效）** — 經實際讀 code 確認修對、無回歸：
- **H2** 首頁 leaderboards 改 SSG：`index.vue:21-24` 已移除 `server:false`/`ClientOnly`，實測 `.output/public/index.html` 含真實排行榜連結（`/companies/2619` 等）。
- **H4** `failOnError:true`（`nuxt.config.ts:125`）+ CI 新增 `npm run generate` 會擋壞 build。
- **H5** `dataMode` 預設改 static（`nuxt.config.ts:8-11` + `.env.example`）。
- **M8** AdSense loader 改條件注入 guard（`nuxt.config.ts:88-97`）。
- **L15** IndustryEps `console.log` 已清；**L2** footer rel **僅 index.vue 擴充連結修了**（footer 自身仍缺，見下 NF3）。

**仍成立（尚未動工，逐項確認）**：~~C1 / H1 / M1 / M2 watchlist 41MB + 分頁契約 bug（`page_size`/`limit`）~~（已修，change 2 `frontend-watchlist-static-profile-loading`，2026-06-13）、H3 autocomplete ARIA、M4 無 `error.vue`、M5/M6/M7 a11y、M9/M11 型別安全（M11 的 getCompanies/getYearlySummary 已型別化，其餘 params:any 仍在）— 其餘仍在，零誤判。

**新發現（本輪，報告原本遺漏）**
- ✅ **NF1 [HIGH]（已修，change 0 `frontend-csp-hardening`，待部署）`vercel.json` CSP 形同虛設**（`frontend/vercel.json:25-27`）：CSP 只有 `object-src 'none'; base-uri 'self'; frame-ancestors 'self'`，**缺 `default-src` 與 `script-src`** → 未列出的 `script-src` 完全不受限，等於允許任意來源 / inline script。fc6478b 自稱補的「所有 stored-XSS 的最後防線」實際**未建立**，且 REMEDIATION_PLAN 完成判準抓不到此半套修復。修法：補明確 `script-src 'self' https://pagead2.googlesyndication.com https://www.googletagmanager.com …` + `connect-src`/`frame-src`，先盤點 AdSense/GA 網域避免擋廣告，最好以 nonce 取代 inline。**重新部署前處理。**
- ✅ **NF2 [Low]（已修，change 0）生產 console 殘留**（`AdSenseUnit.vue:37,53`、`useStaticApi.ts:27/49/58`、`stores/company.ts:23`）：fc6478b 只清了 IndustryEps/GA4，AdSense 重試/錯誤路徑仍會印。包 `import.meta.dev` 守衛或移除。
- ✅ **NF3 [Low]（已修，change 0）footer 外連缺 `rel="noopener noreferrer"`**（`AppFooter.vue:142,146`，= 報告 L2，change 0 已補）。

---

## 整體判斷

**做得好的部分（已驗證）**
- **無 XSS**：全 app 無 `v-html`、`innerHTML`、`eval`、`Function`、`document.write`；所有 scraped 政府文字（公司名、地址、違規內容）都走 Vue mustache 自動轉義。
- **JSON-LD 注入是安全的**（這點推翻了初判 critical）：unhead v2.1.2 的 `tagToString` 會把 script innerHTML 內的 `</script` 轉成 `<\/script`，breakout 不成立。
- `runtimeConfig.public` 只暴露非機密 id（appVersion/dataMode/apiBase/adsense/ga），無 secret 外洩。
- Chart.js 用 vue-chartjs wrapper（unmount 自動 destroy，無記憶體洩漏）、explicit registration（tree-shaking 正確，非 `registerables`）。
- SEO 基礎扎實：per-page title/description、canonical/OG/Twitter、build-time sitemap、`lang=zh-TW`、公司頁因 `await useAsyncData` 取得唯一 title。
- `compressPublicAssets`（gzip+brotli）已開、AdSense 用 IntersectionObserver lazy-load + 固定 min-height 抑制 CLS。

**真正的問題集中在五個系統性根因**
1. static JSON 邊界無 runtime 驗證（型別只在編譯期）
2. 資料/狀態邊界刻意抹除型別安全（`params: any` / `as any`）
3. static vs dynamic 雙模式各自實作、行為漂移
4. 整個 dataset 送進瀏覽器 client-side 處理
5. 靜默失敗／fail-open 作為預設（`failOnError:false`、`dataMode` 預設 dynamic、吞錯）

---

## 🔴 五大最優先（綜整建議）

| # | 問題 | 位置 | 為何優先 |
|---|------|------|---------|
| P1 | watchlist 載入 **全部年度 ~42-49MB JSON** 只為顯示少數公司 | `useStaticApi.getYearlySummary` | 唯一 critical；行動裝置數秒凍結/OOM，頁面實質不可用 |
| P2 | 分頁參數契約 bug（`page_size`/`limit` vs `size`） | watchlist + companies 頁 | 確認的正確性缺陷：追蹤 >20 間公司靜默掉資料；列表忽略自己的 12 顯示 20。根因是 `params:any` |
| P3 | 建置 fail-loud + 出貨正確模式（`failOnError:true` + `dataMode` 預設 static） | `nuxt.config.ts` | 三個 config 缺陷複合 → 靜默出貨壞站；一行/設定修正、blast radius 極大 |
| P4 | 首頁 leaderboards `server:false` → 預渲染 HTML 空白 | `pages/index.vue` | 確認 high SEO：首頁是主要爬蟲目標卻 ship 空白排行榜，違背 SSG 目的 |
| P5 | error.vue boundary + 共用元件最低限度 a11y（autocomplete combobox、icon aria-label、skip link） | `app/`、shared 元件 | 無 error.vue（已驗證）；autocomplete 對螢幕報讀器不可用（HIGH）；皆觸及共用元件、每頁繼承 |

---

## 🔴 Critical（驗證後）

### [x] C1. watchlist 把全部年度摘要（~42-49MB JSON）載入瀏覽器只為顯示少數公司 ✅ 已修（change 2：改平行抓 per-company profile + 客戶端組裝，下載量與追蹤數成正比）
- **面向**：performance
- **位置**：`frontend/app/composables/useStaticApi.ts:193-223`（`getYearlySummary`），由 `pages/watchlist.vue:63-66` 呼叫
- **問題**：watchlist 呼叫 `getYearlySummary({ company_code, include:['all'] })` **無 year 參數**，於是 `yearsToLoad = [...index.years]`（全部），對每年 `await fetchJson` 後 concat。**實測** `public/data/yearly-summaries/` 17 個檔共 ~42MB（107-114.json 各 ~5MB）。`company_code` 過濾在**載入全部之後**才做（zero download 節省）。即使只追蹤 1 間公司也下載整個歷史資料集。而且 `await` 在 for-loop 內 → 17 個 round-trip 序列化。
- **影響**：行動裝置上數秒主執行緒 parse/GC 凍結、高記憶體；慢速連線/低 RAM 裝置實質壞掉；成本隨資料集成長（非隨 watchlist）。
- **修法**：後端 ETL 匯出 per-company 年度分片（`yearly-summaries/by-company/{code}.json`），或單一 company_code-keyed 索引；至少把 `company_code` 過濾推到只抓需要的分片；`Promise.all` 平行化。

---

## 🔴 High（驗證後）

### [x] H1. watchlist 用 `page_size`（不存在的參數）→ >20 間追蹤公司被靜默截斷成 20 ✅ 已修（change 2：卡片改 getCompanyCatalog 過濾，實測 25 間全顯示）
- **面向**：data-fetching（high）/ pages-routing（medium）
- **位置**：`frontend/app/pages/watchlist.vue:27-30`
- **問題**：`api.getCompanies({ company_code, page_size: watchedCodes.length })`。static 與 backend 都只認 `size`（`page_size` 全前端僅此一處、無人讀）。`Number(undefined)||20` → 預設 20。`hydrateCompanies` 整批替換 `_companies`，grid、`sortedComparison`、比較表、salary/EPS/radar 圖全被截斷成 20，但 header 仍顯示「共追蹤 N 間」。dynamic 模式同樣壞（且硬上限 100）。
- **修法**：改傳 `size: watchedCodes.length`；以明確 company_code 清單抓取時應跳過分頁回傳全部；用 typed param 介面防再漂移。

### [x] H2. 首頁 leaderboards 用 `server:false` → SSG 預渲染首頁 ship 空白排行榜 ✅ 已修（fc6478b，待部署）
- **面向**：pages-routing（seo）
- **位置**：`app/pages/index.vue:21-25`
- **問題**：首頁是 SEO/行銷入口，唯一資料（violation/salary 排行）用 `useAsyncData(..., { server:false })` 抓，且每個排行榜區塊再包 `<ClientOnly>`。**實測**已產出的 `.output/public/index.html` 只含骨架占位、**零真實資料**（無 `台塑石化`、無 `/companies/6505` 連結）。爬蟲與無 JS 使用者看到空白，首屏有 empty→populated 閃動。`leaderboards.json` 是環境無關的本地檔，可在 build time 讀取。
- **修法**：拿掉 `{ server:false }` 與 ClientOnly，改 server-side（預渲染時 FS 直讀）baked 進靜態 HTML；dynamic API 情況保留 pending fallback。

### [ ] H3. 搜尋 autocomplete 缺 ARIA combobox/listbox 語意（螢幕報讀器無法使用）
- **面向**：a11y
- **位置**：`app/components/company/CompanyAutocomplete.vue:161-169`（input）、`187-221`（ul/li）
- **問題**：自製鍵盤導覽（Arrow/Enter/Esc + `selectedIndex`）但完全不暴露給輔助技術：input 無 `role=combobox`/`aria-expanded`/`aria-controls`/`aria-autocomplete`/`aria-activedescendant`、無 `id`；下拉是純 `ul/li` 無 `role=listbox/option`/`aria-selected`/per-option id。`CompanyFilterBar` 的 `<label for="search">` 連不到任何 input。報讀器使用者收不到「出現建議」「目前選項」「結果數」。
- **影響**：公開資訊平台的主要搜尋功能對報讀器使用者實質不可用。
- **修法**：補完整 combobox ARIA（role/aria-* 如上）、input 給 id 連 label、加 `aria-live` 結果數區域。

### [x] H4. `nitro.prerender.failOnError:false` 靜默出貨壞掉/不完整的 SSG 站 ✅ 已修（fc6478b）
- **面向**：config / reliability
- **位置**：`nuxt.config.ts:115-122`
- **問題**：`getCompanyUrls()` 餵 ~2615 條 `/companies/{code}` 進 prerender；任一頁渲染丟例外（缺檔/壞 JSON/fetch 失敗）時，Nuxt 只 warn 並繼續、**exit 0**。**驗證** nitropack 原始碼：只有 `failOnError===true` 才會 throw。CI（`.github/workflows/ci.yml`）只跑 eslint、不跑 `nuxt generate` → prerender 失敗永不被發現。
- **影響**：一筆壞匯出記錄或暫時錯誤 → 公開站缺頁/空頁、零建置訊號、爬蟲索引死頁。
- **修法**：`failOnError:true`（或 prod/CI build gate）；若有少數已知壞 route 要容忍，明確從 routes 過濾而非全域吞錯。

### [x] H5. `dataMode` 預設 `'dynamic'` 但 production 需 `'static'` → 缺 env 出貨錯模式 ✅ 已修（fc6478b）
- **面向**：config / reliability
- **位置**：`nuxt.config.ts:44`
- **問題**：`dataMode: process.env.NUXT_PUBLIC_DATA_MODE || 'dynamic'`。production 是 SSG/static（兩份 CLAUDE.md + 作者本地 `.env`），但 **committed `.env.example` 是空值** → 解析為 `dynamic` → `useDynamicApi` 打 `apiBase` 預設 `http://localhost:8000`。乾淨 checkout / 新 CI / 新貢獻者的 build 全指向 localhost，全站資料呼叫失敗。作者本地 `.env`（gitignored）正確，所以自己沒踩到。
- **影響**：一個忘記/空的 env → 全站打 localhost:8000、空白頁、無建置訊號（與 H4 複合）。
- **修法**：預設改 `static` 對齊 production，或值非 static/dynamic 時 fail build；`.env.example` 設 `NUXT_PUBLIC_DATA_MODE=static`。

---

## 🟠 Medium（驗證後）

### [x] M1. companies 列表頁傳 `limit:12` 但兩模式都不讀 → 每頁顯示 20 而非 12 ✅ 已修（change 2：size:12 + satisfies CompanyListParams，實測 12/頁、218 頁）
- **面向**：data-fetching / pages-routing
- **位置**：`app/pages/companies/index.vue:28`
- **問題**：`queryParams` 含 `limit:12` 無 `size`。static `getCompanies` 用 `Number(params?.size)||20`；backend 用 `size`（FastAPI 丟棄 `limit`）。兩模式都 fallback 20。SSG production 顯示 20/頁，dynamic 顯示 12，內部不一致。
- **修法**：統一參數名 `size:12`（或讓 static 把 `limit` 當 `size` 別名）。挑一套 param 契約給兩個 `useApi` 實作共用。

### [x] M2. `getYearlySummary` 無 year 參數時每次呼叫載入並 concat 全部年份檔 ✅ 已修（change 2：watchlist 不再呼叫 getYearlySummary；該函式保留但已無呼叫端）
- **面向**：data-fetching / performance
- **位置**：`useStaticApi.ts:193-223`
- **問題**：與 C1 同根，但泛指所有無 year 的呼叫。序列化 `await` for-loop、無 memoization、`company_code` 過濾在 load 之後。
- **修法**：`Promise.all` 平行化、composable 內 memoize；有 `company_code` 時優先讀 per-company profile JSON。

### [ ] M3. 整個 780KB / 2615 筆公司 catalog 在主執行緒每次按鍵 filter+sort
- **面向**：performance
- **位置**：`useStaticApi.getCompanies`；`CompanyAutocomplete.vue:43-86`
- **問題**：**實測** `company-catalog.json` = 779,964 bytes / 2615 筆。autocomplete 的 `suggestions` computed 每次按鍵對全部 2615 筆 `filter().sort().slice(0,10)`，**無 debounce**。（companies 列表頁 `name` 只在明確搜尋時 commit，故不受每鍵影響——這點比初判輕，故由 high 降 medium。）
- **修法**：autocomplete query debounce ~150-200ms、極短 query early-return；規模化考慮預建搜尋索引（minisearch/trie）。

### [ ] M4. 無 `error.vue` error boundary + 404 變成 soft-404（HTTP 200 可索引）
- **面向**：pages-routing（reliability）/ a11y-seo（SEO）
- **位置**：缺 `app/error.vue`（已驗證）；`companies/[id].vue:129-143` 錯誤分支
- **問題**：無 `error.vue`，render 期或非 await setup 的例外落到 Nuxt 預設未品牌化錯誤頁。`[id]` 的「找不到此公司資料」回 **HTTP 200 可索引 thin content**（無 `createError`/`noindex`/canonical 控制）。`failOnError:false` 下未預渲染的公司頁在 runtime 也依賴此路徑。
- **修法**：加 `app/error.vue`（品牌化 404/500 + `clearError()` + `robots:noindex`）；`[id].vue` 未知 code 時 `throw createError({ statusCode:404 })` 而非 render 可索引 200。

### [ ] M5. 無 skip-to-content 連結（WCAG 2.4.1）
- **面向**：a11y
- **位置**：`layouts/default.vue:5-34`、`home.vue:8-27`
- **問題**：兩個 layout 第一個可聚焦元素都不是 skip link，`<main>` 也無 id。sticky header 多個連結 + theme toggle，鍵盤/報讀器使用者每次導覽都要 tab 過 header。
- **修法**：layout 第一個子元素加 `<a href="#main" class="sr-only focus:not-sr-only">跳到主要內容</a>`，`<main id="main">`。（附帶：`companies/index.vue:84` 有巢狀 `<main>`，多重 landmark，另一小 a11y 問題。）

### [ ] M6. icon-only header/footer 連結無可靠 accessible name
- **面向**：a11y
- **位置**：`AppHeader.vue`（watchlist 23-38、brand 44-55）、`AppFooter.vue`（buymeacoffee 139、github 143）
- **問題**：heart/brand 連結只靠 `title` + 裝飾 Icon（`@iconify/vue` 預設 `aria-hidden`）；**GitHub 連結完全無 accessible name**（icon-only、無 title/aria-label/text）。
- **修法**：每個 icon-only 連結/按鈕加 `aria-label`（追蹤清單/回品牌首頁/GitHub 原始碼/請我喝杯咖啡），內層 Icon `aria-hidden=true`。

### [ ] M7. 公司頁 tab 導覽未以 ARIA tabs 暴露
- **面向**：a11y
- **位置**：`companies/[id].vue:224-241`（nav/buttons）、panels 247/347/377/719
- **問題**：四 tab（基本資料/薪資趨勢/違規紀錄/員工福利）是 `<nav aria-label="Tabs">` 內純 button + v-if panel，無 `role=tablist/tab/tabpanel`、無 `aria-selected`、無 roving tabindex、無方向鍵。button 仍可聚焦/Enter 觸發、文字會被報讀，故非 blocker，但 active 狀態與 tab 語意缺失。
- **修法**：套 WAI-ARIA tabs（tablist/tab/tabpanel + aria-selected + tabindex + Left/Right 方向鍵）。

### [x] M8. AdSense loader 無條件注入、env 缺時送 `client=undefined` ✅ 已修（fc6478b）
- **面向**：config（reliability）/ performance / security（consent）
- **位置**：`nuxt.config.ts:84-89`
- **問題**：`app.head.script` 無守衛地注入 `adsbygoogle.js?client=${process.env...}`，直接讀 `process.env`（非 runtimeConfig 的 `|| ""` fallback）。env 未設時 ship `client=undefined`，每頁一個壞的跨域請求。對照 GA4（`ga4.client.ts` 有 `if(!gaId) return`）與 `AdSenseUnit.vue`（守 `adClient`），唯獨此 loader 無守衛、也無 consent gating。
- **修法**：僅在 AdSense ID 非空時條件式注入（mirror GA4 守衛）；讀 runtimeConfig 而非 raw `process.env`；考慮 consent gating（Consent Mode v2）。

### [ ] M9. static JSON 形狀無 runtime 驗證；`types/api.ts` 契約僅編譯期
- **面向**：config / correctness
- **位置**：`useStaticApi.ts:32-62/168-174/226-235`
- **問題**：`fetchJson<T>` 只 `JSON.parse` 後當作 T，無對 `~/types/api` 的 runtime 驗證；catalog 列 `as unknown as Company`、violations `as any`、sort 盲索引 `a[key]`。後端匯出若改欄位名/型別/巢狀，邊界不丟錯，UI 靜默 render 錯/空/undefined（配 `failOnError:false` 連 build 都不掛）。
- **修法**：用既有 Zod 為 static JSON 形狀（catalog/profile/yearly/leaderboards）定 runtime schema，在 `fetchJson` 邊界 parse，mismatch 時明確報錯；驗證後移除 `as unknown as`/`as any`。

### [ ] M10. 非平凡 client-side 邏輯零自動測試
- **面向**：config / maintainability
- **位置**：`package.json:6-14`（無 vitest/playwright）
- **問題**：無測試框架（兩份 CLAUDE.md 自承）。但有大量未測邏輯：`useStaticApi` client-side filter/null-aware sort/pagination、`useCompanyFilters` URL↔state 雙向同步、`format.ts` 的 ROC↔西元/currency、`AdSenseUnit` retry timing。
- **修法**：加 Vitest（+ @nuxt/test-utils），先測 `format.ts` 邊界與 `useStaticApi` paginate/sort/filter + market-type mapping，再加 Playwright 對 companies 列表與公司頁的 smoke test。

### [ ] M11. 型別安全在資料/狀態邊界被侵蝕（`params:any`、`as unknown as`、`as any`、`@ts-ignore`）
- **面向**：config / maintainability
- **位置**：`useStaticApi.ts`/`useApi.ts` 全部 `params?: any`、172 `as unknown as`、234 `as any`；`useCompanyFilters.ts:119` `@ts-ignore`
- **問題**：所有 `params` 為 `any` → query 參數 key 打錯靜默無感（H1/M1 的 `page_size`/`limit` 正是因此編譯通過）。ESLint 把 `no-explicit-any`/`ban-ts-comment` 降為 warn。
- **修法**：引入 typed params 介面（由 `CompanyFilters` 衍生）給所有 `get*`；以驗證過的 mapper 取代 cast；`updateFilter` 泛型化移除 `@ts-ignore`；清乾淨後把規則調回 error。

---

## 🟡 Low（多為未獨立驗證或驗證後降級，集中列出）

| # | 問題 | 位置 | 修法摘要 |
|---|------|------|---------|
| [ ] L1 | AdSense+GA4 無 consent gating（PDPA/GDPR 疑慮） | `nuxt.config.ts`/`ga4.client.ts` | consent banner 或 Consent Mode v2 後才注入 |
| [ ] L2 | footer 外連 `target=_blank` 缺 `rel=noopener noreferrer` | `AppFooter.vue:139/143` | 補 rel（與全站其他連結一致） |
| [ ] L3 | `[id]` route param 原樣進 fetch 路徑，無 client 驗證 | `useStaticApi.getCompanyProfile` | `[id].vue` 加 `validate`/guard `^[A-Za-z0-9]+$`，否則 404 |
| [ ] L4 | static `getViolations` 回 `{pages:0}` via `as any` 偏離 `PaginatedResponse` | `useStaticApi.ts:226-235` | 回 `total_pages:0` 並正確 typed（目前無 caller，dead） |
| [ ] L5 | `getCompanies` 用 Date 建構式偽造 `last_updated` | `useStaticApi.ts:169-172` | 別偽造；optional 或讀真實 export 時間戳（目前無 UI 綁定） |
| [ ] L6 | `market_type` mapping 有重複 `'OTC'` 值、僅存於 static | `useStaticApi.ts:133-142` | 移除重複；集中 mapping 給兩模式共用 |
| [ ] L7 | `fetchJson` 吞錯後 rethrow，非 useAsyncData caller 可能未處理 rejection | `useStaticApi.ts:57-61` | 統一錯誤策略；`getYearlySummary` 的 index 讀加 fallback；console gate `import.meta.dev` |
| [ ] L8 | Zod `filterSchema` 宣告卻從未 `.parse()`（文件謊稱有驗證） | `useCompanyFilters.ts:4-13` | 實際 `safeParse` URL query，失敗 fallback 預設 |
| [ ] L9 | watchlist `_companies` 重載後對非 watchlist 頁的 consumer 為空（但 count 非零） | `stores/watchlist.ts` | persist 最小顯示投影，或從 catalog lazy hydrate |
| [x] L10 | persist `storage` 註解謊稱有 SSR cookie fallback ✅ 已修（change 2） | `stores/watchlist.ts:60-66` | 修正/移除註解 |
| [ ] L11 | catalog cache 吞 fetch 錯誤、無 error state、無 stale-while-revalidate | `stores/company.ts:22-26` | 暴露 error ref；TTL 過期時背景 revalidate |
| [ ] L12 | `formatDate` 用 `toLocaleDateString('zh-TW')`，時區依賴 + hydration mismatch | `utils/format.ts:18-29` | 用 UTC 元件或固定時區格式化（負時區訪客 off-by-one） |
| [ ] L13 | `companies/[id].vue` 936 行 God component（兩段 ~140 行違規表格近重複） | `companies/[id].vue` | 抽 `<ViolationTable>`/`<WelfarePolicyCard>`；`isValidUrl`/`ensureProtocol` 移到 utils |
| [ ] L14 | `usePageMeta`/structured-data 用 setup 期非反應式快照 | `companies/[id].vue:32-58` | 傳 reactive getter；`watchEffect` 重注入 schema |
| [ ] L15 | `IndustryEps.vue` 殘留 5 個 `console.log`（dump 整個 leaderboard payload） | `components/home/IndustryEps.vue:9-35` | 刪除（對齊乾淨的 `IndustrySalary.vue`）；CI 加 no-console gate |
| [ ] L16 | 薪資差距門檻單位混用（仟元值比 100，helper 文字說 10 萬） | `SalaryMetrics.vue:105/198/210` | 抽具名常數帶單位註解；統一顯示單位 |
| [ ] L17 | `Pagination` 以陣列 index 為 key（含重複 `...` sentinel） | `Pagination.vue:54` | 以穩定值為 key（`'p'+page` / `'dots-'+index`） |
| [ ] L18 | `AnimatedNumber` 收到非數值時 render `NaN` | `AnimatedNumber.vue:16-24` | watcher/computed 加 `Number.isFinite` 守衛 |
| [ ] L19 | Chart.js 在 12 個檔重複全域 register（冗餘、易漏） | 各 chart 元件 | 集中到 `plugins/chartjs.client.ts` 註冊一次 |
| [ ] L20 | 多個 chart 元件 prop 為 `any[]`（已有 `NonManagerSalary` 型別卻沒用） | `YearlyStats.vue:32`/`MinWageChart.vue:27` | import 共用型別 |
| [ ] L21 | 公司頁 chart 元件 eager bundle、無 lazy hydration/code-split | `companies/[id].vue` | 用 `<Lazy*>`/`defineAsyncComponent` + `hydrateOnVisible` 把 Chart.js 切 chunk |
| [ ] L22 | `Pagination` 硬編 light 色（dark 模式對比破）+ 無 `aria-current` | `Pagination.vue` | 補 `dark:` variant 與 `aria-current=page` |
| [ ] L23 | OG/Twitter image 用相對路徑（部分爬蟲要絕對 URL） | `usePageMeta.ts:13/30/39` | `${siteUrl}` 前綴 |
| [ ] L24 | deindex 僅靠 per-page noindex、robots.txt 全開放 | `nuxt.config.ts:110`/`robots.txt` | 可接受；選擇性集中 noindex 策略 |

---

## ✅ 被推翻的誤報（8 個，展示驗證價值）

| 初判 | 問題 | 推翻理由 |
|------|------|---------|
| **Critical** | JSON-LD stored XSS（scraped 公司名/地址經 `JSON.stringify`+innerHTML 進 ld+json） | **unhead v2.1.2 `tagToString` 自動把 script 內 `</script` 轉成 `<\/script`**；實測 payload 不 breakout、JSON 仍合法。框架層已防護（此誤報在 security-xss 與 a11y-seo 兩面向各出現一次，皆推翻）。 |
| High | sort comparator null 處理違反全序、會 throw | **實測 V8 不會 throw**（即使 `()=>1` 也不丟）；null 在 asc/desc 都正確沉底，可見結果正確且確定性。僅 null 之間相對序未定義（無害）。 |
| Medium | static MOPS/violations 端點 404+toast+throw | `getEmployeeBenefits` 等四方法**零 caller**（MOPS 資料實際走 `getCompanyProfile` 內嵌）。是 dead code 陷阱、非 runtime 失敗。 |
| Medium | filter↔URL 雙向同步 race / 同 tick 重複 `router.replace` | **Vue watcher 預設 flush:'pre' 批次去重**，一次邏輯操作只觸發一次 replace；輸入綁 local ref 不影響每鍵。無可觀察缺陷。 |
| Medium | 負 EPS 被 `\|\| 0` 靜默歸零 | **JS 中負數是 truthy**，`-3.2 \|\| 0 === -3.2`，無 sign loss。負 EPS 由 Chart.js 軸 `min:0` clamp 到底部（正確排序），非歸零。 |
| Medium | `format.ts` ROC regex 把 8 位西元日期 +1911 / 輸出 'NaN' | regex `^(\d{2,3})[-/]?(\d{2})[-/]?(\d{2})$` **最多 7 位**，8 位 `20231101` 不可能 match；實資料全為 ISO `YYYY-MM-DD`。`rocToWestern` 是 dead code。`Intl` 對 NaN 回 '非數值' 非 'NaN'。 |
| Medium | JSON-LD config 重複項 | 同 critical，unhead 已轉義。 |

> 教訓：JSON-LD `innerHTML` + `JSON.stringify` 在**純 JS 層確實**有 `</script>` breakout 風險——只是這個 Nuxt/unhead 版本剛好幫你轉義了。若未來換掉 unhead、或自行用原生 DOM 注入，這個 critical 會復活。**建議仍主動轉義**（`replace(/</g,'\\u003c')`）作為 defense-in-depth，不要依賴框架隱性行為。

---

## 待後續確認（建議下一輪）

- [ ] **CSP 與安全標頭**：有 AdSense+GA4+inline script 卻無 CSP/nonce、無 `X-Content-Type-Options`/`Referrer-Policy`/`Permissions-Policy`（`nitro.routeRules` 未設）。
- [ ] **隱私/consent gating**：GA4+AdSense 無 consent banner（台灣 PDPA 下或可接受，但 posture 未評估）。
- [ ] **sitemap 規模化健康**：2615+ route prerender + `failOnError:false` 的互動、build time/memory、部分失敗靜默跳過；sitemap 無 lastmod/priority。
- [ ] **各頁 loading/empty/error 狀態審視**：公司無違規/薪資資料時的空狀態、chart 元件骨架。
- [ ] **i18n**：全 zh-TW 硬編碼、無 i18n 層（品牌名 bilingual 意圖未決）。
- [ ] **bundle 分析**：catalog 列表頁實際 ship 了什麼（是否帶了只有公司頁需要的 Chart.js）。

---

## 附錄：跨面向系統性根因

1. **static JSON 邊界無 runtime 驗證** — `fetchJson<T>` 盲信形狀；`useCompanyFilters` 宣告 Zod 卻不 `.parse()`。
2. **型別安全在資料/狀態邊界被刻意抹除** — `params:any`/`as any` 是整個 data-fetching 正確性 cluster 的機械根因（四個分頁 bug 因此編譯通過）。
3. **static vs dynamic 雙模式漂移** — 兩實作各自寫、無共用契約或測試釘住。
4. **整個 dataset 在瀏覽器 client-side 處理** — catalog 每鍵 filter/sort、watchlist concat 全部年份；ETL 匯出 flat dump 把切片全推給瀏覽器。
5. **靜默失敗/fail-open 為預設** — `failOnError:false`、`dataMode` 預設 dynamic、store 吞錯、script 無條件注入。
6. **a11y 是事後補的** — 共用 primitive（icon 連結、autocomplete、Pagination、tabs、skip link）皆有缺口，每頁繼承。
7. **SSG/SSR 非確定性渲染風險** — 首頁 `server:false` ship 空白、`last_updated` 偽造、`toLocaleDateString` 時區依賴 → hydration mismatch。
