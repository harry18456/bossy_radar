# Bossy Radar (Frontend)

**Bossy Radar** 是一個台灣上市櫃公司薪資與勞動違規查詢平台。透過透明化的資訊，幫助求職者避開慣老闆，找到待遇更好的工作。

## 🚀 目前進度 (Current Status)

專案正處於 **Alpha 開發階段**，核心功能已完成：

### ✅ 已完成功能

1.  **公司列表與搜尋 (`/companies`)**
    - 支援 **多重篩選** (產業別、市場別)。
    - 關鍵字搜尋 (公司名稱/代號)。
    - 依資本額、上市日期排序。
    - 響應式 Filter Sidebar (手機版可收合)。
2.  **公司詳情頁 (`/companies/[id]`)**
    - **薪資趨勢圖**：整合 Chart.js 顯示歷年非主管薪資 (平均數/中位數) 與 EPS。
    - **違規紀錄**：列出勞動部裁罰紀錄 (法條、金額、日期)。
    - [x] **OG Image 生成**：已自動生成並部署至 `public/og-image.png`。
3.  **追蹤清單 (`/watchlist`)**
    - **Local Persistence**：使用 Pinia + LocalStorage 儲存關注公司。
    - **薪資比較表**：一鍵比較追蹤公司的薪資水準與違規次數。
4.  **UI/UX 體驗**
    - **Dark Mode**：完整支援深色模式 (自動跟隨系統或手動切換)。
    - **Responsive**：完全支援手機/桌機版面。
    - **Loading State**：使用 Skeleton Screen 優化載入體驗。

---

## 🛠️ 技術疊代 (Tech Stack)

本專案採用最新的前端技術構建：

- **Framework**: [Nuxt 4](https://nuxt.com/) (Vue 3)
- **Styling**: [Tailwind CSS v4](https://tailwindcss.com/)
- **State Management**: [Pinia](https://pinia.vuejs.org/) + `pinia-plugin-persistedstate`
- **Data Fetching**: Filter/Sort URL Synchronization Strategy
- **Charts**: `vue-chartjs` (Chart.js)
- **Icons**: `@nuxt/icon` (Lucide Icons)
- **UI Components**: Custom components with "ui-ux-pro-max" design principles.

---

## ⚙️ 安裝與執行 (Setup)

### 1. 安裝套件

```bash
npm install
```

### 2. 環境變數設定

請在專案根目錄建立 `.env` 檔案：

```properties
# Backend API URL (FastAPI)
NUXT_PUBLIC_API_BASE=http://localhost:8000
```

### 3. 啟動開發伺服器

```bash
npm run dev
```

瀏覽器打開 `http://localhost:3000` 即可看到畫面。

---

## 📂 專案結構

```
frontend/
├── components/          # Vue 元件
│   ├── common/          # 共用元件 (Pagination, ThemeToggle)
│   └── company/         # 公司相關元件 (Card, Filter, Charts)
├── composables/         # 邏輯複用 (useApi, useCompanyFilters)
├── layouts/             # 頁面佈局 (Header, Footer)
├── pages/               # 路由頁面
│   ├── index.vue        # 公司列表
│   ├── watchlist.vue    # 追蹤清單
│   └── companies/[id].vue # 公司詳情
├── stores/              # Pinia 狀態管理
├── utils/               # 工具函式 (formatCurrency, formatDate)
└── nuxt.config.ts       # Nuxt 設定
```
