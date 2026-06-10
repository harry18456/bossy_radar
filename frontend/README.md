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
# Data mode defaults to static JSON. Use dynamic only with a runtime FastAPI.
NUXT_PUBLIC_DATA_MODE=static
# Backend API URL (FastAPI, required only for dynamic mode)
NUXT_PUBLIC_API_BASE=http://localhost:8000
```

Runtime FastAPI mode requires `NUXT_PUBLIC_DATA_MODE=dynamic`. Empty or unset `NUXT_PUBLIC_DATA_MODE` uses static JSON from `public/data`.

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

---

## 🔍 程式碼檢查 (Linting)

本專案使用 [ESLint](https://eslint.org/) + [`@nuxt/eslint`](https://eslint.nuxt.com/) 進行程式碼品質檢查，並已整合至 [pre-commit hook](https://pre-commit.com/)。

### 檢查所有檔案

```bash
npm run lint
```

### 自動修正可修的問題

```bash
npm run lint:fix
```

### Pre-commit 自動檢查

每次 `git commit` 時，pre-commit 會自動對 `frontend/` 下被修改的 `.ts`、`.vue`、`.mjs` 檔案執行 ESLint 檢查。若有 error 則 commit 會被擋下。

> **注意**：需先在根目錄安裝 pre-commit（已包含在 backend dev dependencies 中）：
>
> ```bash
> pip install pre-commit
> pre-commit install
> ```

---

## 📦 部署 (Deployment)

本專案目前採用 **Static Site Generation (SSG)** 模式部署至 Vercel。
因資料庫龐大且未上雲端，目前建議使用 **Local Build** 方式部署。

### 部署步驟 (Vercel)

1.  **確認環境變數 (.env)**
    確保本地 `.env` 包含正式環境需要的設定 (因為打包時會將變數寫入)：

    ```properties
    NUXT_PUBLIC_API_BASE=http://localhost:8000
    NUXT_PUBLIC_DATA_MODE=static
    NUXT_PUBLIC_GA4_ID=G-XXXXXXXXXX
    NUXT_PUBLIC_GOOGLE_ADSENSE_ID=ca-pub-XXXXXXXX
    ```

2.  **打包靜態網頁**
    此指令會生成 `.output/public` 資料夾，內含 HTML/JS 與 `public/data` 所有資料。

    ```bash
    npm run generate
    ```

3.  **推送到 Vercel**
    使用 Vercel CLI 將打包好的資料夾推上去 (無需在 Vercel 雲端 Build)。
    Run from the `frontend` project root so `frontend/vercel.json` applies headers and `outputDirectory=.output/public`.

    ```bash
    npx vercel deploy --prod --archive=tgz
    ```

> **注意**：每次更新資料或程式碼時，都需重複步驟 2 與 3。

> ⚠️ **部署踩雷防呆（務必遵守）**
> 1. **勿移除** `nuxt.config.ts` 的 `nitro.preset: "static"`。Vercel 雲端 build 會自動把 `nuxt generate` 切成 `vercel-static` preset（輸出到 `.vercel/output`），與 `outputDirectory: .output/public` 不一致，導致公司頁 `_nuxt` chunk 全部 404、無法 hydration（tab/圖表失效）。`preset: "static"` 強制純 SSG 輸出、壓過自動偵測。
> 2. **勿執行 `rm -rf .vercel`**。這會清掉專案連結，下次 `vercel deploy` 會誤連/誤建到別的專案（例如名為 `frontend` 的新專案），www 不會更新。若已誤連，用 `npx vercel link --yes --project bossy-radar` 修回，並確認 `.vercel/project.json` 的 `projectName` 是 `bossy-radar`。
> 3. **部署後務必確認** CLI 回傳的 Production 網址前綴是 `bossy-radar-…`（不是 `frontend-…`），並隨機開一個公司頁（如 `/companies/2330`）確認 tab 能切換、圖表會出現。
> 4. Windows 上若 `npx vercel deploy --archive=tgz` 報路徑錯誤（`~\…\D:\…` 之類），改用 **PowerShell**（`Set-Location <frontend 絕對路徑>; npx vercel deploy …`）避開 Git Bash 的路徑轉譯 bug。
