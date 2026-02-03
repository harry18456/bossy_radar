# Backend

FastAPI 後端服務 + Typer CLI 資料同步工具。

## 技術棧

- **框架**: FastAPI
- **ORM**: SQLModel (SQLAlchemy + Pydantic)
- **CLI**: Typer
- **套件管理**: uv
- **Python**: 3.11+

## 專案結構

```
backend/
├── app/
│   ├── api/           # REST API 端點
│   │   └── v1/        # API v1 路由
│   ├── cli/           # CLI 指令 (ETL/資料同步)
│   ├── core/          # 核心設定 (config, dependencies)
│   ├── db/            # 資料庫連線與初始化
│   ├── models/        # SQLModel 資料模型
│   ├── schemas/       # Pydantic request/response schemas
│   ├── services/      # 商業邏輯層
│   └── main.py        # FastAPI app 進入點
├── scripts/           # 輔助腳本
├── cli.py             # CLI 進入點
├── main.py            # 開發用進入點
└── pyproject.toml     # 專案設定
```

## 常用指令

### 啟動開發伺服器

```bash
uv run fastapi dev app/main.py    # 開發模式 (自動重載)
# API 文件: http://127.0.0.1:8000/docs
```

### CLI 資料同步

```bash
# 同步公司資料 (上市/上櫃/興櫃/公開發行)
uv run python -m app.cli.main sync-companies --type all

# 同步勞動違規資料 (勞基法、性平法、職安法等 8 種)
uv run python -m app.cli.main sync-violations --source all

# 同步環境違規資料
uv run python -m app.cli.main sync-env

# 同步 MOPS 員工薪資/福利資料
uv run python -m app.cli.main sync-mops
uv run python -m app.cli.main sync-mops --start-year 113 --end-year 113

# 同步公司詳細連結 (t05st03)
uv run python -m app.cli.main sync-company-details --retries -1 --retry-delay 5

# 匯出靜態 JSON (供前端 SSG)
uv run python -m app.cli.main export --output-dir ../frontend/public/data
```

## 架構原則

### 分層設計

1. **進入點 (CLI/API)**: 僅處理輸入解析並觸發服務
2. **服務層 (services/)**: 包含商業邏輯
3. **資料層 (models/)**: 處理資料庫互動

### 資料來源

- **公司資料**: [MOPS 開放資料](https://mopsfin.twse.com.tw/opendata/t187ap03_L.csv)
- **勞動違規**: [勞動部開放資料](https://apiservice.mol.gov.tw/OdService/download/A17000000J-030225-QDf)
- **環境違規**: [環境部開放資料](https://data.moenv.gov.tw/api/v2/EMS_P_46)
- **薪資福利**: MOPS t100sb14, t100sb15, t100sb13, t222sb01, t05st03

### 資料庫

- **主資料庫 (`bossy_radar.db`)**: 儲存與上市櫃公司連結的資料
- **歸檔資料庫 (`archive.db`)**: 儲存未比對的資料 (保持主資料庫乾淨)

## API 端點

| 端點 | 說明 |
|------|------|
| `GET /api/v1/companies` | 公司列表 |
| `GET /api/v1/companies/{code}/profile` | 公司詳細資料 |
| `GET /api/v1/companies/yearly-summary` | 公司年度摘要 |
| `GET /api/v1/violations` | 勞動違規列表 |
| `GET /api/v1/environmental-violations` | 環境違規列表 |
| `GET /api/v1/mops/employee-benefits` | 員工福利資訊 |
| `GET /api/v1/mops/non-manager-salaries` | 非主管薪資資訊 |
| `GET /api/v1/system/sync-status` | 系統同步狀態 |

## 開發注意事項

1. **長時間任務**: CLI 負責資料擷取，不應阻塞 HTTP 請求
2. **檔案儲存**: `data/` 目錄為暫時儲存，必須被 gitignore
3. **比對策略**: 違規資料透過公司名稱、簡稱、分公司名、負責人等多重比對
