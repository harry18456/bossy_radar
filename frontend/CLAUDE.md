# Frontend

Nuxt 4 前端應用，提供公司查詢、薪資比較、違規追蹤等功能。

## 技術棧

- **框架**: Nuxt 4 (Vue 3)
- **樣式**: Tailwind CSS v4
- **狀態管理**: Pinia + pinia-plugin-persistedstate
- **圖表**: vue-chartjs (Chart.js)
- **圖示**: @nuxt/icon (Lucide Icons)
- **工具**: VueUse, Zod

## 專案結構

```
frontend/
├── app/
│   ├── assets/        # CSS、圖片等靜態資源
│   ├── components/    # Vue 元件
│   │   ├── common/    # 共用元件 (Pagination, ThemeToggle)
│   │   └── company/   # 公司相關元件 (Card, Filter, Charts)
│   ├── composables/   # 邏輯複用 (useApi, useCompanyFilters)
│   ├── constants/     # 常數定義
│   ├── layouts/       # 頁面佈局 (Header, Footer)
│   ├── pages/         # 路由頁面
│   │   ├── index.vue           # 首頁
│   │   ├── companies/          # 公司列表
│   │   │   └── [id].vue        # 公司詳情
│   │   └── watchlist.vue       # 追蹤清單
│   ├── plugins/       # Nuxt 插件
│   ├── stores/        # Pinia 狀態管理
│   ├── types/         # TypeScript 型別定義
│   ├── utils/         # 工具函式 (formatCurrency, formatDate)
│   └── app.vue        # 根元件
├── public/
│   └── data/          # 靜態 JSON 資料 (SSG 模式用)
├── nuxt.config.ts     # Nuxt 設定
├── tailwind.config.ts # Tailwind 設定
└── package.json
```

## 常用指令

```bash
npm install      # 安裝依賴
npm run dev      # 開發伺服器 (http://localhost:3000)
npm run build    # 建置
npm run generate # 生成靜態網頁 (SSG)
npm run preview  # 預覽建置結果
```

## 環境變數

```properties
# .env
NUXT_PUBLIC_API_BASE=http://localhost:8000    # 後端 API URL
NUXT_PUBLIC_DATA_MODE=static                   # 資料模式 (static/api)
NUXT_PUBLIC_GA4_ID=G-XXXXXXXXXX               # Google Analytics
NUXT_PUBLIC_GOOGLE_ADSENSE_ID=ca-pub-XXXXXXXX # Google AdSense
```

## 主要功能

### 頁面

| 路由 | 說明 |
|------|------|
| `/` | 首頁 |
| `/companies` | 公司列表 (支援篩選、排序、搜尋) |
| `/companies/[id]` | 公司詳情 (薪資趨勢圖、違規紀錄) |
| `/watchlist` | 追蹤清單 (本地儲存) |

### 功能特色

- **多重篩選**: 產業別、市場別、關鍵字搜尋
- **排序**: 資本額、上市日期等
- **薪資趨勢圖**: 歷年非主管薪資 (平均數/中位數) 與 EPS
- **違規紀錄**: 勞動部裁罰紀錄
- **追蹤清單**: LocalStorage 持久化
- **深色模式**: 自動跟隨系統或手動切換
- **響應式設計**: 完整支援手機/桌機

## 部署

採用 **Static Site Generation (SSG)** 模式部署至 Vercel：

```bash
# 1. 生成靜態網頁
npm run generate

# 2. 部署到 Vercel
npx vercel deploy .output/public --prod --archive=tgz
```

## 開發注意事項

1. **資料模式**: SSG 模式下從 `public/data/` 讀取靜態 JSON，API 模式下從後端 API 取得資料
2. **狀態持久化**: 追蹤清單使用 LocalStorage，不依賴後端
3. **URL 同步**: Filter/Sort 狀態同步至 URL query string
4. **SEO**: 包含 sitemap、structured data、canonical URLs
