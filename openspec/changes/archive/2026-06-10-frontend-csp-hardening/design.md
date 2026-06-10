## Context

bossy_radar 前端是 Nuxt 4 SSG，部署為 Vercel 純靜態站。現有 frontend/vercel.json 已有多個 response hardening headers，但 CSP 只有 object-src 'none'; base-uri 'self'; frame-ancestors 'self'，沒有 default-src 與 script-src，script 來源不受限制。

本次開工前以目前程式碼執行 cd frontend && npm run generate 成功。產物盤點顯示首頁與 /companies/2619/ 各有 8 個 script tag：自訂 dark-mode inline script、Nuxt color-mode inline script、JSON-LD inline script、window.__NUXT__.config inline script、data-nuxt-data JSON payload、Nuxt module script、AdSense loader。GA4 script 由 frontend/app/plugins/ga4.client.ts 在 production runtime 注入。

SSG 輸出沒有 per-request nonce；window.__NUXT__.config 與 data-nuxt-data payload 會隨建置與頁面變動，JSON-LD 也會因頁面資料不同而變動。以單一 Vercel 靜態 header 實作完全 hash-only CSP 的維護成本高，且容易在資料或 Nuxt 版本變動時阻斷 production。

以臨時本機 static server 注入候選 CSP，並用 Chrome headless + CDP 載入首頁與 /companies/2619/ 後，實際 runtime 來源包含 pagead2.googlesyndication.com、www.googletagmanager.com、www.google-analytics.com、googleads.g.doubleclick.net、api.iconify.design、ep1.adtrafficquality.google、ep2.adtrafficquality.google。apply 階段再次驗證時，GA/GTM 另會以 image beacon 打到 `https://www.googletagmanager.com/a...`，因此 `img-src` 也需列入 www.googletagmanager.com。

## Goals / Non-Goals

**Goals:**

- 讓 frontend/vercel.json 的 CSP 實際限制 script-src，且不使用萬用來源。
- 保留 AdSense、GA4、Nuxt client hydration、Nuxt color mode、JSON-LD structured data 與 Nuxt Icon runtime 的 production 行為。
- 清除已知生產 console 殘留，並讓必要診斷只在 development 或 build/server-only 條件下輸出。
- 修補 footer 外連 opener 風險。
- 讓 JSON-LD 序列化主動跳脫 <，避免未來框架轉義行為改變時復活 script breakout 風險。

**Non-Goals:**

- 不處理 watchlist 41MB、分頁參數契約、a11y/error.vue、後端、extension。
- 不新增 consent banner 或變更 GA4/AdSense 產品整合策略。
- 不把 SSG 站改成 SSR，也不引入 per-request nonce infrastructure。
- 不新增 nuxt-security 依賴，除非 review 明確要求改採該方向。
- 不重構 Nuxt Icon 圖示打包；本 change 只允許已實測的 api.iconify.design runtime fetch。

## Decisions

### Use Vercel CSP allowlist with SSG-compatible inline handling

建議方案是維持 frontend/vercel.json 作為 response header 來源，將 CSP 改為下列完整字串：

```text
default-src 'self'; script-src 'self' 'unsafe-inline' https://pagead2.googlesyndication.com https://www.googletagmanager.com https://*.googlesyndication.com https://*.adtrafficquality.google; connect-src 'self' https://www.google-analytics.com https://*.google-analytics.com https://analytics.google.com https://*.analytics.google.com https://www.googletagmanager.com https://pagead2.googlesyndication.com https://*.googlesyndication.com https://googleads.g.doubleclick.net https://*.g.doubleclick.net https://api.iconify.design https://*.adtrafficquality.google; img-src 'self' data: https://*.googlesyndication.com https://*.g.doubleclick.net https://*.google-analytics.com https://www.googletagmanager.com https://www.google.com https://pagead2.googlesyndication.com https://*.adtrafficquality.google; frame-src https://googleads.g.doubleclick.net https://tpc.googlesyndication.com https://*.googlesyndication.com https://www.google.com https://*.adtrafficquality.google; style-src 'self' 'unsafe-inline'; font-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'self'; form-action 'self'
```

