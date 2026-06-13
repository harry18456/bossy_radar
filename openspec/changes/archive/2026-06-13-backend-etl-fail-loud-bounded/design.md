## Context

CLI（backend/app/cli/main.py）的 sync-companies / sync-violations / sync-mops 在下載或同步失敗時只寫 log，最後無條件印 completed 並 exit 0；只有 sync-env 的下載失敗會 raise typer.Exit(1)。sync_all 以子程序依序執行各指令並檢查 returncode——所以只要子指令 exit code 正確，sync_all 自然 fail-loud。

服務層現況：
- company_service.sync_companies(data_dir, target_types) 與 violation_service.sync_violations(data_dir, target_sources) 都回傳 None，內部失敗自行吞掉。
- mops_scraper._sync_data_source 對每個 (year, market) 包 try/except continue，從不 rollback session/archive_session（NF3）；_upsert_data 的 per-record 迴圈無防護且每 500 列跨 (year, market) commit（M4）。
- mops_scraper._fetch_and_process 以當日日期為 cache key，fetch 後只 raise_for_status 就無條件寫 cache，無內容驗證（M5）——MOPS 維護頁是 HTTP 200。
- company_detail_scraper._fetch_with_retry 在 retries < 0 時 while True 無出口（H3），維護頁字串被當 retryable 例外。
- violation_service 解析迴圈 except Exception: pass 靜默丟列。

既有測試：tests/test_mops_scraper.py 覆蓋 parser 與 upsert 基本路徑（用 test_session fixtures）；tests/conftest.py 提供 in-memory engine。mops_scraper 的 _sync_data_source 直接用生產 engine 建 Session——測試需以可注入方式驅動（仿 change 3 的 ExportService 注入模式）。

## Goals / Non-Goals

**Goals:**

- 任何 source 失敗時 CLI 非零退出並輸出 per-source 成敗摘要；全成功時摘要 + exit 0。
- 不存在無限重試路徑；對限流/維護頁有斷路器。
- MOPS 單列失敗不污染整個 (year, market)；(year, market) 失敗不污染後續批次（rollback）。
- 維護頁/垃圾內容不進 cache；可疑 cache 自動重抓一次。
- 被丟棄的解析列有 log 與計數，不再靜默蒸發。

**Non-Goals:**

- DB constraint/去重（change 5）、比對歸屬（change 5b）、run 級交易 checkpoint（M12）。
- sync-company-details 個別公司失敗不觸發非零 exit（摘要呈現失敗數；全數失敗或斷路器觸發才非零）。
- 不改 sync_all 子程序架構。

## Decisions

### SyncReport 統計結構與服務層回傳

**選擇**：新增 backend/app/services/sync_report.py，提供 dataclass SourceResult（name、success、rows_written、rows_skipped、error）與 SyncReport（results 清單、add 方法、has_failures 屬性、render_summary() 回傳多行字串）。company_service.sync_companies、violation_service.sync_violations、mops_scraper 的 _sync_data_source / sync_all / 四個 sync_* 包裝、company_detail_scraper.sync_all_details 改為回傳 SyncReport（或將結果併入呼叫端傳入的 report）。

**理由**：CLI 需要結構化資訊才能決定 exit code 與摘要；dataclass 無外部依賴、好測試。

**捨棄方案**：用例外中斷整個指令 — 違背「單一 source 失敗不應阻止其他 source 嘗試」的批次語意；只印 log 不回傳 — CLI 無從判斷。

### CLI 摘要與非零退出

**選擇**：sync-companies / sync-violations / sync-mops 在執行後印出 report.render_summary()，若 report.has_failures 則 raise typer.Exit(1)。下載步驟失敗（download_file 回傳 False）直接把該 source 記為失敗，不再只 logger.error。sync-env 維持現有下載失敗退出行為並加上 sync 段摘要。sync-company-details 印摘要；僅當「有嘗試但全數失敗」或斷路器觸發時 exit 1。

