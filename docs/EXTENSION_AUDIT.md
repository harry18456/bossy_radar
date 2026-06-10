# Bossy Radar 瀏覽器擴充功能稽核報告

> 產出日期：2026-06-07
> 對象：Chrome/Edge Manifest V3 擴充功能（zero-build 純 JS，4 個檔 901 行），在 104.com.tw 頁面注入 widget 顯示公司違規/薪資。
> 方法：5 個面向平行深讀 → 每個 critical/high/medium 發現派獨立 agent 對抗式驗證（追 source→sink 路徑、確認攻擊者可控性、MV3 機制是否已緩解）→ 跨面向綜整。
> 規模：22 個 agent、157 次工具呼叫。
> 結果：**25 個發現，22 個成立、3 個被推翻**。
>
> 嚴重度為「對抗式驗證後的調整值」。勾選框供逐項處理追蹤。

---

## 🔁 第二輪複查（2026-06-10）

> 對照當前程式碼重新對抗式驗證。擴充 remediation（changes 6-7）**尚未動工**。注意實際檔案在子目錄（`content-scripts/`、`background/`），行號與報告扁平路徑略有差異。

**仍成立（逐項確認，零修復、零誤判）**：H1/H2/H3 三個 `innerHTML` XSS sink（`content-scripts/main.js:356/408/411`）、M1 無 escape 層、M2 `custno=` 不限 domain 且 P3 最高（`interceptor.js:148-181`）、M3 SW 無 schema 驗證、L2/L3/L4/L6/L7/L8/L10/L11/L14 — 全部仍在。
- 關鍵釐清：`57be302`/`276ffed` 兩 commit 都在報告基準（6-07）**之前**，未影響 M2 判定；`is104Domain` 只守 response body（P2），**不守 URL param（P3）**，M2 攻擊面完整保留。
- 出貨完整性複核通過：`manifest.json` 當前 `0.3.4`，與 `store/bossy-radar-0.3.4.zip` **逐檔一致**、無版本漂移；所有 zip 已 gitignore、未被 git 追蹤（L14 的「git 追蹤殘留」已不成立，僅剩本地磁碟雜物）。

**新發現（本輪，較報告更廣）**
- 🟠 **NF1 [Medium] 隱私政策矛盾範圍比 M4 更廣**（`PRIVACY_POLICY.md` vs `content-scripts/main.js:161-243` `fetchTaxIdBySlug`）：政策只承認「在職缺頁透過 104 API 取統編」，但實際會**主動 fetch 104 的 `/company/ajax/content|summary/{slug}`、甚至 fallback 抓整頁 company HTML，且帶使用者已登入的 104 session cookie**，範圍超出政策宣稱。屬 Web Store「準確揭露」下架風險。修法：政策揭露 per-company 請求 + `fetchTaxIdBySlug` 主動帶 cookie 探測。
- 🟡 **NF2 [Low] `fetchTaxIdBySlug` HTML fallback 無上限/timeout**（`main.js:230-240`）：`await htmlRes.text()` 對整頁 104 HTML 無 `Content-Length`/timeout/Content-Type 守衛，直接跑 regex。加 `AbortSignal.timeout`、限制讀取大小。
- 🟡 **NF3 [Low] `extension/CLAUDE.md` 仍描述已移除的 `dispatched=true` latch**（= L5）：`57be302` 已改 priority 系統，但文件未更新，會誤導後續 AI agent 的威脅模型評估。

---

## 整體判斷

**做得好的部分（已驗證）**
- **權限極精簡**：只有 `storage` + 單一 `https://www.bossy.eraser.tw/*` host_permission；無 `tabs`/`scripting`/`<all_urls>`/eval/remote code。
- **interceptor monkey-patch 寫得謹慎**：fetch wrapper 一律呼叫原始函式、re-throw、用 `response.clone()` 讀 body（**不消耗頁面需要的 stream** — 避開最危險的相容性陷阱）；XHR patch 保留 `this`、轉發所有參數。
- **interceptor 無外送**：grep 確認無 console/fetch/sendBeacon/navigator/Image，攔截到的 tax ID/URL/response body **不離開 main world**，只經 DOM attribute + CustomEvent 橋接。
- **tax_id 在比對端有 UBN checksum 驗證**（`isValidUBN`），且只當 Map key 用、成功路徑不進 innerHTML。
- **slug 經 `[a-zA-Z0-9]+` regex 限制**，`fetchTaxIdBySlug` 無 path traversal。
- 出貨的 0.3.4 zip 與原始碼一致、版本無漂移；舊 zip 已 gitignore。

