## Context

後端用兩個 sqlite 引擎（`app/db/session.py`：engine→bossy_radar.db ~40MB、archive_engine→archive.db ~360MB），schema 全靠各 service 散落呼叫 `SQLModel.metadata.create_all()` 建立，無 Alembic。7 個 model（company、violation、environmentalviolation、non_manager_salary、employee_benefit、welfare_policy、salary_adjustment）零 UniqueConstraint。

自然鍵：
- MOPS 四表：(raw_company_code, year, market_type)。
- violation：(data_source, disposition_no)，但 disposition_no 可為 NULL/空字串（H5：空鍵每次重插）。
- environmentalviolation：disposition_no 可空，亦需合成鍵。

實測現況（唯讀查詢，2026-06-13）：兩 DB **零重複**（所有自然鍵）、violation **零空-disposition 列**、archive 全表 **company_code 皆 NULL**（未比對列）。因此：(a) 無資料需清除；(b) 開 foreign_keys=ON 不會擋既有 archive 列（NULL FK 合法）；(c) 加 UNIQUE 約束重建表不會因既有重複而失敗。風險集中在 migration 機制本身與正式 DB 的原地重建。

子表 company_code 皆宣告 `foreign_key="company.code"` 但 PRAGMA 未開。

## Goals / Non-Goals

**Goals:**
- 以 Alembic 版本化管理兩引擎 schema，取代 create_all。
- DB 層保證自然鍵唯一與冪等 upsert（含空 disposition_no 的確定性合成鍵）。
- 連線層強制 WAL / busy_timeout / foreign_keys。
- 既有正式 DB 原地遷移、零資料遺失。

**Non-Goals:**
- 不改比對歸屬（5b）、不換 DB 引擎、不處理 M12 run 級交易、不重爬資料、不改前端/export/API 查詢。

## Decisions

### 採用 Alembic 並以單一 migrations/ 套件驅動兩引擎

**選擇**：新增 `backend/alembic.ini` 與 `backend/migrations/`（env.py、script.py.mako、versions/）。env.py 的 `run_migrations_offline/online` 改為迴圈跑兩個 database：main（engine）與 archive（archive_engine），各自維護 `alembic_version` 表於自己的 DB。target_metadata = SQLModel.metadata（import 所有 model 後）。命令以 `-x db=main|archive` 或預設「兩者皆跑」驅動。

**理由**：兩 DB schema 相同（同一批 model），單一 migration 腳本可套用到兩邊；env.py 迴圈是 Alembic 官方多-DB 模式的精簡版。

**捨棄方案**：Alembic 內建 multidb 模板（一次產生兩套 version 目錄）對「相同 schema 兩 DB」過度複雜；改用單腳本迴圈套用。

### baseline migration 與既有 DB 的 stamp 策略

**選擇**：0001_baseline 以 `op.create_table(...)`/反映現有 SQLModel 結構描述目前 schema（與 create_all 等價）。對**既有** DB（已有表）不能重跑 create_table，故遷移流程為：既有 DB 先 `alembic stamp 0001`（標記 baseline 已套用但不執行 DDL），再 `alembic upgrade head` 只跑 0002 之後。乾淨新 DB 則 `alembic upgrade head` 從 0001 全跑。

**理由**：baseline 對既有資料是「描述現況」，stamp 避免對已存在的表重複 create。

### 0002：UNIQUE 約束 + dedup_key 欄位 + 回填，用 batch_alter_table

**選擇**：SQLite 無法 ALTER TABLE ADD CONSTRAINT，故 0002 用 Alembic `op.batch_alter_table`（copy-and-move：建新表→複製資料→換名）對每張表：(a) 新增 `dedup_key` 欄位（violation、environmentalviolation）；(b) 加對應 UniqueConstraint。回填：先以 `op.execute` 用 SQL 計算並寫入既有列的 dedup_key，再於同一 batch 加 UNIQUE（確保回填後才上唯一約束）。dedup_key 計算邏輯與 app 層 `dedup.py` 一致（見下）。

**理由**：batch_alter_table 是 SQLite 加約束的官方手段；先回填再加約束保證不違反唯一性（已驗證零重複）。

**捨棄方案**：手寫 raw SQL 重建表 — 易錯、不可逆且無 Alembic 版本追蹤。

### dedup_key 合成規則（H5）放在共用純函式

**選擇**：新增 `backend/app/services/dedup.py`，提供 `violation_dedup_key(...)` 與 `env_violation_dedup_key(...)`：當 disposition_no 非空 → `f"{data_source}|{disposition_no}"`（violation）/ disposition_no（env）；空時 → 對 (company_name, penalty_date_iso, law_article, fine_amount, data_source) 以 sha1 取 hex 前 32 字元，前綴 `syn:`。函式為純函式、可單元測試，並被 migration 回填 SQL 與 app upsert 共用（migration 以等價 SQL 表示，app 以 Python 呼叫）。

**理由**：app 與 migration 必須產生相同 key 才能保證遷移後與後續 sync 一致；純函式集中規則。

**捨棄方案**：只在 app 端算 key、migration 端複製邏輯 — 會 drift（重演 change 3 的 H8 教訓）。

### upsert 改 SQLite ON CONFLICT DO UPDATE

