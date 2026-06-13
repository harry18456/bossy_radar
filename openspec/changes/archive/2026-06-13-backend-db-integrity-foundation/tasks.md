## 1. 連線層 PRAGMA（M6/M7，RED → GREEN）

- [x] 1.1 撰寫 backend/tests/test_db_pragmas.py 失敗測試，覆蓋 spec「SQLite connections SHALL enforce runtime PRAGMAs」：對 main 與 archive 兩引擎開連線後斷言 PRAGMA journal_mode=wal、busy_timeout=5000、foreign_keys=1；並覆蓋「Foreign keys are enforced」（插入不存在 company_code 被拒）與「Null foreign keys remain allowed」。驗證：cd backend && uv run pytest tests/test_db_pragmas.py 失敗（PRAGMA 尚未設定）。
- [x] 1.2 依 design「PRAGMA 連線事件」在 backend/app/db/session.py 用 sqlalchemy.event.listens_for(..., "connect") 對兩引擎每連線執行 PRAGMA journal_mode=WAL、busy_timeout=5000、foreign_keys=ON。驗證：uv run pytest tests/test_db_pragmas.py 全綠。

## 2. dedup 合成鍵純函式（H5，RED → GREEN）

- [x] 2.1 撰寫 backend/tests/test_idempotent_upsert.py 的 dedup 部分失敗測試，覆蓋 spec「Empty disposition numbers SHALL use a deterministic dedup key」spec 例：非空 disposition_no → key 為 data_source|disposition_no（violation）/ disposition_no（env）；空 disposition_no → 同識別欄位產生相同 syn: 前綴 hash、不同欄位產生不同 key。驗證：uv run pytest 此檔的 dedup 測試失敗（dedup.py 未實作）。
- [x] 2.2 依 design「dedup_key 合成規則（H5）放在共用純函式」實作 backend/app/services/dedup.py 的 violation_dedup_key 與 env_violation_dedup_key（非空走自然鍵、空走 sha1 前 32 字元 + syn: 前綴）。驗證：uv run pytest tests/test_idempotent_upsert.py 的 dedup 測試全綠。

## 3. Model 約束與 dedup_key 欄位

- [x] 3.1 依 design「0002：UNIQUE 約束」在 backend/app/models 的 violation.py、environmental_violation.py 新增 dedup_key 欄位（str、index），並對 violation/environmentalviolation/non_manager_salary/employee_benefit/welfare_policy/salary_adjustment 六個 model 以 __table_args__ 加具名 UniqueConstraint（MOPS 四表 raw_company_code+year+market_type；violation/env dedup_key）。驗證：uv run python -c "import app.models" 無誤、ruff check 通過（此 task 只改 model 宣告，DB 套用在 migration task）。

## 4. Alembic 導入與 migrations（測 tmp DB）

- [x] 4.1 撰寫 backend/tests/test_migrations.py 失敗測試，覆蓋 spec「Schema SHALL be managed by versioned migrations」與「Existing databases SHALL migrate in place without data loss」：在 tmp sqlite 對 alembic upgrade head 後斷言各表存在預期 UNIQUE 約束、downgrade 回 baseline 無誤；對預先 seed 的 tmp DB 先 stamp baseline 再 upgrade head 後列數不變。驗證：uv run pytest tests/test_migrations.py 失敗（alembic 未設定）。
- [x] 4.2 依 design「採用 Alembic 並以單一 migrations/ 套件驅動兩引擎」新增 backend/pyproject.toml 的 alembic 依賴、backend/alembic.ini、backend/migrations/env.py（迴圈套用 main+archive、target_metadata=SQLModel.metadata、支援 -x db=main|archive）、backend/migrations/script.py.mako。驗證：cd backend && uv run alembic history 可執行、env.py import 無誤。
- [x] 4.3 依 design「baseline migration 與既有 DB 的 stamp 策略」新增 backend/migrations/versions/0001_baseline.py 捕捉現有 schema（與 create_all 等價，含所有表與既有 index）。驗證：tmp 空 DB 對 alembic upgrade 0001 建出全部表。
- [x] 4.4 依 design「0002：UNIQUE 約束 + dedup_key 欄位 + 回填，用 batch_alter_table」與「dedup_key 合成規則」新增 backend/migrations/versions/0002_unique_constraints_and_dedup_keys.py：batch_alter_table 對各表加 dedup_key 欄位（violation/env）、以等價 SQL 回填既有列 dedup_key（與 dedup.py 對拍）、加 UniqueConstraint；提供 downgrade。驗證：uv run pytest tests/test_migrations.py 全綠（含 upgrade head 後約束存在、stamp+upgrade 列數不變、downgrade 可回滾）。