**真正的問題集中在三個系統性根因**
1. **未轉義的資料進 innerHTML**（widget 全靠 raw template string + `.innerHTML`，全 codebase 無任何 escape/sanitize helper）
2. **main↔isolated 世界橋接無信任邊界**（`data-bossy-tax-id` 屬性與 CustomEvent 任何 main-world script 都能偽造）
3. **把「格式正確」當成「可信/正確」**（UBN checksum、URL_PARAM 最高優先級、200 即當合法 JSON）

---

## 🔴 三大最優先（綜整建議）

| # | 問題 | 位置 | 為何優先 |
|---|------|------|---------|
| P1 | 消除 innerHTML sink：用 textContent/DOM API（或 escape helper）重建 widget，並移進 Shadow DOM | `main.js` 三個 render 函式 | 一次收斂 3 個 high + 1 個 medium XSS 發現；修 sink 即中和所有來源 |
| P2 | 跨世界橋接加明確信任閘：tax_id 綁定顯示中的公司、`custno=` 限 104 domain、每個讀取點都驗證 | `interceptor.js` + `main.js` | UBN checksum 只證「格式對」非「正確/來自本擴充」；攻擊者可換掉顯示的公司並回顯進 innerHTML |
| P3 | 強化 service worker：schema 驗證 + 限大小 catalog/company 回應、fetch timeout、`res.json()` Content-Type 守衛、拒絕不信任 sender | `service-worker.js` | worker 是 innerHTML sink 的上游餵食者，未驗證資料快取 24h → 一次壞回應汙染整天每次瀏覽（cache poisoning → stored XSS） |

> **隱私政策**（P4，非程式碼）：`PRIVACY_POLICY.md` 宣稱「不傳送任何瀏覽行為至任何伺服器」，但每次看公司頁都 fetch `/data/companies/{code}.json` → 伺服器（依 IP+時間）必然知道使用者在查哪些公司。屬商店上架合規風險，需修正措辭。

---

## 🔴 High（驗證後）— 三條 DOM XSS 路徑，同一個 innerHTML sink

> **共同根因**：`main.js` 三個 render 函式（`createWidget`:272、`renderCompanyData`:356、`renderNotFound`:408）全用 raw template string 指派給 `.innerHTML`，**全 codebase 無任何 escape/sanitize/DOMPurify helper**（grep 零命中）。main.js 是 content script，注入的 markup 落在 104.com.tw 的共享 DOM。
>
> **重要 CSP 注意**：`innerHTML` 不會執行注入的 `<script>`，但 `<img src=x onerror=...>`/`<svg onload=...>` 的 inline handler 會觸發。最終能否執行任意 JS 取決於 **104.com.tw 自己的 CSP**（是否擋 inline handler）；即使 CSP 嚴格，HTML/DOM 注入（clickjacking「查看完整報告」連結、竄改 widget）仍成立。修法一致：escape 或 textContent。

### [ ] H1. 反射型 DOM XSS：104 頁面公司名 → `renderNotFound` innerHTML
- **面向**：dom-xss / bridge-trust
- **位置**：`main.js:411`（sink）、`getCompanyNameFromDOM`:97-158（source）、caller :598
- **問題**：`renderNotFound` 把 `${name}` 直接插進 innerHTML，`name` 來自 `document.querySelector('h1').textContent`、`og:title` meta、anchor textContent —— **全部頁面可控**（任何人可在 104 張貼帶 XSS payload 的公司/職缺名；og:title 可被 MITM）。「找不到」是任何 DB 缺漏公司的**預設路徑**，故常態觸發。textContent 讀出的字面 payload 再經 innerHTML 重新解析會復活成 live HTML（mutation XSS，104 自己的輸出轉義救不了）。
- **修法**：`escapeHtml(name)`，或用 `createElement`+`textContent` 建構 not-found 區塊。

