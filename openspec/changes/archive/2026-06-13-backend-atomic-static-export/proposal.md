## Problem

三個會在每次 export/部署時製造或放大資料風險的問題（BACKEND_AUDIT H4、NF1、NF2，並涉及 H8）：

1. **Export 非原子（H4 + L14）**：export_all 第一步就 shutil.rmtree 刪光輸出目錄，再執行數千次 DB 驅動的逐檔寫入，全程無 temp-dir-then-rename、無失敗還原。中途任何失敗（DB 例外、磁碟滿、Ctrl-C）= 前端 public/data 被刪光或半寫，SSG 網站資料直接下線。單檔 _save_json 也是 truncate-then-write，crash 中途留下無效 JSON。另有 L13：output_dir 未驗證就直接 rmtree（foot-gun）。
2. **NF1：export_yearly_summaries 已實際 drift**：route 端受 include 參數控制，export 端是約 200 行的複製品、無 include 概念，兩邊已出現行為分歧；H8 指出這種逐行複製讓「route 修了 bug、export 沒同步」成為常態風險。
3. **NF2：leaderboard bottom_by_count / bottom_by_fine 榜語意錯誤（route 與 export 同源）**：bottom 榜取的是「被 limit*2 截斷的 top 池尾端」而非全體真正的最後 N 名，輸出的「違規最少」榜單實際上是「違規前 20 多名裡的尾端」，資料是錯的。

## Root Cause

- export 流程從未設計失敗路徑：先刪後寫、逐檔 truncate、無交易邊界（BACKEND_AUDIT 系統性根因 5「多步驟寫入無 all-or-nothing 邊界」）。
- leaderboard 與 yearly-summary 的組裝邏輯在 route 與 exporter 各複製一份（系統性根因「複製且 drift」），bottom 榜實作貪圖方便直接從 top 池切尾端。
- ETL/export 層零測試覆蓋（H7），錯誤語意與 drift 在綠燈下存活。

## Proposed Solution

1. **原子化 export**：export_all 改寫進同層級的 temp 目錄，全部成功後做原子 swap（舊目錄 rename 成 .bak → temp rename 成正式目錄 → 刪 .bak）；任何失敗保留舊目錄完整、清掉 temp 並以非零方式失敗。_save_json 改寫 temp 檔後 os.replace。rmtree 前驗證目標路徑（resolve 後必須是既有 export 輸出形狀或空目錄，拒絕意外路徑）。
2. **抽共用組裝函式**：yearly-summary 組裝（年份集合、違規/環境違規統計、MOPS 配對、skip-empty、include 集合）抽成單一共用 builder，aggregation route 與 exporter 共用，exporter 以 include=all 呼叫；leaderboard 組裝（含全部 SQL 查詢與回應建構）抽成單一共用 builder，route 與 exporter 共用。
3. **修正 bottom 榜語意**：違規排行榜的 bottom_by_count / bottom_by_fine 改為獨立查詢（對全體有違規的公司 order by count asc / fine asc 取前 N），不再從 top 池尾端切片；歷年累計與各年度榜同步修正。
4. **建立 export 層測試**：以 in-memory SQLite seed 資料，測試（a）export 失敗時舊輸出目錄完整保留、（b）單檔寫入原子性、（c）export 輸出與對應 route 回應形狀/值一致（yearly-summary 與 leaderboards 的 parity 測試）、（d）bottom 榜為真正的全體倒序前 N。

## Non-Goals

- 不動 ETL sync 流程的 fail-loud / rollback（change 4 backend-etl-fail-loud-bounded 範圍）。
- 不加 DB unique constraint 或 migration（change 5 範圍）。
- 不改 CompanyMatcher / 違規歸屬（change 5b 範圍）。
- 不重新匯出並提交 frontend/public/data 的資料內容（資料發布是獨立決策；本次驗證對 temp 目錄匯出，不覆寫已提交的靜態資料）。
- 暫緩 L15（export_company_details N+1 效能）、L16（system-status 只報 1 張 MOPS 表）、L17（熱迴圈建丟棄式 ORM）：純效能/完整性低風險項，明列於此不默默丟棄，待後續 change 處理。
- 不處理 API 層分頁/DoS gate（change 9 範圍）。

## Success Criteria

- 對 temp 目錄執行完整 export，途中任一 export 步驟被注入例外時：既有輸出目錄內容與 export 前完全相同（位元組級），且程序以非零/例外結束（測試覆蓋）。
- 成功 export 後：輸出目錄為完整新資料，無 .bak 或 temp 殘留（測試覆蓋）。
- 以相同 seed 資料，exporter 產出的 yearly-summaries 各年檔內容與 aggregation route（include=all、無分頁截斷情境）回傳 items 完全一致；leaderboards.json 與 leaderboard route 回應完全一致（parity 測試覆蓋）。
- seed 25 間公司違規數 1..25 時，bottom_by_count 為違規數 1..10 的公司（升冪）而非 top 池尾端（測試覆蓋）。
- uv run pytest 全綠、uv run ruff check 通過；實際對真實 DB 跑 CLI export 至 temp 目錄 exit 0，輸出檔案集合與現行 public/data 同形（檔名集合一致、抽樣 JSON 結構一致、bottom 榜內容為預期中的語意修正差異）。

## Capabilities

### New Capabilities

- `backend-export-atomicity`: 靜態 export 的原子性 — 失敗保留舊輸出、成功才整批切換、單檔寫入原子化、rmtree 目標驗證。
- `backend-yearly-summary-parity`: yearly-summary 組裝邏輯單一來源 — route 與 exporter 共用同一 builder（含 include 集合），輸出形狀/值一致。
- `backend-leaderboard-correctness`: leaderboard 組裝邏輯單一來源且 bottom 榜語意正確 — bottom_by_count / bottom_by_fine 反映全體升冪前 N 名。

### Modified Capabilities

(none)

## Impact

- Affected specs: backend-export-atomicity（新增）、backend-yearly-summary-parity（新增）、backend-leaderboard-correctness（新增）
- Affected code:
  - Modified:
    - backend/app/services/export_service.py
    - backend/app/api/routes/leaderboard.py
    - backend/app/api/routes/aggregation.py
    - docs/BACKEND_AUDIT.md
    - docs/REMEDIATION_PLAN.md
  - New:
    - backend/app/services/leaderboard_builder.py
    - backend/app/services/yearly_summary_builder.py
    - backend/tests/test_export_atomicity.py
    - backend/tests/test_export_route_parity.py
    - backend/tests/test_leaderboard_builder.py
  - Removed: (none)
