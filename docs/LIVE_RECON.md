# Bossy Radar 生產環境唯讀勘查（Live Recon）

> 日期：2026-06-07
> 範圍：對線上站 `https://www.bossy.eraser.tw/` 做**唯讀** HTTP/瀏覽器勘查，目的是**校準** `BACKEND_AUDIT.md` / `FRONTEND_AUDIT.md` / `EXTENSION_AUDIT.md` 三份靜態稽核的優先級——不是重新找 bug。
> 工具：`curl`（HTTP 層：headers / 量級 / JSON 內容）+ Chrome（執行層：console / 渲染）。
> 守則：全程唯讀 GET，無寫入、無壓測、未對線上 API 發 `size=-1`，未碰第三方（104 / AdSense / GA）。

---

## 🔁 第二輪複查（2026-06-10）

> `frontend-ssg-correctness-and-headers`（commit `fc6478b`）已實作。以下對照原始碼修復狀態。**注意：LIVE_RECON 是對線上站勘查，原始碼修復須重新 `npm run generate` + Vercel 部署後才在生產生效。**

| §2 生產發現 | 修復狀態 | 證據 |
|---|---|---|
| 首頁預渲染空白 | **已修（待部署）** | `index.vue` 移除 ClientOnly/`server:false`，預渲染 HTML 已含排行榜資料 |
| console.log 外洩（IndustryEps 5 行） | **已修（待部署）** | `IndustryEps.vue` 5 處 console 全刪 |
| GA4 ID 印 console | **已修（待部署）** | `ga4.client.ts` dev 改 `gtag=()=>{}`，全檔 0 console |
| 缺安全標頭 | **已修（待部署）** | `vercel.json` 補了 X-Content-Type-Options/Referrer-Policy/Permissions-Policy/X-Frame-Options；CSP 於 change 0 補完整 script-src allowlist（見下，已解決）|
| watchlist 41MB（FE H1） | **未修** | fc6478b 未觸碰；仍 Critical |

**✅ 已由 change 0 `frontend-csp-hardening` 修正（待部署）。** 原始發現（⚠️ §4 自稱的「XSS 最後防線」名實不符）：`vercel.json:25-27` 的 CSP 原本只有 `object-src 'none'; base-uri 'self'; frame-ancestors 'self'`，**缺 `default-src`/`script-src`** → script 來源完全不受限。§4 把「補安全標頭」定位為「所有 stored-XSS 發現的最後防線」，但這道防線實際**未建立**。需在重新部署前補完整 `script-src`（self + 列明的 AdSense/GA 網域，最好 nonce 取代 inline），並先盤點廣告網域避免擋廣告（§4 自己也叮囑了這點）。

---

## 1. 部署現況（最重要的重排訊號）

| 事實 | 證據 |
|------|------|
| 託管在 **Vercel**、純靜態 SSG | `Server: Vercel`、`X-Vercel-Cache: HIT`、`dataMode` 實際走 `/data/*.json` |
| **FastAPI API 完全沒對外曝露** | `/api/v1/companies/catalog` → **404**、`/api/v1/companies/?size=1` → **404**、`/docs` → **404**；`api.bossy.eraser.tw` 無法解析 |

**影響**：`BACKEND_AUDIT.md` 的整組 API 層發現（`size=-1` 全表傾印 DoS、`/companies/catalog` 無分頁、`yearly-summary` 記憶體爆量、CORS+credentials、`/docs` 曝露、無 rate limit……）在**目前生產環境不可被攻擊**，因為沒有公開 API。它們從「High，立即」降為「**latent — 只有日後將 dynamic API 對外部署才會咬**」。

→ backend 報告中**仍然立即有效**的是「資料完整性」那組（無 disposition_no 重複插入、靜默失敗報成功、export 非原子 rmtree、create_all 無 migration），因為那發生在你跑 ETL/export 時，與 API 是否曝露無關。

---

## 2. 生產環境坐實的發現