### [ ] H2. 儲存型 DOM XSS：scraped catalog 公司名 → `renderCompanyData` innerHTML
- **面向**：dom-xss
- **位置**：`main.js:358`（sink），source = `/data/company-catalog.json` 的 `name`
- **問題**：`${catalogItem.name}` 直接進 innerHTML，`name` 來自 scraper→DB→static JSON pipeline（後端稽核已認定不可信）。任一筆記錄的公司名（或未來若 render address/violation_content/welfare 文字）含 markup → 對每個看該公司的使用者在 104 origin 執行（全使用者基數 blast radius）。
- **修法**：對 `catalogItem.name` 及所有自由文字欄位 escape；一致套用而非只 name。

### [ ] H3. DOM XSS：未驗證的 `data-bossy-tax-id` 橋接屬性 → `renderNotFound` innerHTML
- **面向**：bridge-trust（初判 critical，因 104 CSP 條件性降 high）
- **位置**：`readTaxIdFromDOM`:494（無驗證讀取）、`showNotFound`:597、`renderNotFound`:413（sink）
- **問題**：成功比對路徑有 `isValidUBN` 守門，但**失敗路徑沒有**。`readTaxIdFromDOM()` = `getAttribute('data-bossy-tax-id')` **零驗證**；`data-bossy-tax-id` 在 documentElement 上、**任何 main-world script（104 JS、注入廣告、其他擴充）都能寫入**任意 HTML。攻擊者寫 `<img src=x onerror=...>` → 不過 `isValidUBN` → 不比對 → `detectedTaxId` 為 null → 逾時後 `showNotFound` 用 raw 屬性 → 進 innerHTML 執行。
- **修法**：`readTaxIdFromDOM` 不過 `isValidUBN` 就回 null；render 前再驗一次；改 textContent。把 `data-bossy-tax-id` 與 CustomEvent detail 在**每個讀取點**都視為完全不可信。

---

## 🟠 Medium（驗證後）

### [ ] M1. 無 HTML 轉義層（系統性 root）
- **面向**：dom-xss
- **位置**：`createWidget`:272、`renderCompanyData`:356、`renderNotFound`:408
- **問題**：三個 render 全 raw innerHTML，無 escape util（textContent 只用於「讀」頁面與靜態 'BR' 標籤）。架構（CLAUDE.md「rebuild innerHTML from scratch」）讓每個現在與未來的插值都預設成 XSS sink。今天安全的欄位（tax_id/code/marketLabel/version）只靠隱性上游驗證、非輸出編碼，任何新增欄位自動繼承漏洞。
- **修法**：單一 `escapeHtml()` 全程路由，或改 `createElement`+`textContent`+`setAttribute`；建立「untrusted string 永不串進 innerHTML literal」慣例。

### [ ] M2. URL `custno=` 擷取不限 domain 且最高優先級 → 可偽造顯示的公司
- **面向**：interceptor-mainworld
- **位置**：`interceptor.js`:42-45/148-153/176-181，`PRIORITY.URL_PARAM=3`:59
- **問題**：`custNo` 從**任何**請求 URL 擷取（fetch/XHR，不限 104），且給最高優先級覆蓋 JSON-body(2)/HTML-scan(1)。註解明寫「不限 domain」。interceptor 在 main world，故 104 JS / 廣告 / 其他擴充只要發 `fetch('https://anything/?custno=<valid-UBN>')` 就能 pin widget 到攻擊者選的公司（鎖死後不可覆蓋）。`namesOverlap` 交叉檢查在 DOM 名為 null 的 SPA mid-render 時機窗可被繞過。
- **影響**：內容/完整性偽造（讓使用者看 B 公司時顯示 A 公司資料）。非 XSS、非竊資（main.js 用 catalog 的可信 name render）。
- **修法**：URL_PARAM 擷取加 `is104Domain` 閘；重新考慮是否該讓 raw URL param 高於 104 結構化 JSON。

### [ ] M3. catalog 快取無 schema 驗證 → cache poisoning 持續 24h 進 innerHTML
- **面向**：service-worker（初判 high，因來源是 first-party HTTPS 降 medium）
- **位置**：`service-worker.js`:21-31（`fetchCatalog`）
- **問題**：fetched JSON 原樣存 `chrome.storage.local`、原樣回給 main.js（`${catalogItem.name}`/`${catalogItem.code}` 進 innerHTML），**無欄位驗證**。後端/CDN 被攻破或 TLS MITM → 一次壞回應被快取整天、每次瀏覽重播 payload（把暫時注入變成持久 stored XSS），且清上游無法清 client 快取。
- **修法**：快取前驗證（陣列、各 item 型別：tax_id digits、code allowlist regex、name 為 string），丟棄畸形 item；並修真正 sink（escape）；schema 版本檢查。