## 5. 冪等 upsert（H5/H6，RED → GREEN）

- [x] 5.1 擴充 backend/tests/test_idempotent_upsert.py：覆蓋 spec「Natural keys SHALL be unique at the database layer」（同 MOPS (raw_company_code,year,market_type) upsert 兩次只剩一列且第二次更新）與「Empty disposition numbers...dedupe」（同識別欄位空 disposition 違規 upsert 兩次只剩一列）；以 alembic upgrade 後的 tmp DB 驅動。驗證：uv run pytest tests/test_idempotent_upsert.py 失敗（upsert 仍走 SELECT-then-INSERT、無 dedup_key 填值）。
- [x] 5.2 依 design「upsert 改 SQLite ON CONFLICT DO UPDATE」改寫 backend/app/services/mops_scraper.py、violation_service.py、environmental_service.py 的 upsert 為 sqlite insert().on_conflict_do_update(index_elements=自然鍵)，並於 app 端用 dedup.py 算 dedup_key 填入 violation/env record；移除空鍵無條件 add 分支。驗證：uv run pytest tests/test_idempotent_upsert.py 全綠。

## 6. 移除 create_all 並改走 migration

- [x] 6.1 依 design「採用 Alembic...取代 create_all」移除 backend/app/services 的 company_service.py、violation_service.py、mops_scraper.py、environmental_service.py 內的 SQLModel.metadata.create_all 呼叫；測試 fixture（conftest）保留以 create_all 建 in-memory schema（測試不跑 alembic）。驗證：grep 確認 app/services 無 create_all、uv run pytest 全綠（既有測試不回歸）。

## 7. 正式 DB 遷移與整體驗證

- [x] 7.1 依 design「既有正式 DB 遷移流程（含備份與回滾）」執行：備份 backend/bossy_radar.db 與 archive.db；對兩 DB alembic stamp 0001 後 upgrade head；以驗證腳本斷言各表 upgrade 前後列數相等、UNIQUE 約束存在、dedup_key 非空；通過才保留遷移結果（保留備份至本 change 完成）。驗證：遷移前後列數零差異實測紀錄 + 約束/欄位檢查輸出。
- [x] 7.2 全套品質關卡：cd backend && uv run pytest 全綠、uv run ruff check . 與 uv run ruff format --check . 通過。驗證：三指令 exit 0。
- [x] 7.3 真實冪等驗證：對已遷移的正式 DB 重跑一次單一年度真實 MOPS sync（sync-mops --start-year 113 --end-year 113 --data-type non_manager_salary），斷言目標表零新增重複列（遷移後與重跑後 (raw_company_code,year,market_type) 重複數皆 0）。驗證：重跑前後重複數實測紀錄。
- [x] 7.4 [P] 同步勾選 docs/BACKEND_AUDIT.md（H5、H6、M6、M7、M8）與 docs/REMEDIATION_PLAN.md（change 5 標記完成），並更新 backend/CLAUDE.md 記錄 Alembic 遷移指令與 PRAGMA。驗證：內容檢視，勾選與實際完成項一致。
