## 1. SyncReport 基礎

- [x] 1.1 依 design「SyncReport 統計結構與服務層回傳」以 RED→GREEN 小循環建立 backend/app/services/sync_report.py：先在 backend/tests/test_sync_fail_loud.py 寫 SourceResult / SyncReport 的失敗測試（has_failures 判定、render_summary() 每 source 一行、失敗 source 含 FAILED 標記與錯誤摘要、成功 source 含寫入/跳過列數——支撐 spec「Sync commands SHALL print a per-source summary」），再實作使其通過。驗證：uv run pytest tests/test_sync_fail_loud.py 綠燈。

## 2. 重試上限與斷路器（RED → GREEN）

- [x] 2.1 撰寫 backend/tests/test_bounded_retries.py 失敗測試（mock httpx 與 time.sleep）：覆蓋 spec「Retry loops SHALL have an absolute attempt ceiling」spec 例表格（retries 3→4 次、0→1 次、-1→至多 50 次）與「Consecutive maintenance pages SHALL trip a circuit breaker」（連續 5 次維護頁後不再發新請求、report 標記 circuit broken）。驗證：uv run pytest tests/test_bounded_retries.py 失敗（現行 while True 無上限）。
- [x] 2.2 依 design「重試絕對上限與維護頁斷路器」改寫 backend/app/services/company_detail_scraper.py：_fetch_with_retry 改有界迴圈（MAX_TOTAL_ATTEMPTS=50）、維護頁失敗型態可辨識、sync_all_details 連續維護頁計數達 5 即中止並回傳含 circuit_broken 的 SyncReport。驗證：uv run pytest tests/test_bounded_retries.py 全綠。
- [x] 2.3 [P] 修正 backend/CLAUDE.md 的 sync-company-details 範例改用有限 retries 並註明負值受 50 次上限約束；滿足 spec「Documentation SHALL NOT recommend unbounded retries」。驗證：內容檢視。

## 3. MOPS 批次完整性（RED → GREEN）

- [x] 3.1 擴充 backend/tests/test_mops_scraper.py 失敗測試：覆蓋 spec「A failing MOPS row SHALL NOT abort its batch」（一列壞資料、其餘照寫、skipped+1、warning 含 raw_company_code/year/market）、「A failed MOPS batch SHALL roll back both sessions」（第一個 (year,market) 失敗後第二個正常 commit、無 PendingRollbackError、失敗單位入 record）、「MOPS commits SHALL align with (year, market) boundaries」（>500 列單位一次 commit，無中途 commit）、「MOPS cache SHALL only store validated content」（維護頁不寫 cache 且記失敗、0 列 cache 作廢重抓一次、重抓仍 0 列視為合法空）。驗證：uv run pytest tests/test_mops_scraper.py 新增測試失敗（行為尚未實作）。
- [x] 3.2 依 design「MOPS (year, market) 級 commit 與例外 rollback」「MOPS per-record 防護與跳過列記錄」「MOPS cache 內容驗證與可疑快取重抓」改寫 backend/app/services/mops_scraper.py：_upsert_data per-record try/except 與 (written, skipped) 回傳、移除 500 列中途 commit、_sync_data_source 每 (year,market) 一次 commit / except 雙 session rollback / 失敗計數、可注入 session 與 archive_session、新增 _is_valid_mops_html 並接上 cache 寫入與 0 列重抓邏輯。驗證：uv run pytest tests/test_mops_scraper.py 全綠。

## 4. CLI fail-loud（RED → GREEN）

- [x] 4.1 在 backend/tests/test_sync_fail_loud.py 加入失敗測試：typer CliRunner 對 sync-violations / sync-companies / sync-mops（mock 服務回傳含失敗的 SyncReport）斷言 exit code 1 且 stdout 含失敗 source 摘要，全成功時 exit 0——覆蓋 spec「Sync commands SHALL exit non-zero when any source fails」；並對 violation_service 解析迴圈寫測試覆蓋 spec「Skipped parse rows SHALL be logged and counted」（壞列 warning 含 source、skipped 計數、其餘列照常）。驗證：uv run pytest tests/test_sync_fail_loud.py 新增測試失敗。
- [x] 4.2 依 design「SyncReport 統計結構與服務層回傳」「CLI 摘要與非零退出」改寫 backend/app/services/company_service.py、backend/app/services/violation_service.py（含 except-pass 改 warning+計數）、backend/app/services/mops_scraper.py 的 sync_* 包裝與 backend/app/cli/main.py：服務回傳 SyncReport、下載失敗記為 source 失敗、CLI 印 render_summary() 且 has_failures 時 raise typer.Exit(1)、sync-company-details 印摘要並於全數失敗或斷路時 exit 1。驗證：uv run pytest tests/test_sync_fail_loud.py 全綠。

## 5. 整體驗證與文件

- [x] 5.1 依 design「ETL fail-loud 測試組」完成全套品質關卡：cd backend && uv run pytest 全綠、uv run ruff check . 與 uv run ruff format --check . 通過。驗證：三指令 exit 0。
- [x] 5.2 真實煙霧測試：先備份 backend/bossy_radar.db 與 backend/archive.db，執行 uv run python -m app.cli.main sync-mops --start-year 114 --end-year 114 對真實 MOPS，exit 0 且 stdout 含 per-source 摘要（寫入/跳過列數）。驗證：實測紀錄與 exit code。
- [x] 5.3 [P] 同步勾選 docs/BACKEND_AUDIT.md（H3、M4、M5、M11、NF3）與 docs/REMEDIATION_PLAN.md（change 4 標記完成）。驗證：內容檢視，勾選與實際完成項一致。
