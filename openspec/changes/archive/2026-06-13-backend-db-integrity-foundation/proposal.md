## Problem

資料完整性沒有任何 DB 層後盾（BACKEND_AUDIT H5、H6、M6、M7、M8）：

1. **H6 全表零 UniqueConstraint**：7 個 model 都只有非唯一 index。所有 upsert 是 app 層 SELECT-then-INSERT，dedup bug、重試 sync、部分 commit 都能產生重複列，DB 一律接受，污染下游所有 aggregation（leaderboard、yearly-summary）。
2. **H5 空處分字號違規每次重插**：violation 去重鍵 (data_source, disposition_no)，但 disposition_no 為空字串/NULL 時無條件 add，無 unique 後盾 → 每次同步重插。environmentalviolation 的 disposition_no 同樣可空。
3. **M8 僅 create_all()、無 migration**：任何 model schema 變更（新 unique/index/欄位）對既有 bossy_radar.db(~40MB)/archive.db(~360MB) 永不生效，會出現 no such column 或需手動清庫。沒有 Alembic。
4. **M6 無 WAL / busy_timeout**：兩引擎只設 check_same_thread=False，預設 rollback-journal + busy_timeout=0。CLI sync 寫鎖期間任何 API 讀立即 SQLITE_BUSY → 未處理 500。
5. **M7 FK 宣告但未強制**：6 個子 model 宣告 foreign_key="company.code"，但從未 PRAGMA foreign_keys=ON，約束純裝飾。

## Root Cause

冪等性與參照完整性全靠脆弱的 Python（SELECT-then-INSERT、無 constraint），DB 從不否決壞資料；且沒有版本化 migration 機制，導致「想加的約束無法套用到既有庫」。

## Proposed Solution

採用 Alembic 作為 migration baseline（使用者定案），分階段建立 DB 層完整性：

1. **Alembic 導入**：新增 alembic 依賴與設定，env.py 同時驅動 main 與 archive 兩個 sqlite 引擎；建 baseline migration 捕捉現有 schema（與目前 create_all 等價）；服務層移除散落的 SQLModel.metadata.create_all() 改由 migration 管理 schema。
2. **PRAGMA（M6/M7）**：在 db/session.py 為兩引擎註冊 connect event，每連線執行 PRAGMA journal_mode=WAL、busy_timeout=5000、foreign_keys=ON。已驗證 archive 全表 company_code 皆 NULL，開 FK 不會擋既有資料。
3. **自然鍵 UniqueConstraint（H6）**：各 model 以 __table_args__ 宣告 UniqueConstraint — MOPS 四表 (raw_company_code, year, market_type)、violation (data_source, dedup_key)、environmentalviolation dedup_key；以 batch_alter_table migration 重建既有表套用約束（已驗證零重複，重建不會因約束失敗）。
4. **H5 確定性合成鍵**：violation 與 environmentalviolation 新增 dedup_key 欄位，值為自然識別欄位的確定性 hash（violation：data_source+disposition_no 或 disposition_no 空時用 company_name+penalty_date+law_article+fine_amount+data_source）；migration 回填既有列；upsert 一律以 dedup_key 去重，永不無條件 add。
5. **冪等 upsert（H5/H6）**：violation/env/MOPS 的 upsert 改用 SQLite INSERT ... ON CONFLICT(自然鍵) DO UPDATE，冪等性由 DB 保證而非 app 層先查後插。

## Non-Goals

- 不改違規歸屬比對邏輯（change 5b 範圍）；本 change 只保證「同一筆不重複插入」，不修「不掛錯公司」。
- 不導入 Postgres 或改 DB 引擎；維持雙 sqlite。
- 不處理 run 級交易/checkpoint-resume（M12）。
- 不改前端、export、API 路由的查詢邏輯（約束與 PRAGMA 對它們透明）。
- 不重爬資料；既有資料原地 migrate（已驗證零重複、零 dangling FK，故為低風險原地遷移）。

## Success Criteria

- alembic upgrade head 能在乾淨 sqlite 與既有 DB 上成功執行；alembic downgrade 能回滾 baseline 之後的 migration。
- 對既有 bossy_radar.db 與 archive.db（已備份）執行 upgrade 後：各表列數與 upgrade 前完全相同（零資料遺失）、每張表存在預期的 UNIQUE 約束、dedup_key 欄位已回填且非空。
- 重複插入同一筆 violation/MOPS 列兩次，DB 只保留一列（ON CONFLICT 生效，單元測試覆蓋）。
- 空 disposition_no 的兩筆相同違規（同公司+日期+法條+罰鍰+來源）只保留一列（H5，單元測試覆蓋）。
- 連線後 PRAGMA 查詢回報 journal_mode=wal、busy_timeout=5000、foreign_keys=1（兩引擎，單元測試覆蓋）。
- 既有 backend pytest 全綠、ruff check/format 通過。
- 重跑一次真實 sync（單一年度 MOPS）後，目標表零新增重複列（冪等，實測）。

## Capabilities

### New Capabilities

- `backend-schema-migrations`: 版本化 schema 管理 — Alembic 雙引擎 baseline 與升降級，取代 create_all。
- `backend-db-uniqueness`: 自然鍵唯一性與冪等 upsert — UNIQUE 約束 + ON CONFLICT + 空鍵確定性合成鍵。
- `backend-sqlite-runtime-pragmas`: 連線層 PRAGMA — WAL、busy_timeout、foreign_keys 強制。

### Modified Capabilities

(none)

## Impact

- Affected specs: backend-schema-migrations（新增）、backend-db-uniqueness（新增）、backend-sqlite-runtime-pragmas（新增）
- Affected code:
  - New:
    - backend/alembic.ini
    - backend/migrations/env.py
    - backend/migrations/script.py.mako
    - backend/migrations/versions/0001_baseline.py
    - backend/migrations/versions/0002_unique_constraints_and_dedup_keys.py
    - backend/app/services/dedup.py
    - backend/tests/test_db_pragmas.py
    - backend/tests/test_idempotent_upsert.py
    - backend/tests/test_migrations.py
  - Modified:
    - backend/app/db/session.py
    - backend/app/models/violation.py
    - backend/app/models/environmental_violation.py
    - backend/app/models/non_manager_salary.py
    - backend/app/models/employee_benefit.py
    - backend/app/models/welfare_policy.py
    - backend/app/models/salary_adjustment.py
    - backend/app/services/violation_service.py
    - backend/app/services/environmental_service.py
    - backend/app/services/mops_scraper.py
    - backend/app/services/company_service.py
    - backend/pyproject.toml
    - backend/CLAUDE.md
    - docs/BACKEND_AUDIT.md
    - docs/REMEDIATION_PLAN.md
  - Removed: (none)