理由：這個 policy 將 script 來源限制在 self、AdSense、GA4/GTM、AdSense traffic-quality runtime，不允許任意第三方 script src；同時用 'unsafe-inline' 容納 Nuxt SSG 必然產生且每頁可能不同的 inline payload。這比現況有實質防護，能擋非白名單網域的外部 script 注入。

殘餘風險：'unsafe-inline' 仍允許成功注入的 inline script 執行，因此 CSP 不是完整 XSS 防線。現有前端已驗證沒有 v-html、任意 innerHTML、eval、Function、document.write 這類直接 sink；本 change 同時清 console、footer rel、JSON-LD 主動轉義，降低可利用面。

待 review 確認：是否採用此最小改動方案作為本 change 的實作方向。

### Record stricter CSP alternatives without applying them by default

方案 A：Vercel allowlist + 'unsafe-inline'。建議採用。優點是符合純靜態部署現況、已用 production-like browser 測得 AdSense/GA4 可載入、無新增依賴。缺點是 inline script 仍被允許。

方案 B：hash-only script-src。可對自訂 dark-mode inline script 與 Nuxt color-mode inline script放 hash，但 window.__NUXT__.config、data-nuxt-data payload、JSON-LD 會因頁面或建置變動而不同；若用單一靜態 header 管理所有頁面，需額外產生 per-route CSP 或移除 inline payload。此方案超出最小改動。

方案 C：引入 nuxt-security。模組可集中管理 headers，但本專案是 Vercel 純靜態輸出，仍要面對 SSG inline payload、AdSense/GA4 allowlist 與 Vercel header 契約；新增依賴會擴大測試面。除非 review 要求統一 security header 管理，否則不採用。

### Include observed runtime third-party domains

CSP 不只依 source code 字串列網域，還要納入 browser runtime 實測來源。api.iconify.design 由 Nuxt Icon 在首頁缺 lucide:moon 時 runtime fetch；ep1.adtrafficquality.google 與 ep2.adtrafficquality.google 由 AdSense runtime 載入設定、script、iframe 與 pixel；www.googletagmanager.com 同時作為 GA4 script 來源與 GTM image beacon 來源。這些來源若缺少，Chrome 會出現阻斷性 CSP violation。

替代作法是修正 Nuxt Icon 打包以完全移除 api.iconify.design runtime fetch，或禁用 AdSense traffic-quality runtime。這兩者都超出本 change 的最小修補目標。

### Clean production diagnostics without changing user-facing fallback behavior

AdSenseUnit、useStaticApi、company store 的已知 console 殘留要移除或包在 import.meta.dev。useStaticApi 的 toast 與 rethrow 行為維持不變；company store 的 loading state 與 failure swallowing 行為維持不變；AdSense 已載入或容器不可見時的 retry/fallback 行為維持不變。

替代作法是全面移除所有 console。此 change 不處理 build-time operator signals，例如 sitemap 讀取失敗時在 generate 階段輸出的警告或錯誤。

### Escape JSON-LD through a shared serializer

useStructuredData 應建立或使用單一 JSON-LD 序列化路徑，將 JSON.stringify(schema) 的結果再執行 replace(/</g, '\\u003c')，並套用到 WebSite、Organization、Company、Breadcrumb 四種 structured data 注入。

替代作法是繼續依賴 unhead v2.1.2 的 tagToString 轉義。此作法目前安全，但框架行為是隱性依賴，不適合作為長期 defense-in-depth。

## Implementation Contract

**Behavior:**

- Public route responses from Vercel SHALL include a CSP with default-src and script-src; script-src SHALL be non-empty and SHALL NOT contain * or https: as a blanket source.
- Production homepage and a generated company page SHALL hydrate under the CSP, load the Nuxt module script, load AdSense loader, inject GA4 gtag script, create AdSense iframes when ad slots enter view, and send GA4 collect requests without blocking CSP violations.
- Production browser console SHALL NOT contain diagnostics from AdSense retry/error paths, static API fetch fallback/error paths, or company catalog store failure paths.
- Footer external links that open a new tab SHALL include rel="noopener noreferrer".
- JSON-LD script contents SHALL serialize < as \u003c before passing content to useHead.