### [ ] M4. 隱私政策宣稱「不送瀏覽行為至任何伺服器」但每次看公司頁都 fetch
- **面向**：manifest-privacy（初判 high，降 medium）
- **位置**：`PRIVACY_POLICY.md`:29/81，`service-worker.js`:33-39
- **問題**：政策中英文皆稱「不會將瀏覽行為…傳送至任何伺服器」/「does not transmit browsing behavior… to any server」，但每個匹配公司頁都 `fetch('/data/companies/{code}.json')` → bossy.eraser.tw 伺服器收到使用者 IP + 時間 + **正在查的公司**（依定義即瀏覽行為）。無 per-company 快取，故每次瀏覽都發。政策自身的 Network Requests 表又承認連往 bossy.eraser.tw — 內部自相矛盾。
- **影響**：published store 隱私政策的實質不實陳述，Chrome Web Store / Edge「準確揭露」政策下架風險。
- **修法**：改寫政策揭露 per-company 請求與伺服器可觀察到的（公司代碼、時間、IP）；移除絕對的「不送任何瀏覽行為」措辭；記載伺服器端 logging/retention。

---

## 🟡 Low（驗證後降級或未獨立驗證）

| # | 問題 | 位置 | 修法摘要 |
|---|------|------|---------|
| [ ] L1 | 橋接通道（DOM attr + CustomEvent）任何 main-world script 可寫，interceptor 無法保護自己的 egress | `interceptor.js`:62-77 | 文件化「橋接為不可信 egress、main.js 是唯一邊界」；考慮 nonce handshake（best-effort） |
| [ ] L2 | widget 連結 href 由 `catalogItem.code` 組成、未 URL-encode（屬性 breakout） | `main.js`:395 | `setAttribute` + `encodeURIComponent`；驗證 code `^[0-9A-Za-z]+$` |
| [ ] L3 | bridge tax-id 只在比對端驗證、非每個讀取點（defense-in-depth gap） | `main.js`:529/536/509 | 單一 validate 函式，每個 `data-bossy-tax-id`/event 讀取點都過 |
| [ ] L4 | `injector.js` 無 `script.onerror`/CSP 失敗處理 → 嚴格 CSP 下靜默失效無診斷 | `injector.js`:12-15 | 加 `onerror` 記一次診斷、退回 name-only 比對 |
| [ ] L5 | CLAUDE.md 仍記載已移除的 `dispatched=true` 一次性 latch（與現行 priority 覆蓋模型不符） | `extension/CLAUDE.md` | 更新文件為 priority-override 模型；重新檢視優先級安全性 |
| [ ] L6 | `scanInlineHtml` 對整份 document innerHTML regex 掃描（DOMContentLoaded） | `interceptor.js`:127-143 | 掃描 bounded 來源（特定 script/state JSON）；高優先級命中後跳過 |
| [ ] L7 | 無 fetch timeout → MV3 worker 可能 mid-request 被殺、widget 靜默失敗無重試 | `service-worker.js`:21/34 | 加 `AbortSignal.timeout(8000)`；content script 檢查 `lastError`、區分 fail vs no-data |
| [ ] L8 | `res.json()` 無 Content-Type 守衛、404/500 與「無資料」都收斂成 null | `service-worker.js`:24/38 | Content-Type 檢查 + try/catch；HTTP error 與 not-found 分流 |
| [ ] L9 | GET_COMPANY 無快取（重複瀏覽重打網路）；catalog 單一 blob 無大小上限 | `service-worker.js`:33-39/25-28 | per-code 短 TTL 快取；catalog chunk/壓縮；`storage.set` try/catch |
| [ ] L10 | `*://` 而非 `https://` → 允許明文 HTTP 104 頁面（MITM 竄改橋接資料） | `manifest.json`:13/18/27 | 三處改 `https://*.104.com.tw/*`（104 實務全 HTTPS、非破壞性） |
| [ ] L11 | content script 跑在**所有** 104 頁面含已登入帳號/履歷區，interceptor 在那裡仍 patch 全域 fetch/XHR 並掃全頁 HTML | `manifest.json`:13/18 + `interceptor.js` | 把 injector/interceptor matches 或 path 限制到 `/company/*`、`/job/*`；同步更新政策 |
| [ ] L12 | `web_accessible_resources` 把 interceptor.js 曝露給任何 104 頁面（指紋辨識） | `manifest.json`:24-29 | 可接受；如需更緊用 `use_dynamic_url:true` |
| [ ] L13 | SW `onMessage` 不驗證 sender（`_sender` 被忽略） | `service-worker.js`:41-55 | 加 `if (_sender.id !== chrome.runtime.id) return`；驗證 `code` 格式（defense-in-depth） |
| [ ] L14 | 殘留舊 build zip（0.3.2 在非標準路徑、0.3.3） | `extension/`、`extension/store/` | 刪除 stale zip，只留當前 release；確認 .gitignore 持續排除 |

