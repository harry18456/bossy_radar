# Bossy Radar

Bossy Radar 是一個專門用來追蹤與分析公司資料的工具，提供勞動違規、財務狀況及公司治理等資訊。本專案旨在提升資訊透明度，協助求職者做出更明智的決定。

## 功能特色

- **公司搜尋**：透過名稱或統編輕鬆搜尋公司記錄。
- **違規追蹤**：查看歷史勞動法規與環境違規紀錄。
- **財務分析**：存取財務摘要與薪資資訊（來源為公開資料）。
- **公司治理**：連結至官方利害關係人與治理資訊區。
- **薪資趨勢圖**：歷年非主管薪資（平均數/中位數）與 EPS 視覺化。
- **追蹤清單**：將感興趣的公司加入追蹤，資料持久化於瀏覽器本地。
- **響應式設計**：現代化且支援行動裝置的介面，含深色模式。

## 瀏覽器擴充套件

**[Bossy Radar - 104 公司快查](https://chromewebstore.google.com/detail/bossy-radar-104-%E5%85%AC%E5%8F%B8%E5%BF%AB%E6%9F%A5/ofkcclhbelkcnaghcdigdljkeonebigj)** — 在瀏覽 104 人力銀行時，自動顯示公司的勞動違規、環境違規與薪資資訊。

- 瀏覽 104 公司頁面或職缺頁面時，自動彈出資訊卡片
- 顯示勞動違規次數、環境違規次數、累計罰款金額
- 顯示非主管員工中位數 / 平均年薪
- 一鍵連結至 [Bossy Radar](https://www.bossy.eraser.tw/) 查看完整報告

**安裝連結：**

| 瀏覽器 | 狀態   | 連結                                                                                                                                                              |
| ------ | ------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Chrome | 已上架 | [Chrome Web Store](https://chromewebstore.google.com/detail/bossy-radar-104-%E5%85%AC%E5%8F%B8%E5%BF%AB%E6%9F%A5/ofkcclhbelkcnaghcdigdljkeonebigj)                |
| Edge   | 已上架 | [Microsoft Edge Add-ons](https://microsoftedge.microsoft.com/addons/detail/bossy-radar-104-%E5%85%AC%E5%8F%B8%E5%BF%AB%E6%9F%A5/hahgkkffopmbccnocmkhncpopnmphoik) |

詳細說明請參考 [extension/README.md](extension/README.md)。

## 技術架構 (Tech Stack)

本專案採用現代化的技術堆疊，強調效能與開發者體驗。

### 後端 (Backend)

- **框架**：[FastAPI](https://fastapi.tiangolo.com/)
- **CLI 工具**：[Typer](https://typer.tiangolo.com/)
- **ORM**：[SQLModel](https://sqlmodel.tiangolo.com/)
- **套件管理**：[uv](https://github.com/astral-sh/uv)
- **Lint / Format**：[Ruff](https://docs.astral.sh/ruff/)
- **測試**：[pytest](https://docs.pytest.org/) + [pytest-cov](https://pytest-cov.readthedocs.io/)

### 前端 (Frontend)

- **框架**：[Nuxt 4](https://nuxt.com/) (Vue.js)
- **樣式**：[Tailwind CSS v4](https://tailwindcss.com/)
- **狀態管理**：[Pinia](https://pinia.vuejs.org/)
- **圖表**：[vue-chartjs](https://vue-chartjs.org/) (Chart.js)
- **Lint**：[ESLint](https://eslint.org/) (@nuxt/eslint)

### 瀏覽器擴充套件 (Extension)

- **規格**：Chrome Extension Manifest V3
- **語言**：純 JavaScript（零建置工具，無 bundler）
- **支援**：Chrome / Edge

## 專案結構

```
bossy_radar/
├── backend/             # FastAPI 後端 + CLI 工具
│   ├── app/
│   │   ├── api/         # REST API 端點
│   │   ├── cli/         # ETL / 資料同步指令
│   │   ├── core/        # 核心設定 (config, dependencies)
│   │   ├── db/          # 資料庫連線與初始化
│   │   ├── models/      # SQLModel 資料模型
│   │   ├── schemas/     # Pydantic schemas
│   │   └── services/    # 商業邏輯層
│   └── tests/           # pytest 測試
├── frontend/            # Nuxt 4 前端
│   └── app/
│       ├── components/  # Vue 元件
│       ├── composables/ # 邏輯複用
│       ├── pages/       # 路由頁面
│       └── stores/      # Pinia 狀態管理
├── extension/           # Chrome / Edge 瀏覽器擴充套件
│   ├── background/      # Service Worker (跨域資料請求)
│   ├── content-scripts/ # 內容腳本 (104 頁面注入)
│   └── manifest.json    # Manifest V3 設定
└── .github/workflows/   # CI/CD (GitHub Actions)
```

## 快速開始 (Quick Start)

### 前置需求 (Prerequisites)

- **Python**: 3.11+
- **Node.js**: 22+
- **uv**: 一個極速的 Python 套件安裝與解析器。

### 後端設定 (Backend Setup)

1. 進入後端目錄：

   ```bash
   cd backend
   ```

2. 安裝依賴套件：

   ```bash
   uv sync
   ```

3. 設定環境變數：
   複製 `.env.template` 為 `.env` 並填入所需數值。

   ```bash
   cp .env.template .env
   ```

4. 啟動開發伺服器：

   ```bash
   uv run fastapi dev app/main.py
   ```

   API 文件：http://127.0.0.1:8000/docs

5. 執行 CLI 指令（資料同步）：

   ```bash
   # 同步公司資料
   uv run python -m app.cli.main sync-companies --type all

   # 同步勞動違規資料
   uv run python -m app.cli.main sync-violations --source all

   # 同步環境違規資料
   uv run python -m app.cli.main sync-env

   # 同步 MOPS 薪資/福利資料
   uv run python -m app.cli.main sync-mops

   # 匯出靜態 JSON (供前端 SSG)
   uv run python -m app.cli.main export --output-dir ../frontend/public/data
   ```

### 前端設定 (Frontend Setup)

1. 進入前端目錄：

   ```bash
   cd frontend
   ```

2. 安裝依賴套件：

   ```bash
   npm install
   ```

3. 設定環境變數：
   複製 `.env.example` 為 `.env` 並進行相應設定。

   ```bash
   cp .env.example .env
   ```

4. 啟動開發伺服器：

   ```bash
   npm run dev
   ```

### 瀏覽器擴充套件 (Extension)

無需建置步驟，直接以開發者模式載入：

1. 開啟 `chrome://extensions/`（或 `edge://extensions/`）
2. 開啟「開發人員模式」
3. 點選「載入未封裝項目」，選擇 `extension/` 資料夾

## 開發工具

### 測試

```bash
# 後端測試
cd backend
uv run pytest                                          # 執行所有測試
uv run pytest --cov=app --cov-report=term-missing      # 含覆蓋率報告
```

### Lint / Format

```bash
# 後端 (Ruff)
cd backend
uv run ruff check .          # 檢查代碼品質
uv run ruff format .         # 格式化代碼

# 前端 (ESLint)
cd frontend
npm run lint                 # 檢查代碼品質
npm run lint:fix             # 自動修復
```

### Pre-commit Hooks

本專案已配置 pre-commit，每次 `git commit` 會自動執行 Ruff（後端）與 ESLint（前端）檢查：

```bash
# 安裝 pre-commit hooks
uv run pre-commit install
```

### CI/CD

每次 Push 或 Pull Request 至 `main` 分支時，GitHub Actions 會自動執行：

- **後端**：Ruff lint / format 檢查 → pytest 測試
- **前端**：ESLint 檢查

設定檔：[.github/workflows/ci.yml](.github/workflows/ci.yml)

## 授權 (License)

本專案採用 [GNU Affero General Public License v3.0 (AGPL-3.0)](LICENSE) 授權。

AGPL-3.0 是一個 Copyleft 授權，要求任何修改程式碼並透過網路提供服務的人，都必須釋出其修改後的原始碼。這確保了專案能保持開放，並持續造福社群。