**Interface / configuration shape:**

- frontend/vercel.json keeps the existing wildcard headers rule and replaces only the Content-Security-Policy value.
- useStructuredData continues exposing injectWebSiteSchema, injectOrganizationSchema, injectCompanySchema, injectBreadcrumbSchema with the same call signatures.
- No package dependency or runtime environment variable is added.

**Failure modes:**

- If a static data fetch fails, existing toast/error propagation remains unchanged; only production console emission changes.
- If AdSense cannot fill an ad on localhost or production, the app must not crash; CSP verification only requires loader/script/frame creation and no CSP block, not a paid ad impression.
- If a new third-party runtime host appears during verification, implementation must add the narrow host to the relevant directive or document why the blocked request is acceptable before review.

**Acceptance criteria:**

- Run cd frontend && npm run generate; command exits 0 with nitro.prerender.failOnError still true.
- Inspect .output/public/index.html and .output/public/companies/2619/index.html or another generated company page; document inline script classes and external script sources.
- Serve .output/public with the proposed CSP header in production mode, load / and /companies/2619/ in Chrome, and confirm GA4 script/resource hits, AdSense script/resource hits, AdSense iframe creation, and zero CSP security log entries.
- Confirm frontend/vercel.json CSP contains default-src, script-src, connect-src, img-src, frame-src, style-src, font-src, object-src, base-uri, frame-ancestors.
- Confirm production console output no longer includes the known AdSenseUnit, useStaticApi, or company store diagnostics.
- Confirm footer target="_blank" links include rel="noopener noreferrer".
- Confirm JSON-LD output escapes < as \u003c by unit-level inspection or generated HTML inspection using a payload containing <.

**Scope boundaries:**

- In scope: frontend/vercel.json, AdSenseUnit console hygiene, useStaticApi console hygiene, company store console hygiene, AppFooter rel attributes, useStructuredData JSON-LD serialization, local production-like CSP verification.
- Out of scope: watchlist payload performance and pagination contract, a11y/error.vue, backend API/ETL/export, extension security, consent UX, dependency-level security header modules.

## Risks / Trade-offs

- [Risk] AdSense runtime domains change over time. -> Mitigation: keep allowlist narrow but verification-driven; add only observed Google ad runtime domains and require browser verification before deploy.
- [Risk] 'unsafe-inline' weakens CSP against inline script injection. -> Mitigation: record SSG constraint, keep source allowlist for external scripts, and leave hash-only or nonce-based CSP as a future architecture change.
- [Risk] api.iconify.design runtime fetch adds an external dependency. -> Mitigation: limit it to connect-src only and document that removing this host requires separate icon bundling work.
- [Risk] Localhost AdSense behavior differs from production inventory. -> Mitigation: acceptance checks script, resource, and iframe creation plus absence of CSP blocks; production preview remains required before promotion.
- [Risk] JSON-LD escaping could double-escape if implemented in more than one place. -> Mitigation: use one shared serializer path in useStructuredData and replace all direct JSON.stringify(schema) innerHTML assignments.

## Migration Plan

1. Review CSP strategy and confirm whether to apply the recommended Vercel allowlist + 'unsafe-inline' policy.
2. Update frontend/vercel.json CSP value and scoped frontend security hygiene files.
3. Run generate and inspect SSG output.
4. Run production-like browser verification with the final CSP header against homepage and one company page.
5. Deploy through the documented Vercel frontend project-root flow only after local verification passes.
6. If Vercel preview shows blocking CSP violations, roll back the CSP value to the previous minimal baseline and revise the allowlist before promotion.

## Open Questions

- 待 review 確認：本 change 是否採用建議方案 A（Vercel allowlist + 'unsafe-inline'），並將 hash-only / nonce / nuxt-security 留作後續架構性 change。