**理由**：M11 修法原文「追蹤 per-source 成功/失敗計數並在摘要呈現；任何 source 失敗或異常 0 列時 exit 非零」。

### 重試絕對上限與維護頁斷路器

**選擇**：company_detail_scraper 模組層常數 MAX_TOTAL_ATTEMPTS = 50、MAINTENANCE_BREAK_THRESHOLD = 5。_fetch_with_retry 改為 for 迴圈：有限 retries 用 retries+1 次嘗試，retries < 0 用 MAX_TOTAL_ATTEMPTS；回傳 None 或文字之外，另以回傳值/旗標區分「維護頁」失敗型態。sync_all_details 追蹤連續維護頁次數，達門檻即中止整輪並於 report 記 circuit_broken；backend/CLAUDE.md 範例改 --retries 5 並註記 -1 受 50 次上限約束。

**理由**：H3 修法原文「即使 infinite 模式也要有 wall-clock deadline 或總次數上限（如 50）＋ N 次連續維護頁後 circuit breaker」。

**捨棄方案**：wall-clock deadline — 測試需要 mock 時鐘較繁瑣，總次數上限等效且更可預測。

### MOPS (year, market) 級 commit 與例外 rollback

**選擇**：_upsert_data 移除 500 列批次 commit，改由 _sync_data_source 在每個 (year, market) 成功處理後 commit 兩個 session；except 路徑先對 session 與 archive_session rollback() 再 continue，並把該 (year, market) 記入 report 失敗。_sync_data_source 增加可選 session/archive_session 參數供測試注入（預設自建，CLI 路徑不變）。

**理由**：NF3 修法原文「except 內對兩 session rollback()」；commit 邊界對齊失敗邊界，rollback 才能乾淨（M4 修法選項二）。

**捨棄方案**：savepoint — SQLite + 雙 session 下複雜度高；500 列批次 commit 的記憶體效益在單 (year, market) 數千列規模下可忽略。

### MOPS per-record 防護與跳過列記錄

**選擇**：_upsert_data 的 per-record 主體包 try/except：失敗列 log warning（含 raw_company_code、year、market_type 與例外訊息）、計入 skipped、continue；回傳 (written, skipped) 供 report。violation_service 解析迴圈的 except Exception: pass 改為 log warning（含 source 與列序號）並累計 skipped，計入該 source 的 SourceResult。

**理由**：M4 修法原文「per-record body 包 try/except（仿 parser 的 per-row 防護）」；parser skip log 是 REMEDIATION change 4 明列項目。

### MOPS cache 內容驗證與可疑快取重抓

**選擇**：mops_scraper 新增 _is_valid_mops_html(html) 私有函式：非空、不含「服務暫時無法提供」「請稍後再試」、含小寫 table 標籤字樣。fetch 後內容無效 → 不寫 cache、視為該 (year, market) 失敗（raise 讓外層計數）。cache 命中時若解析出 0 列 → 刪除該 cache 檔重抓一次；重抓後仍 0 列 → 接受為空（某些年度/市場本來就無資料）並 log。

**理由**：M5 修法原文「寫 cache 前驗證內容；既有 cache 命中卻 parse 出 0 列時視為訊號重抓」；0 列不能一律當失敗，未來年度合法為空。

### ETL fail-loud 測試組

**選擇**：新增 backend/tests/test_sync_fail_loud.py（typer CliRunner：mock 服務回傳含失敗的 SyncReport → exit 1 + 摘要含失敗 source；全成功 → exit 0；MOPS _sync_data_source 注入 session 測 NF3 rollback 連環、M4 壞列、M5 cache 驗證）與 backend/tests/test_bounded_retries.py（mock httpx 與 time.sleep：retries=-1 持續失敗 50 次內終止；連續維護頁斷路）。

**理由**：Success Criteria 全部自動化；CliRunner 是 Typer 官方測試路徑。

## Implementation Contract

**行為**：

