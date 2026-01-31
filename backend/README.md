# Backend 架構說明

## 架構原則

### 1. 資料擷取 / ETL (CLI)

- **角色**: 負責「準備資料」
- **資料來源 (Source URLs)**:
  - [公開資訊觀測站開放資料 (MOPS Open Data)](https://mopsfin.twse.com.tw/opendata/t187ap03_L.csv) - 公司基本資料
  - [MOL 勞動部開放資料](https://apiservice.mol.gov.tw/OdService/download/A17000000J-030225-QDf) - 勞動違規資料
- **位置**: `app/cli`
- **職責**:
  - 擷取外部資料（網頁爬蟲、API 呼叫）
  - 資料解析與清理
  - 儲存/更新資料庫
- **特性**:
  - **長時間執行**: 不應阻塞 HTTP 請求
  - **主動/排程**: 由管理員指令或 cron job 觸發
  - **寫入密集**: 專注於資料持久化

### 2. 資料服務 (FastAPI)

- **角色**: 負責「提供/消費資料」
- **位置**: `app/api`
- **職責**:
  - 提供前端/客戶端 API 端點
  - 處理請求/回應週期
  - 查詢參數驗證（過濾、排序）
- **特性**:
  - **即時**: 必須快速回應避免超時
  - **被動**: 由使用者操作觸發
  - **讀取密集**: 專注於高效查詢

### 3. 分層設計 (Services)

- **角色**: 共用商業邏輯
- **位置**: `app/services`
- **原則**: 不要將核心邏輯鎖在 CLI 字串或 API 路由中
- **結構**:
  - **進入點 (CLI/API)**: 僅處理輸入解析並觸發服務
  - **服務層**: 包含實際邏輯（如 `crawler_service.py`、`company_service.py`）
  - **資料層 (DB/Models)**: 處理直接的資料庫互動

### 4. 檔案儲存 / 產出物

- **角色**: CLI 操作的暫時或持久檔案儲存
- **位置**: `backend/data`
- **結構**:
  - `data/raw`: 爬蟲的原始 HTML/JSON 回應（如 MOPS 快取）
- **政策**:
  - **Gitignore**: **必須**被 git 忽略
  - **保留期**: 視為暫時性。資料庫為資料來源的唯一真相

## 功能與模組

### 1. 公司資料（上市櫃資訊）

從證交所同步公司基本資料（上市/上櫃/興櫃/公開發行）。

- **CLI 指令**:
  ```bash
  # 同步所有市場類型
  uv run python -m app.cli.main sync-companies --type all
  ```
- **API**: `GET /api/v1/companies`
  - 支援過濾：`market_type` (Listed, OTC, Emerging, Public)、`industry`、`code`、`name`
  - 支援多欄位排序（如 `sort=-capital`）

### 2. 勞動違規資料

從勞動部開放資料同步 8 種勞動違規記錄（勞基法、性平法、職安法等）。

- **架構**:
  - **主資料庫 (`bossy_radar.db`)**: 儲存與**上市櫃、公開發行公司**連結的違規
  - **歸檔資料庫 (`archive.db`)**: 儲存未比對的違規（中小企業、個人），保持主資料庫乾淨
- **比對策略**:
  1. **精確比對**: 直接比對公司名稱或簡稱
  2. **分公司比對**: 違規名稱以公司名稱開頭（如「台積電高雄分公司」）
  3. **負責人比對**: 負責人為唯一對應到某上市公司
- **CLI 指令**:
  ```bash
  # 同步所有違規來源
  uv run python -m app.cli.main sync-violations --source all
  ```
- **API**: `GET /api/v1/violations`
  - **主要過濾器**:
    - `data_source`: 依法規類型過濾（如 `LaborStandards`）
    - `min_fine` / `max_fine`: 依罰款金額過濾
    - `start_date` / `end_date`: 依處分日期過濾

### 3. 環境違規資料

從環境部開放資料同步違反環保法規記錄。

- **資料來源**: [EMS_P_46 環境部開放資料](https://data.moenv.gov.tw/api/v2/EMS_P_46)
- **架構**:
  - **主資料庫 (`bossy_radar.db`)**: 儲存與上市櫃公司成功比對的違規資料
  - **歸檔資料庫 (`archive.db`)**: 儲存無法比對的資料
- **CLI 指令**:
  ```bash
  # 同步環境違規資料
  uv run python -m app.cli.main sync-env
  ```
- **API**: `GET /api/v1/environmental-violations`
  - 支援過濾：`min_fine`, `max_fine`, `start_date`, `end_date`, `violation_type`, `authority`

### 4. MOPS 員工薪資/福利資料

從公開資訊觀測站同步上市櫃公司員工薪資與福利資料。

- **資料來源**:
  | 來源代號 | 說明 |
  |----------|------|
  | t100sb14 | 財務報告附註揭露之員工福利(薪資)資訊 |
  | t100sb15 | 非擔任主管職務之全時員工薪資資訊 |
  | t100sb13 | 員工福利政策及權益維護措施揭露 |
  | t222sb01 | 基層員工調整薪資或分派酬勞 |

- **架構**:
  - **主資料庫 (`bossy_radar.db`)**: 儲存與上市櫃、公開發行公司成功比對的薪資/福利資料
  - **歸檔資料庫 (`archive.db`)**: 儲存無法比對的資料（如公司代號不在 Company 表中）
- **比對策略**:
  1. **公司代號比對**: 直接比對 MOPS 資料的公司代號
  2. **分公司比對**: 若公司代號帶有分公司後綴，比對母公司代號

- **CLI 指令**:

  ```bash
  # 同步所有資料類型（預設：近 5 年）
  uv run python -m app.cli.main sync-mops

  # 同步指定年份範圍
  uv run python -m app.cli.main sync-mops --start-year 113 --end-year 113

  # 同步指定資料類型
  uv run python -m app.cli.main sync-mops --data-type employee_benefit
  ```

- **API 端點**:
  | 端點 | 說明 |
  |------|------|
  | `GET /api/v1/mops/employee-benefits` | 員工福利(薪資)資訊 |
  | `GET /api/v1/mops/non-manager-salaries` | 非主管全時員工薪資 |
  | `GET /api/v1/mops/welfare-policies` | 福利政策揭露 |
  | `GET /api/v1/mops/salary-adjustments` | 基層員工調薪/分派酬勞 |
  | `GET /api/v1/system/sync-status` | 系統同步狀態 |

- **共用查詢參數(MOPS)**:
  - `page`、`size`: 分頁（每頁最多 100 筆）
  - `sort`: 多欄位排序（如 `-year`、`company_code`）
  - `company_code`、`year`、`market_type`: 多值過濾

### 5. 公司聚合 API

提供公司綜合資料查詢，整合違規、薪資、福利等關聯資料。

- **API 端點**:
  | 端點 | 說明 |
  |------|------|
  | `GET /api/v1/companies/{code}/profile` | 單一公司完整資料（含歷年違規/薪資/福利） |
  | `GET /api/v1/companies/yearly-summary` | 公司年度摘要列表（公司×年份矩陣） |

- **Yearly Summary 回傳資料選擇**（`include` 參數）:
  | 值 | 回傳內容 |
  |----|----------|
  | 不設定 | 只有公司基本資料 + year |
  | `violations` | + 違規統計（當年度/歷年累計） |
  | `employee_benefit` | + 員工福利完整資料 (t100sb14) |
  | `non_manager_salary` | + 非主管全時員工薪資完整資料 (t100sb15) |
  | `welfare_policy` | + 福利政策完整資料 (t100sb13) |
  | `salary_adjustment` | + 調薪完整資料 (t222sb01) |
  | `all` | 包含所有資料 |

- **查詢參數**:
  - `page`: 頁碼（從 1 開始）
  - `size`: 每頁筆數（最多 100 筆）
  - `sort`: 支援所有數值欄位排序（如 `-violations_total_count`）
  - `year`、`company_code`、`market_type`、`industry`: 多值過濾
  - `include`: 選擇要回傳的資料（可多選）

### 6. 資料匯出服務 (SSG)

將資料庫內容匯出為靜態 JSON 檔案供前端 SSG (Static Site Generation) 使用。

- **CLI 指令**:
  ```bash
  # 匯出所有資料至指定目錄 (預設: frontend/public/data)
  uv run python -m app.cli.main export --output-dir frontend/public/data
  ```
- **產出檔案**:
  - `company-catalog.json`: 公司目錄
  - `yearly-summaries.json`: 年度摘要總表
  - `system-status.json`: 系統更新狀態
  - `companies/{code}.json`: 各公司詳細資料

## 本地開發

### 前置需求

- Python 3.10+
- [uv](https://github.com/astral-sh/uv)（套件管理器）

### 安裝

```bash
# 安裝依賴
uv sync
```

### 啟動伺服器

```bash
# 啟動開發伺服器（自動重載）
uv run fastapi dev app/main.py
```

- **API 文件**: `http://127.0.0.1:8000/docs`
- **API 根路徑**: `http://127.0.0.1:8000/api/v1`
