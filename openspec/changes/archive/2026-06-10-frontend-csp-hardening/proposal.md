## Why

`frontend-ssg-correctness-and-headers` 已補安全標頭，但目前 Content-Security-Policy 只有 object-src、base-uri、frame-ancestors，缺 default-src 與 script-src，無法限制外部 script 來源，不能作為 stored-XSS 的最後防線。

第二輪複查同時指出生產 console、footer 外連 rel 與 JSON-LD 主動轉義仍有殘留缺口，應在重新部署前與 CSP 同批收斂，避免安全標頭完成判準再次落空。

## What Changes

- 將 frontend/vercel.json 的 Content-Security-Policy 擴充為可執行的 allowlist policy，至少包含 default-src、script-src、connect-src、img-src、frame-src、style-src、font-src，並保留 object-src 'none'、base-uri 'self'、frame-ancestors 'self'。
- 以實測盤點 Nuxt SSG 產物、GA4、AdSense、Nuxt Icon runtime 來源後決定 CSP 網域清單，確保 script-src 非空、非萬用，且 AdSense/GA4 在 production 模式仍能載入。
- 清理 AdSenseUnit、useStaticApi、company store 的殘留生產 console；保留必要診斷時必須以 import.meta.dev 或 build/server-only 條件限制。
- 為 AppFooter 的兩個 target="_blank" 外連補 rel="noopener noreferrer"。
- 將 JSON-LD 產生邏輯改為主動跳脫小於號，例如將 < 轉成 \u003c，不依賴 unhead 的隱性 script breakout 防護。

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- frontend-static-site-delivery: 強化 production CSP、console hygiene、外連 rel 與 JSON-LD structured data 輸出的安全要求。

## Impact

- Affected specs: frontend-static-site-delivery
- Affected code:
  - Modified: frontend/vercel.json
  - Modified: frontend/app/components/common/AdSenseUnit.vue
  - Modified: frontend/app/composables/useStaticApi.ts
  - Modified: frontend/app/stores/company.ts
  - Modified: frontend/app/components/common/AppFooter.vue
  - Modified: frontend/app/composables/useStructuredData.ts
- Affected dependencies: none
- Affected deployment: Vercel static frontend headers for generated SSG output