1. sync-violations 在任一 source 下載失敗或同步擲例外時：stdout 含 per-source 摘要（失敗 source 標示 FAILED 與錯誤摘要）、process exit code 為 1；其餘 source 仍被嘗試。sync-companies、sync-mops 同樣規則（sync-mops 的失敗單位是 (source_key, year, market) 聚合到 source 層）。
2. 全部 source 成功時：stdout 含每個 source 的寫入列數與跳過列數，exit code 0。
3. _fetch_with_retry(retries=-1) 在持續失敗下總嘗試次數 ≤ 50 後回傳 None；有限 retries 行為不變（retries+1 次嘗試）。
4. sync_all_details 連續 5 次維護頁偵測後不再發出新請求，回報 circuit broken；該情況 CLI exit 1。
5. MOPS 單列建模失敗：該列 skipped+1 並 log warning（含 raw_company_code/year/market），同 (year, market) 其他列正常寫入。
6. (year, market) 處理擲例外後：兩個 session 皆被 rollback；下一個 (year, market) 正常 flush/commit，不出現 PendingRollbackError。
7. 維護頁回應：cache 目錄不產生該 (year, market) 的 cache 檔，該單位記為失敗。
8. cache 命中且解析 0 列：原 cache 檔被刪除、重新 fetch 一次；重抓仍 0 列則視為合法空集（不算失敗）。
9. 既有成功路徑語意不變：對乾淨資料的 sync 寫入結果與現行相同（既有 test_mops_scraper.py 全綠）。

**介面 / 資料形狀**：

- SourceResult(name: str, success: bool, rows_written: int = 0, rows_skipped: int = 0, error: str | None = None)
- SyncReport.add(result)、SyncReport.has_failures -> bool、SyncReport.render_summary() -> str
- company_service.sync_companies / violation_service.sync_violations / mops_scraper.sync_all 與四個 sync_* / company_detail_scraper.sync_all_details 回傳 SyncReport。
- mops_scraper._sync_data_source(source_key, years, markets, session=None, archive_session=None) -> SourceResult（彙總該 source 全部 (year, market)）。

**失敗模式**：

- 下載失敗 / HTTP 錯誤 / 維護頁 / 解析例外 / 寫入例外 → 對應 SourceResult.success=False 與 error 摘要；CLI exit 1。
- 個別列失敗 → rows_skipped 計數 + warning log，不影響 source 成敗判定。
- 斷路器觸發 → 中止後續請求、exit 1。

**驗收**：

- uv run pytest 全綠（含兩個新測試檔與既有 test_mops_scraper.py）；ruff check / format --check 通過。
- 真實煙霧測試（先備份 backend/bossy_radar.db 與 backend/archive.db）：uv run python -m app.cli.main sync-mops --start-year 114 --end-year 114 exit 0 且 stdout 含 per-source 摘要。
- backend/CLAUDE.md 不再以 --retries -1 為建議範例。

**範圍邊界**：

- In scope：backend/app/cli/main.py、mops_scraper.py、company_detail_scraper.py、violation_service.py、company_service.py、sync_report.py（新）、兩個新測試檔、test_mops_scraper.py 擴充、backend/CLAUDE.md、docs 勾選。
- Out of scope：environmental_service 內部重構（僅 CLI 層沿用既有 fail-loud）、DB schema、export、frontend。

## Risks / Trade-offs

- [服務回傳型別改變影響呼叫端] → 全部呼叫端都在 cli/main.py 與測試內，一次改齊；sync_all 走子程序不受介面影響。
- [(year, market) 單次 commit 增加單筆交易大小] → 每單位數百至數千列，SQLite 可輕鬆處理；換得乾淨 rollback 邊界。
- [0 列重抓策略對合法空年度多打一次請求] → 每 (year, market) 最多一次額外請求，可接受；避免垃圾 cache 整日鎖死。
- [真實煙霧測試寫入生產 DB] → 執行前備份兩個 DB 檔；MOPS upsert 以 (raw_company_code, year, market_type) 去重為冪等。