| 報告項 | 確認結果 | 證據 |
|--------|---------|------|
| FE H1 watchlist 巨量載入 | **Critical 成立**：17 個年度檔 = **3.79 MB 壓縮傳輸（brotli）+ 41 MB 解壓後在瀏覽器解析**。傳輸尚可，但 41MB parse/GC + 持有記憶體 = 低階行動裝置真凍結 | `113.json` 單檔 raw 5.8MB；17 檔加總 raw 41MB / br 3.79MB |
| FE H2 首頁預渲染空白 | **成立**：首頁 HTML 僅 23KB，含 **5 個 `animate-pulse` 骨架、0 個 `/companies/` 排行榜連結**，有「最新年度排行」標題但無資料；排行榜靠客戶端 JS 後補 | `curl` HTML grep + console 顯示 `No salary_by_industry in data null` 先於資料到達 |
| FE L15 console.log 外洩 | **成立**：生產 console 實際印出 IndustryEps 5 行 debug + 完整資料物件 | `Checking year 115/114/113 for EPS data... Object`、`Found EPS data in industry: Object`、`Found year with EPS data: 113` |
| （新）GA4 ID 印進 console | 生產 console 印出 measurement ID | `[GA4] Initializing Production Mode with ID: G-473WGPY5QN`（半公開資訊，低風險，但屬 debug 殘留） |
| 三報告共同：缺安全標頭 | **成立**：只有 `HSTS`，其餘全缺 | ✗ CSP、✗ X-Content-Type-Options、✗ Referrer-Policy、✗ X-Frame-Options、✗ Permissions-Policy；✓ `Strict-Transport-Security: max-age=63072000` |

---

## 3. 被部署環境緩解／可下調的

| 報告項 | 校準 | 證據 |
|--------|------|------|
| FE M4 soft-404（200 可索引 thin content） | **下調**：Vercel 對未預渲染路由回**真正的 404**，直接爬蟲命中已被緩解；僅客戶端 SPA 導航才走 in-component 200 path | `/companies/INVALIDXYZ` → **HTTP 404**；`/companies/2330` → 200 |
| FE 儲存型 XSS / EXT stored XSS | **下調為 latent**：漏洞真實，但目前**無任何觸發資料** | catalog（780KB）+ 抽樣 `2330/2317/1101/2603` profile（含台積電 38 筆違規文字、台泥 146KB）**全部 0 個 `<`/`>`** |
| BE API 層 DoS 整組 | **下調為 latent**：無公開 API，目前不可利用 | 見 §1 |

---

## 4. 淨結論：修復優先序重排

1. **最該先修（與部署無關、現在就有效）**
   - 前端 watchlist 41MB（FE H1）—— 真實使用者現在就會中
   - 後端資料完整性（重複插入、靜默失敗、export 非原子）—— 每次跑 ETL/export 就發生
   - **補安全標頭**（CSP / X-Content-Type-Options / Referrer-Policy / X-Frame-Options / Permissions-Policy）—— 一個 `vercel.json` 的 `headers` 就能補，CP 值極高，且是所有 XSS 發現的最後防線
   - 移除 IndustryEps / GA4 的 debug console.log（FE L15）
2. **重要但可排後（latent，等資料變髒 / 開 API 才咬）**
   - 前端 stored-XSS 轉義、擴充 innerHTML 轉義、backend API 層 DoS
3. **可下調**
   - soft-404（Vercel 已處理）

> 安全標頭建議（`vercel.json`）方向：`Content-Security-Policy`（允許 self + `pagead2.googlesyndication.com` / GA 網域 + `'unsafe-inline'` 給 dark-mode inline script，或改 nonce）、`X-Content-Type-Options: nosniff`、`Referrer-Policy: strict-origin-when-cross-origin`、`X-Frame-Options: SAMEORIGIN`、`Permissions-Policy`。實作前需先盤點 AdSense/GA 需要的網域，避免擋掉廣告。

---

## 附錄：原始勘查輸出（摘要）

```text
# 首頁標頭
HTTP/1.1 200 OK | Server: Vercel | X-Vercel-Cache: HIT
Strict-Transport-Security: max-age=63072000
Access-Control-Allow-Origin: *      # 靜態公開內容，無 auth/cookie，低風險
(無 CSP / X-Content-Type-Options / Referrer-Policy / X-Frame-Options / Permissions-Policy)

# API 曝露
/api/v1/companies/catalog  -> 404
/api/v1/companies/?size=1  -> 404
/docs                      -> 404
api.bossy.eraser.tw        -> 無法解析

# 量級（brotli 壓縮）
company-catalog.json : 779,964 bytes raw
yearly-summaries 全 17 檔 : 41 MB raw / 3.79 MB br（watchlist 一次全載）
leaderboards.json : 411,772 bytes raw

# soft-404
/companies/INVALIDXYZ -> 404 (text/html)

# stored-XSS 可達性
catalog '<'=0 '>'=0
2330/2317/1101/2603 profile '<'=0 '>'=0

# 首頁預渲染
23,158 bytes | animate-pulse x5 | /companies/ 連結 x0 | 有「最新年度排行」標題

# 生產 console（執行層）
[GA4] Initializing Production Mode with ID: G-473WGPY5QN
No salary_by_industry in data null
Checking year 115/114/113 for EPS data... Object
Found EPS data in industry: Object  /  Found year with EPS data: 113
```