---

## ✅ 被推翻的誤報（3 個，皆關於 service worker 信任）

三個 high/medium 發現都主張「SW onMessage 不驗證 sender → 任意網頁/擴充可驅動 fetch proxy / path traversal / SSRF」，**全被 MV3 訊息模型推翻**：

1. **`manifest.json` 無 `externally_connectable`** → 外部網頁與其他擴充**根本無法**傳訊到此 worker。
2. 即使有，跨擴充訊息送到 `onMessageExternal`，**永不**到此處用的 `onMessage`（本擴充無 `onMessageExternal`）。
3. 唯一能到 `onMessage` 的是本擴充自己的 content script `main.js`（isolated world），而它只送可信的 `catalogItem.code`（來自 first-party catalog，非頁面/攻擊者可控）。104 頁面 JS（main world）無法存取 content script 的 `chrome.runtime`。

→ `message.code` 未驗證 + 缺 `encodeURIComponent` 仍是 **defense-in-depth 衛生建議**（見 L13），但**非可利用的漏洞**。

---

## 待後續確認（建議下一輪）

- [ ] **104.com.tw 實際 CSP**：決定上面三個 DOM XSS 是升級為任意 JS 執行、還是僅 HTML/CSS 注入（clickjacking）。需對 104 真實回應 header 做一次聚焦檢查。
- [ ] **注入 widget 的隔離**：`manifest.json` 無 `content_security_policy` key、widget 無 Shadow DOM/iframe（直接進 `document.body`）→ 注入以 host 頁面 DOM 權限執行。建議 Shadow DOM 隔離。
- [ ] **`go.104.com.tw` 變體**：四個 script 在 go.104 也載入，`og:title` 解析路徑同樣餵 innerHTML，該變體的 XSS source 路徑需各別確認；`reviews.104` 等子網域行為未枚舉。
- [ ] **`fetchTaxIdBySlug` egress**（`main.js`:161-243）：對 104 ajax 端點主動探測（帶使用者已登入 session）、抓全頁 HTML fallback 的隱私意涵與大小/時間上限未評估。
- [ ] **發佈/更新完整性**：Web Store `update_url`、簽章；catalog/per-company JSON 無 SRI/簽章（直接餵 innerHTML sink）。

---

## 附錄：跨面向系統性根因

1. **未轉義資料進 innerHTML**（主導根因）— 三個 render 全 raw HTML template，無 escape helper。修 sink 而非逐一修 source。
2. **main↔isolated 橋接無信任邊界/驗證** — 兩條通道任何頁面 script 可偽造；唯一閘 `isValidUBN` 只證「是合法 UBN」非「對應螢幕上公司、來自本擴充」；且只在比對端驗、render 失敗路徑先用了 raw 值。
3. **把「格式正確」當「可信/正確」** — UBN checksum + URL_PARAM 最高優先級被當權威；SW 把 200 當合法 JSON（無 Content-Type/schema 檢查）。
4. **注入 UI 無隔離** — widget 直接進 `document.body`，無 Shadow DOM/iframe、manifest 無 CSP。
5. **SW 把遠端回應當可信且無上限** — 無 schema 驗證、無 timeout、無大小上限、無 `res.json()` 守衛；壞/MITM 回應汙染 24h 快取。
6. **文件/行為漂移** — CLAUDE.md 記載已移除的 `dispatched` latch，誤導威脅模型評估。
7. **host 範圍過廣且允許明文** — `*://*.104.com.tw/*` 含 HTTP、含已登入帳號/履歷頁。
