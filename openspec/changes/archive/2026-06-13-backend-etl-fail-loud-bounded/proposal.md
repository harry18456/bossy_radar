## Problem

ETL/CLI 層的失敗是靜默的，且重試無上限（BACKEND_AUDIT M11、H3、M4、M5、NF3）：

1. **M11 假性成功**：sync-companies / sync-violations / sync-mops 的下載或解析失敗只寫 log，CLI 仍無條件印 completed 並 exit 0；只有 sync-env 會非零退出。排程器與 CI 把部分失敗或空 sync 當成健康。
2. **H3 無限重試**：company_detail_scraper 的 _fetch_with_retry 在 retries 為負時 while True 永不終止；MOPS 維護頁字串被當成可重試錯誤，等於對限流中的政府站永久自旋；backend/CLAUDE.md 還把 --retries -1 當建議範例。
3. **M4 批次半寫**：mops_scraper._upsert_data 的 per-record 迴圈無防護，每 500 列 commit；任一列失敗時已落地的批次留下半寫狀態、無 rollback、無紀錄哪些列被丟。
4. **NF3 session 連環污染**：_sync_data_source 的 per-(year,market) except continue 從不 rollback 兩個 session；若例外發生在 flush 後，下一個市場的查詢直接 PendingRollbackError，整個 source 後續全部連環失敗，CLI 照樣印 completed。
5. **M5 垃圾快取**：MOPS 維護頁（HTTP 200）被無條件寫進當日 cache，之後同日所有 rerun 重用垃圾頁解析出 0 列並「成功」。
6. **parser 靜默丟列**：violation_service 解析迴圈的 except Exception: pass 完全不記錄被丟棄的列。

## Root Cause

ETL 設計把「不要中斷整個批次」誤實作成「吞掉所有失敗且不留痕跡」：服務層不回傳成敗統計、CLI 無從判斷、例外路徑沒有 rollback 與計數，重試迴圈缺乏絕對上限與對維護頁的斷路。

## Proposed Solution

1. **成敗統計回傳 + CLI fail-loud（M11）**：新增輕量 SyncReport 結構（per-source：成功與否、寫入列數、跳過列數、錯誤摘要），sync_companies / sync_violations / MOPS _sync_data_source / sync_all 回傳之；CLI 印出 per-source 摘要表，任何 source 失敗即 raise typer.Exit(1)；下載失敗同樣計為該 source 失敗。
2. **重試上限與斷路器（H3）**：_fetch_with_retry 即使 retries 為負也受總嘗試次數上限（50 次）約束；連續 5 次偵測到維護頁即視為被限流，中止整個 detail sync 並回報；backend/CLAUDE.md 的 --retries -1 範例改為有限值並註明 -1 已被上限約束。
3. **MOPS 批次完整性（M4 + NF3）**：_upsert_data 改為 per-record try/except（失敗列記 warning 含列識別資訊並計入 skipped）；commit 邊界改為每 (year, market) 一次；_sync_data_source 的 except 路徑對 session 與 archive_session 都 rollback 後再 continue，並把該 (year, market) 計入失敗。
4. **快取驗證（M5）**：寫入 cache 前驗證內容（非空、含預期表格標記、無維護頁字串），維護頁視為該 (year, market) 失敗且不得寫 cache；cache 命中但解析 0 列時，作廢該 cache 重抓一次，重抓後仍 0 列才接受為空並記 log。
5. **parser skip log**：violation_service 解析迴圈的 except 改為記 warning（含來源與列序）並累計 skipped 數，於摘要呈現。

## Non-Goals

- 不加 DB unique constraint、不清既有重複資料（change 5 範圍）。
- 不改公司比對邏輯與歸屬正確性（change 5b 範圍）。
- 不處理 M12（run 級交易/checkpoint-resume），僅收斂 commit 邊界到 (year, market)。
- 不改 export 流程（change 3 已完成）。
- sync-company-details 的個別公司失敗不觸發非零 exit（長爬流程個別失敗屬常態），僅於摘要呈現失敗數；全數失敗或斷路器觸發才非零退出。
- 不為 sync_all 改造子程序架構（其已依子指令 exit code 中止，自然受惠）。

## Success Criteria

- 任一違規 source 下載失敗或解析異常時，sync-violations 以非零 exit 結束並列出失敗 source（CLI 測試覆蓋）；sync-companies、sync-mops 同理。
- 全部 source 成功時 CLI 印出 per-source 摘要（寫入/跳過列數）且 exit 0。
- retries 設為 -1 時，_fetch_with_retry 在持續失敗下於 50 次嘗試內終止（單元測試以 mock 時鐘覆蓋）；連續 5 次維護頁觸發斷路中止。
- MOPS 單列壞資料不再中止整個 (year, market)：其餘列照常寫入、壞列數出現在摘要（單元測試覆蓋）。
- 第一個 (year, market) 失敗後，後續 (year, market) 不再出現 PendingRollbackError、可正常寫入（單元測試覆蓋）。
- 維護頁內容不會寫入 cache；cache 命中 0 列會重抓一次（單元測試覆蓋）。
- uv run pytest 全綠、ruff check / format --check 通過；對真實 MOPS 以單一年度執行 sync-mops 煙霧測試 exit 0 且印出摘要（執行前備份兩個 DB 檔）。

## Capabilities

### New Capabilities

- `backend-etl-fail-loud`: CLI 同步指令的成敗統計與非零退出 — 任何 source 失敗不得假性成功。
- `backend-etl-bounded-retries`: 重試絕對上限與維護頁斷路器 — 不存在無限重試路徑。
- `backend-mops-sync-integrity`: MOPS 批次寫入完整性 — per-record 防護、(year, market) 級 commit/rollback、cache 內容驗證、跳過列記錄。

### Modified Capabilities

(none)

## Impact

- Affected specs: backend-etl-fail-loud（新增）、backend-etl-bounded-retries（新增）、backend-mops-sync-integrity（新增）
- Affected code:
  - Modified:
    - backend/app/cli/main.py
    - backend/app/services/mops_scraper.py
    - backend/app/services/company_detail_scraper.py
    - backend/app/services/violation_service.py
    - backend/app/services/company_service.py
    - backend/tests/test_mops_scraper.py
    - backend/CLAUDE.md
    - docs/BACKEND_AUDIT.md
    - docs/REMEDIATION_PLAN.md
  - New:
    - backend/app/services/sync_report.py
    - backend/tests/test_sync_fail_loud.py
    - backend/tests/test_bounded_retries.py
  - Removed: (none)
