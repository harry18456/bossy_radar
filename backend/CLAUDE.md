# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Backend

FastAPI 後端服務 + Typer CLI 資料同步工具。

## 技術棧

- **框架**: FastAPI
- **ORM**: SQLModel (SQLAlchemy + Pydantic)
- **CLI**: Typer
- **套件管理**: uv
- **Python**: 3.11+

## 常用指令

### 開發伺服器

```bash
uv run fastapi dev app/main.py    # 開發模式 (自動重載, http://127.0.0.1:8000)
```

### 測試

```bash
uv run pytest                                      # 執行所有測試
uv run pytest tests/test_api_companies.py          # 執行單一檔案
uv run pytest tests/test_api_companies.py::test_get_companies  # 執行單一測試
uv run pytest --cov=app --cov-report=html          # 覆蓋率報告 (htmlcov/index.html)
```

### 代碼品質

```bash
uv run ruff check .    # Lint 檢查
uv run ruff format .   # 格式化
```

### CLI 資料同步

```bash
uv run python -m app.cli.main sync-companies --type all
uv run python -m app.cli.main sync-violations --source all
uv run python -m app.cli.main sync-env
uv run python -m app.cli.main sync-mops --start-year 113 --end-year 113
uv run python -m app.cli.main sync-company-details --retries 5 --retry-delay 5
# 注意：--retries 為負值代表「重試到上限」，但仍受 50 次絕對嘗試上限約束（不會無限重試）；
# 連續 5 次偵測到 MOPS 維護頁會觸發斷路器中止整輪同步。
uv run python -m app.cli.main export --output-dir ../frontend/public/data
uv run python -m app.cli.main sync-all    # 依序執行所有同步
```

## 架構

### 分層設計

```
路由層 (app/api/routes/)     ← 輸入解析、HTTP 回應
服務層 (app/services/)       ← 商業邏輯、爬蟲、比對
模型層 (app/models/)         ← SQLModel ORM 定義
資料層 (bossy_radar.db / archive.db)
```

### 雙資料庫策略

- **主庫 (`bossy_radar.db`)**: 只存已成功比對到上市櫃公司的資料
- **歸檔庫 (`archive.db`)**: 存放未比對的原始資料（保持主庫乾淨）

### 公司比對策略 (`app/services/company_matcher.py`)

`CompanyMatcher` 按優先順序四層比對，`ViolationService` 與 `EnvironmentalService` 共用：

1. **Tax ID 精確比對** — 最可靠
2. **公司名稱精確比對**
3. **分公司/廠區名稱前綴比對**
4. **負責人姓名比對** — 需唯一，否則跳過（避免誤判）

### 路由注意事項

`app/api/main.py` 中 `aggregation` router **必須在 `companies` router 之前**註冊，否則 `/companies/yearly-summary` 會被 `/companies/{code}/profile` 路徑捕獲而出錯。

### `yearly-summary` 查詢模式

此端點需合併多表資料（Company + Violation + EmployeeBenefit + NonManagerSalary...），採用「預載所有資料 → 記憶體組織 → Python 排序/分頁」而非複雜 SQL JOIN，並支援動態 `include` 參數減少資料傳輸。

### MOPS 年份格式

MOPS 薪資/福利資料（t100sb14, t100sb15, t100sb13, t222sb01）以**民國年（ROC year）**儲存，例如 113 = 2024。勞動違規與環境違規使用西元年。

## API 端點

| 端點 | 說明 |
|------|------|
| `GET /api/v1/companies` | 公司列表（分頁、排序、多重篩選） |
| `GET /api/v1/companies/catalog` | 精簡列表（前端搜尋建議用） |
| `GET /api/v1/companies/{code}/profile` | 公司完整資料聚合 |
| `GET /api/v1/companies/yearly-summary` | 公司年度摘要矩陣 |
| `GET /api/v1/violations` | 勞動違規列表 |
| `GET /api/v1/environmental-violations` | 環境違規列表 |
| `GET /api/v1/mops/employee-benefits` | 員工福利費用 (t100sb14) |
| `GET /api/v1/mops/non-manager-salaries` | 非主管薪資統計 (t100sb15) |
| `GET /api/v1/mops/welfare-policies` | 福利政策文字 (t100sb13) |
| `GET /api/v1/mops/salary-adjustments` | 調薪資訊 (t222sb01) |
| `GET /api/v1/leaderboards` | 綜合排行榜（Top/Bottom 十大，含產業） |
| `GET /api/v1/system/sync-status` | 資料同步狀態統計 |

## 測試架構

測試使用內存 SQLite（每個測試函數獨立），透過 FastAPI 依賴覆蓋注入測試資料庫：

- `conftest.py` 提供 `test_engine`、`test_session`、`client`、`seed_companies`（2330 台積電、2317 鴻海、6510 精測）fixtures
- 服務層與 API 層皆有測試覆蓋

## 資料來源

- **公司資料**: MOPS 開放資料 (t187ap03, CSV 格式，四種市場類型)
- **勞動違規**: 勞動部開放資料 API (8 種違規類型)
- **環境違規**: 環境部開放資料 API (EMS_P_46，需 `MOENV_API_KEY`)
- **薪資福利**: MOPS HTML 爬蟲 (t100sb14, t100sb15, t100sb13, t222sb01, t05st03)

## 開發注意事項

- **檔案儲存**: `data/` 目錄為暫時儲存，已 gitignore
- **SSG 匯出**: `export` 指令將所有資料輸出至 `frontend/public/data/` 供前端 SSG 使用
- **自動化**: Commit 前觸發 Pre-commit 檢查；Push 後觸發 GitHub CI
