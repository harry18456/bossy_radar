## 1. Export 原子性（RED → GREEN）

- [x] 1.1 依 design「export 層測試與 route parity 測試」撰寫 backend/tests/test_export_atomicity.py 失敗測試，覆蓋 spec「Static export SHALL be all-or-nothing」（步驟中途注入例外後輸出目錄位元組級不變、temp 清除、例外冒泡；成功後無 .tmp/.bak 殘留；殘留 .tmp/.bak 下次 export 自動回收）、「Single JSON file writes SHALL be atomic」（目標為合法 JSON、無 .tmp 殘留）、「Export deletions SHALL be restricted to service-owned paths」（不合規路徑丟 ValueError 且不刪任何東西）。驗證：cd backend && uv run pytest tests/test_export_atomicity.py 失敗（行為尚未實作）。
- [x] 1.2 依 design「export_all 改寫 temp 目錄並原子 swap」「_save_json 單檔原子寫入」「rmtree 目標驗證防呆」「ExportService 可測試性（engine 注入）」改寫 backend/app/services/export_service.py：寫入 temp 兄弟目錄、成功後 rename 舊→.bak→新→正式→刪 .bak、失敗保留舊目錄並清 temp、_save_json 寫 .tmp 後 os.replace、刪除面收斂到自家命名路徑、export_all 可注入測試 session。驗證：uv run pytest tests/test_export_atomicity.py 全綠。

## 2. yearly-summary 共用 builder

- [x] 2.1 撰寫 backend/tests/test_export_route_parity.py 的 yearly 部分：seed 含違規/環境違規/四張 MOPS 表/多年份的小資料集，斷言 exporter 各年檔與 get_yearly_summary(include=all、size 涵蓋全量) items 逐項相等，並覆蓋 spec「Exported yearly summary index SHALL be derived from builder output」（index.json 的 years/year_stats/total_count 與各年檔一致）。此測試先以現行程式碼執行確認可運行（regression lock），實作後須持續綠燈。驗證：uv run pytest tests/test_export_route_parity.py 可執行且斷言有效（mutation check：暫時竄改 exporter 任一欄位組裝使測試轉紅後還原）。
- [x] 2.2 依 design「yearly-summary 抽共用 builder」新增 backend/app/services/yearly_summary_builder.py（build_yearly_summary_items 含 include 解析），backend/app/api/routes/aggregation.py 改為呼叫 builder 後僅排序/分頁，export_service 以 include 全集呼叫並由回傳結果推導 index；滿足 spec「Yearly summary assembly SHALL have a single shared implementation」（include 控制欄位的情境含於既有 route 測試與 parity 測試）。驗證：uv run pytest（parity + 既有 aggregation API 測試）全綠。

## 3. Leaderboard 共用 builder 與 bottom 榜語意

- [x] 3.1 撰寫 backend/tests/test_leaderboard_builder.py 失敗測試，覆蓋 spec「Violation bottom leaderboards SHALL reflect the true ascending order over all companies」spec 例：25 間公司違規數 1..25 時 bottom_by_count 為 C1..C10 升冪、top_by_count 為 C25..C16 降冪；labor 2 + env 3 的公司 total_count=5 且 labor_count/env_count 分列。並在 test_export_route_parity.py 加入 leaderboards.json 與 get_leaderboards 回應相等的 parity 斷言。驗證：uv run pytest tests/test_leaderboard_builder.py 失敗（現行 bottom 取 top 池尾端）。
- [x] 3.2 依 design「leaderboard 抽共用 builder 並修正 bottom 榜語意」新增 backend/app/services/leaderboard_builder.py（違規榜全量 group by 彙總、Python 合併 labor+env、top desc / bottom asc 切片、薪資榜原邏輯搬入），backend/app/api/routes/leaderboard.py 與 export_service 改用 builder；滿足 spec「Leaderboard assembly SHALL have a single shared implementation」。驗證：uv run pytest tests/test_leaderboard_builder.py tests/test_export_route_parity.py 全綠。

## 4. 整體驗證與文件

- [x] 4.1 全套品質關卡：cd backend && uv run pytest 全綠、uv run ruff check . 與 uv run ruff format --check . 通過。驗證：三個指令 exit 0。
- [x] 4.2 真實資料煙霧測試：對真實 DB 執行 uv run python -m app.cli.main export --output-dir 指向 temp 驗證目錄，exit 0；檔名集合與 frontend/public/data 一致；抽樣比對 company-catalog.json 與任一公司 profile 結構；leaderboards.json 的 bottom_by_count 為升冪小數值公司（NF2 語意修正的預期差異）；不覆寫 frontend/public/data。驗證：實測紀錄。
- [x] 4.3 [P] 同步勾選 docs/BACKEND_AUDIT.md（H4、L13、L14、NF1、NF2，H8 標注 parity 測試已建立）與 docs/REMEDIATION_PLAN.md（change 3 標記完成）。驗證：內容檢視，勾選與實際完成項一致。
