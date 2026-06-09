## 1. 靜態模式與文件契約

- [x] [P] 1.1 實作 Frontend runtime SHALL default to static data mode 與 Use static mode as the default and require explicit dynamic mode：未設定或空白 NUXT_PUBLIC_DATA_MODE 時 useApi 選 static，只有明確 dynamic 才選 dynamic；以清空環境變數後在 frontend 執行 npm run generate，並檢查生成的 Nuxt public config 或頁尾 dataMode 顯示 static 驗證。
- [x] [P] 1.2 更新 frontend/.env.example、frontend/README.md、frontend/CLAUDE.md，讓本地開發與部署文件明確記載 static 是預設、dynamic API 必須設定 NUXT_PUBLIC_DATA_MODE=dynamic；以內容審查確認文件不再宣稱預設 dynamic，且保留 dynamic API 的明確設定方式。

## 2. SSG 失敗訊號與 CI

- [x] [P] 2.1 實作 Static generation SHALL fail loud：Nuxt prerender 遇到 configured route 失敗時 generation command 回傳非零；以檢查 frontend/nuxt.config.ts 的 nitro.prerender.failOnError=true 與執行 frontend 目錄下 npm run generate 驗證正常資料可生成。
- [x] [P] 2.2 讓 GitHub Actions frontend job 執行 static generation，滿足 Static generation SHALL fail loud 的 CI 情境；以內容審查 .github/workflows/ci.yml 確認 npm run generate 位於 npm ci 與 npx nuxt prepare 之後，且不是 continue-on-error。

## 3. 首頁排行榜 SSG

- [x] 3.1 實作 Homepage leaderboards SHALL be prerendered into HTML 與 Render homepage leaderboards server-side using the existing static API：首頁 useAsyncData 允許 prerender 讀取 leaderboards.json，五個 leaderboard 區塊不再被 ClientOnly fallback 取代；以 npm run generate 後檢查 frontend/.output/public/index.html 包含 /companies/6505 與 leaderboard 公司名稱，且排行榜區塊不是只有 animate-pulse skeleton 驗證。
- [x] 3.2 確認首頁 leaderboard 子元件仍可互動且無瀏覽器專用 API 依賴 SSR；以 rg 檢查 frontend/app/components/home 不含 window、document、localStorage、sessionStorage、navigator、onMounted，並以 npm run generate 無 hydration/prerender error 驗證。

## 4. Vercel headers 與 CSP baseline

- [x] [P] 4.1 實作 Production deployment SHALL apply response hardening headers 與 Make the Vercel project root explicit for headers：新增 frontend/vercel.json 作為 frontend project root 設定，定義 generated static output directory 與 wildcard headers rule；以 Vercel schema 內容審查確認 outputDirectory 指向 .output/public，README 部署命令從 frontend project root 執行而非直接部署 .output/public 目錄。
- [x] [P] 4.2 實作 Use an enforced minimal CSP baseline, not strict CSP：headers 包含 X-Content-Type-Options=nosniff、Referrer-Policy=strict-origin-when-cross-origin、Permissions-Policy、X-Frame-Options=SAMEORIGIN 或 CSP frame-ancestors 'self'、Content-Security-Policy object-src 'none' 與 base-uri 'self'；以 Vercel preview 或 production URL 執行 HTTP header inspection 驗證實際回應，不以檔案 grep 取代。

## 5. Production console 與 optional third-party script

- [x] [P] 5.1 實作 Production browser console SHALL not expose debug diagnostics 與 Keep diagnostics development-only：GA4 初始化、dynamic API baseURL、sitemap 載入、IndustryEps 掃描不得在 production console.log；以 rg console.log frontend/app frontend/nuxt.config.ts 檢查剩餘 log 皆被 import.meta.dev 或 build/operator 條件限制，並以 production build 手動瀏覽首頁 console 驗證無指定訊息。
- [x] [P] 5.2 實作 Optional analytics and ads configuration SHALL fail closed：空白 NUXT_PUBLIC_GOOGLE_ADSENSE_ID 不注入 adsbygoogle loader，空白 NUXT_PUBLIC_GA4_ID 不注入 Google tag script；以清空兩個 env 後執行 npm run generate，檢查 frontend/.output/public/index.html 不含 client=undefined、不含空白 client 參數、不含 googletagmanager GA4 script 驗證。

## 6. 整合驗證

- [x] 6.1 執行 frontend 整體驗證：在 frontend 目錄跑 npm run lint 與 npm run generate，確認兩者成功，並重新檢查 generated index HTML、production console 清理、AdSense 空設定輸出、Vercel preview/production headers，全部符合 frontend-static-site-delivery spec。
