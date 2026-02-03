# Bossy Radar

Bossy Radar 是一個台灣上市櫃公司薪資與勞動違規查詢平台，提供勞動違規、財務狀況及公司治理等資訊，協助求職者做出更明智的決定。

## 技術架構

- **後端 (Backend)**: FastAPI + SQLModel + Typer CLI
- **前端 (Frontend)**: Nuxt 4 (Vue 3) + Tailwind CSS v4 + Pinia
- **套件管理**: uv (Python) / npm (Node.js)

## 專案結構

```
bossy_radar/
├── backend/           # FastAPI 後端 + CLI 工具
│   ├── app/
│   │   ├── api/       # REST API 端點
│   │   ├── cli/       # ETL/資料同步指令
│   │   ├── models/    # SQLModel 資料模型
│   │   ├── schemas/   # Pydantic schemas
│   │   └── services/  # 商業邏輯層
│   └── scripts/       # 輔助腳本
├── frontend/          # Nuxt 4 前端
│   └── app/
│       ├── components/  # Vue 元件
│       ├── composables/ # 邏輯複用
│       ├── pages/       # 路由頁面
│       └── stores/      # Pinia 狀態管理
└── README.md
```

## 快速開始

### 後端

```bash
cd backend
uv sync                                    # 安裝依賴
cp .env.template .env                      # 設定環境變數
uv run fastapi dev app/main.py             # 啟動開發伺服器 (http://127.0.0.1:8000)
```

### 前端

```bash
cd frontend
npm install                                # 安裝依賴
cp .env.example .env                       # 設定環境變數
npm run dev                                # 啟動開發伺服器 (http://localhost:3000)
```

## 常用指令

### 後端 CLI (資料同步)

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

### 前端

```bash
npm run dev        # 開發伺服器
npm run generate   # 生成靜態網頁 (SSG)
npm run build      # 建置
```

## 開發注意事項

1. **資料流向**: CLI 負責資料擷取 (ETL)，FastAPI 負責提供 API，前端消費 API 或靜態 JSON
2. **資料庫**: 主資料庫 `bossy_radar.db`，歸檔資料庫 `archive.db` (存放未比對資料)
3. **部署模式**: 前端使用 SSG 模式，資料透過 `public/data` 靜態 JSON 提供
4. **授權**: AGPL-3.0
