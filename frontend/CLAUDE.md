# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 常用指令

```bash
npm run dev        # 開發伺服器 (http://localhost:3000)
npm run generate   # SSG 靜態生成（需先匯出靜態 JSON）
npm run build      # 建置（SSR 模式）
npm run lint       # ESLint 檢查
npm run lint:fix   # ESLint 自動修正
```

## 環境變數

```properties
NUXT_PUBLIC_DATA_MODE=static        # static | dynamic（預設 dynamic）
NUXT_PUBLIC_API_BASE=http://localhost:8000
NUXT_PUBLIC_GA4_ID=G-XXXXXXXXXX
NUXT_PUBLIC_GOOGLE_ADSENSE_ID=ca-pub-XXXXXXXX
```

## 架構核心：雙模式資料存取

`useApi` composable 根據 `NUXT_PUBLIC_DATA_MODE` 切換實作：

| 模式 | 實作 | 資料來源 |
|------|------|----------|
| `static` | `useStaticApi` | `public/data/*.json`（SSG 用） |
| `dynamic` | 直接打 FastAPI | `NUXT_PUBLIC_API_BASE` |

**SSG 生產流程**：
1. 後端 CLI 匯出靜態 JSON → `public/data/`
2. `npm run generate` 讀取 JSON 預渲染所有公司頁面

`useStaticApi` 內部根據執行環境有三種策略：
- **預渲染時** (`import.meta.prerender`)：直接用 `node:fs` 讀檔，繞過 HTTP
- **SSR 時**：用 `useRequestURL().origin` 組成絕對 URL
- **客戶端時**：相對路徑 `/data/...`

## 靜態 JSON 檔案結構

```
public/data/
├── company-catalog.json            # 所有公司清單（CompanyCatalog[]）
├── companies/
│   └── {code}.json                 # 個別公司完整資料（CompanyProfile）
├── yearly-summaries/
│   ├── index.json                  # 可用年份索引
│   └── {year}.json                 # 各年份摘要資料
├── mops/
│   ├── employee-benefits.json
│   ├── non-manager-salaries.json
│   ├── welfare-policies.json
│   └── salary-adjustments.json
├── leaderboards.json
└── system-status.json
```

`nuxt.config.ts` 在建置時讀取 `company-catalog.json` 自動產生 sitemap 和預渲染路由（`nitro.prerender.routes`）。

## 狀態管理

- **`useCompanyStore`**：快取公司 catalog（1 小時），使用 `useApi()` 取得資料
- **`useWatchlistStore`**：僅將公司代碼（`codes: string[]`）持久化至 localStorage；公司詳細資料（`_companies`）不持久化，每次頁面載入時重新 hydrate
- **`useCompanyFilters`**：雙向同步篩選條件與 URL query string（page、size、sort、name、industry、market_type）

## 關鍵慣例

- **圖示**：`@nuxt/icon`，使用 `lucide:` 和 `heroicons:` 前綴
- **深色模式**：`@nuxtjs/color-mode`，`classSuffix: ""`（即 `.dark` class），`nuxt.config.ts` 有 inline blocking script 防止 FOUC
- **Toast 通知**：`vue-sonner`，透過 `useNuxtApp().$toast` 使用
- **市場類型值**：前端用 `Listed / OTC / Emerging / Public`，靜態 API 內部有 mapping 轉換至後端值（`sii / otc / rotc / pub`）
- **排序參數**：前綴 `-` 代表降序，例如 `-capital`