**選擇**：violation_service、environmental_service、mops_scraper 的 upsert 改用 `sqlalchemy.dialects.sqlite.insert(...).on_conflict_do_update(index_elements=自然鍵, set_=更新欄位)`。violation/env 的 index_elements 用 dedup_key（唯一）；MOPS 用 (raw_company_code, year, market_type)。app 端先算 dedup_key 填入 record。移除「先 SELECT 再 add」與「空鍵無條件 add」分支。

**理由**：DB 層保證冪等；單一 statement 取代 TOCTOU 的查-插。

### PRAGMA 連線事件

**選擇**：db/session.py 用 `sqlalchemy.event.listens_for(engine, "connect")` 對兩引擎註冊，連線時 `cursor.execute("PRAGMA journal_mode=WAL"); PRAGMA busy_timeout=5000; PRAGMA foreign_keys=ON`。

**理由**：每連線生效；WAL 讓讀寫並行、busy_timeout 讓寫者等待而非 SQLITE_BUSY、foreign_keys 強制既有宣告。

### 既有正式 DB 遷移流程（含備份與回滾）

**選擇**：apply 時對正式 DB 的步驟固定為：(1) 關閉所有連線；(2) 複製 bossy_radar.db→.bak、archive.db→.bak；(3) `alembic stamp 0001`（兩 DB）；(4) `alembic upgrade head`；(5) 驗證腳本比對 upgrade 前後各表列數相等、UNIQUE 約束存在、dedup_key 非空；(6) 通過才刪 .bak，否則從 .bak 還原。

**理由**：原地遷移不可逆，備份 + 列數驗證是唯一安全網（符合使用者「動 DB 前先備份」原則）。

## Implementation Contract

**行為**：
1. `cd backend && alembic upgrade head` 對乾淨 sqlite 建出含全部表與 UNIQUE 約束的 schema；對既有 DB（先 stamp 0001）只跑 0002 並原地加欄位/約束。
2. 連線後 `PRAGMA journal_mode` 回 `wal`、`PRAGMA busy_timeout` 回 `5000`、`PRAGMA foreign_keys` 回 `1`，main 與 archive 皆然。
3. 同一筆 MOPS (raw_company_code, year, market_type) 連續 upsert 兩次 → DB 一列（第二次走 ON CONFLICT 更新）。
4. 同一筆 violation（含 disposition_no 與空 disposition_no 兩種）連續 upsert 兩次 → DB 一列。
5. 既有 DB upgrade 後各表列數與 upgrade 前位元相等（零資料遺失），dedup_key 欄位全非空。
6. 服務層不再呼叫 create_all；schema 由 alembic 管理。既有 API/export/前端行為不變。

**介面 / 資料形狀**：
- `dedup.violation_dedup_key(data_source, disposition_no, company_name, penalty_date, law_article, fine_amount) -> str`
- `dedup.env_violation_dedup_key(disposition_no, company_name, penalty_date, violation_reason, fine_amount) -> str`
- migrations 目錄可被 `alembic` CLI 從 backend/ 執行；env.py 支援 `-x db=main` / `-x db=archive`，預設兩者。
- 各 model `__table_args__` 含具名 UniqueConstraint。

**失敗模式**：
- upgrade 中途失敗：Alembic 在單一 migration 內以交易執行（SQLite DDL 交易性有限，故 batch 用 copy-and-move 確保中途失敗留下原表）；正式 DB 另有 .bak 還原。
- 唯一衝突（理論上不應發生，因零重複）：upgrade 會在加 UNIQUE 時報錯並中止，留 .bak 還原；驗證腳本會擋。

**驗收**：
- `cd backend && uv run pytest` 全綠（含 test_db_pragmas、test_idempotent_upsert、test_migrations）；`uv run ruff check . && uv run ruff format --check .` 通過。
- test_migrations 在 tmp sqlite 上 `upgrade head` 後斷言各表 UNIQUE 約束存在、`downgrade` 可回到 baseline。
- 對備份後的正式 DB 跑遷移 + 驗證腳本：列數零差異、約束就位、dedup_key 非空。
- 重跑單一年度真實 MOPS sync，目標表零新增重複列。

**範圍邊界**：
- In scope：alembic 設定與 migrations、db/session.py PRAGMA、7 個 model 的約束/欄位、4 個 service 的 upsert、dedup.py、三個測試檔、pyproject 依賴、CLAUDE.md/docs。
- Out of scope：比對歸屬邏輯（5b）、前端、export 組裝、API 路由查詢、引擎更換、重爬。

## Risks / Trade-offs

- [正式 360MB archive.db 原地 batch 重建耗時/中途失敗] → 先備份兩 DB；batch copy-and-move 中途失敗留原表；驗證列數後才刪備份，否則還原。
- [app 層 dedup_key 與 migration 回填 SQL 算出不同 key] → 規則集中於 dedup.py，migration 回填以等價 SQL 並用單元測試對拍 app 函式輸出，遷移後抽樣比對。
- [開 foreign_keys=ON 後既有 dangling FK 致寫入失敗] → 已驗證 archive 全 NULL、main FK 指向實際公司；新增測試覆蓋 FK 違規被拒。
- [WAL 在某些網路檔案系統不支援] → 本地檔案系統部署，WAL 適用；journal_mode 設定失敗時 sqlite 回退不致命。
- [Alembic 雙引擎 env.py 複雜度] → 用單腳本迴圈套用兩 DB，test_migrations 對 tmp DB 驗證升降級。
