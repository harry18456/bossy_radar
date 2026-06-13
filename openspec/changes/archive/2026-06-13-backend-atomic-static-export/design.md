## Context

ExportService.export_all 目前的流程：先 shutil.rmtree 刪掉整個輸出目錄（即前端 SSG 消費的 public/data），再依序執行 catalog、yearly-summaries、system-status、2615 個公司 profile、leaderboards 的逐檔寫入；_save_json 以 open(path, "w") truncate-then-write。整段無 temp 目錄、無失敗還原。

export_yearly_summaries 與 export_leaderboards 各自是 aggregation route（get_yearly_summary）與 leaderboard route（get_leaderboards）的近逐行複製，已存在實際 drift：route 受 include 參數控制查哪些表，export 永遠全查（NF1）。

bottom 榜語意錯誤（NF2）：route 與 export 的違規榜先以 limit*2 取 top 池，_build_violation_leaderboard 再從該池尾端切出 bottom_by_count / bottom_by_fine，因此「違規最少榜」實際是「違規前 20 名左右的尾端」。薪資榜的 bottom 是獨立 asc 查詢，語意正確。

測試基礎：backend/tests 已有 conftest（in-memory SQLite 的 test_engine / test_session / client / seed_companies fixtures），但 ExportService 從未被任何測試 import（H7）。ExportService.export_all 內部自行 Session(engine) 綁定生產 engine，需要可注入性才能測。

## Goals / Non-Goals

**Goals:**

- export 失敗時，既有輸出目錄內容保持與 export 前完全相同；成功時整批原子切換。
- 單一 JSON 檔寫入不可能留下半寫/無效 JSON。
- yearly-summary 與 leaderboard 的組裝邏輯各只存在一份，route 與 exporter 共用；export 輸出與 route 回應形狀/值一致並有 parity 測試鎖住。
- 違規榜 bottom_by_count / bottom_by_fine 反映全體有違規公司的升冪前 N 名。

**Non-Goals:**

- 不動 ETL sync（change 4）、DB constraint/migration（change 5）、公司比對（change 5b）。
- 不重新匯出並提交 frontend/public/data（資料發布獨立決策）。
- L15/L16/L17（export 效能與 system-status 完整性低項）此次不做，明列於 proposal Non-Goals。
- 不改 CLI 介面（export 指令參數不變；例外自然冒泡使 Typer 以非零結束）。

## Decisions

### export_all 改寫 temp 目錄並原子 swap

**選擇**：ExportService 寫入同一父目錄下的 temp 目錄（output_dir 同層的 .tmp 後綴目錄），全部 export 步驟成功後執行 swap：既有正式目錄 rename 為 .bak → temp rename 為正式名 → 刪除 .bak。任何步驟失敗：保留正式目錄原封不動、刪除 temp、讓例外冒泡（Typer CLI 因此非零結束）。export 開始時先清除上次殘留的 .tmp / .bak。建構子不再急切建立正式目錄結構，目錄建立全部發生在 temp 側。

**理由**：rename 在同一檔案系統上是原子操作；temp 與正式目錄同父目錄保證同檔案系統。失敗視窗縮小到兩次 rename 之間，且該視窗內 .bak 仍是完整舊資料，下次 export 可自動回收。

**捨棄方案**：(a) 就地逐檔覆寫不刪目錄 — 無法處理「應刪除的過期檔案」（如下市公司 profile），且中途失敗仍是混合狀態；(b) 檔案系統快照/硬連結 — 平台相依、複雜度不成比例。

### _save_json 單檔原子寫入

**選擇**：_save_json 改為寫入同目錄的暫存檔（目標檔名加 .tmp 後綴）後 os.replace 到目標路徑。

**理由**：os.replace 在 Windows/POSIX 都保證原子取代，消除 truncate-then-write 的半寫視窗（L14）。temp swap 已保護整體目錄，單檔原子化另外保護「同目錄重複匯出單一檔案」與未來的增量匯出路徑。

### rmtree 目標驗證防呆

**選擇**：所有刪除（殘留 temp/.bak 清理、swap 時刪 .bak）只對 resolve 後位於 output_dir 父目錄內、且名稱符合本服務命名規則（正式名 / .tmp / .bak 後綴）的路徑執行；正式目錄本身永不被 rmtree（只被 rename）。對不符合規則的路徑丟 ValueError。

**理由**：L13 指出 output_dir 未驗證直接 rmtree 是 foot-gun；新流程中正式目錄不再需要被刪除，刪除面收斂到自家命名的暫存目錄。

### yearly-summary 抽共用 builder

**選擇**：新增 backend/app/services/yearly_summary_builder.py，提供單一函式 build_yearly_summary_items(session, include, year=None, company_code=None, market_type=None, industry=None) -> list[YearlySummaryItem]，內容為現行 route 的 Step 1-5（年份集合、公司過濾、違規/環境違規統計、四張 MOPS 表配對、skip-empty、include 控制），include 解析（all 展開）也住在此模組。aggregation route 改為呼叫 builder 後只負責排序與分頁；export_yearly_summaries 改為以 include 全集呼叫 builder，再按 year 分組寫各年檔，index.json 的 years/year_stats/total_count 從 builder 回傳結果推導，不另行查詢。

**理由**：NF1 的 drift 根因是兩份複製；單一來源後 include 語意天然一致，export 等價於 route 的 include=all 全量呼叫。

**捨棄方案**：export 直接呼叫 route handler — route 簽名綁 FastAPI Query/分頁/HTTP 語意，exporter 需要的是無分頁全量，硬共用反而醜。

### leaderboard 抽共用 builder 並修正 bottom 榜語意

**選擇**：新增 backend/app/services/leaderboard_builder.py，提供 build_leaderboard_response(session, limit=10, years_to_include=3) -> LeaderboardResponse。違規榜（歷年累計與各年度）改為：對 Violation 與 EnvironmentalViolation 各做**無 limit** 的 group by company_code 全量彙總（行數上限為公司數），在 Python 合併 labor+env 成 total_count/total_fine 後，top 取 desc 前 N、bottom 取 asc 前 N（僅含 total > 0 的公司）。薪資榜查詢邏輯不變，整段搬入 builder。route 與 export_leaderboards 都改為呼叫此 builder。

**理由**：NF2 的根因是 bottom 從截斷的 top 池切尾端；全量彙總後 top 與 bottom 都是精確語意（現行 top 池 max() 合併在邊界情況同樣不精確，一併修正）。全量 group by 行數受公司數（≤2615）約束，成本可忽略。

**捨棄方案**：只為 bottom 加 order by asc 的獨立 SQL 但保留 limit*2 top 池 — labor+env 合併後的 total 排序在 SQL 端做不乾淨（跨兩表），且 top 池的 max() 合併不精確問題依舊。

### ExportService 可測試性（engine 注入）

**選擇**：export_all 增加可選 session 參數（或建構子接受 engine override），測試以 conftest 的 in-memory engine/session 驅動；既有 CLI 呼叫路徑不變。

**理由**：H7 指出 export 層零測試的根因之一是寫死生產 engine；注入後 atomicity 與 parity 測試都能以 tmp_path + seed 資料執行。

### export 層測試與 route parity 測試

**選擇**：新增三個測試檔：
- backend/tests/test_export_atomicity.py：失敗注入（monkeypatch 任一 export 步驟丟例外）後舊目錄位元組級不變、temp 清理、例外冒泡；成功 swap 後無 .tmp/.bak 殘留；_save_json 原子性（寫入後目標為合法 JSON、無 .tmp 殘留）；防呆對不合規路徑丟 ValueError。
- backend/tests/test_export_route_parity.py：seed 小資料集（含違規、環境違規、四張 MOPS 表、多年份），exporter 各年檔內容與 get_yearly_summary(include=all, size 足夠大) 回傳 items 逐項相等；leaderboards.json 與 get_leaderboards 回應相等。
- backend/tests/test_leaderboard_builder.py：seed 25 間公司違規數 1..25，斷言 bottom_by_count 為違規數 1..10（升冪）、top_by_count 為 25..16（降冪）；labor+env 合併 total 正確。

**理由**：Success Criteria 全部可由這三檔自動化覆蓋；parity 測試同時是 H8 要求的 export→前端 JSON 合約測試的第一塊。

## Implementation Contract

**行為**：

1. export 過程中任一步驟丟例外時：正式輸出目錄的檔案集合與每個檔案內容，與 export 開始前完全相同；同層 .tmp 目錄被清除；呼叫方收到原例外；CLI 以非零 exit code 結束。
2. export 成功後：正式目錄為全新完整輸出，父目錄內無本服務的 .tmp / .bak 殘留。
3. 連續兩次 export（第一次成功）之間若有殘留 .tmp/.bak（模擬 crash），第二次 export 開始時自動清除並正常完成。
4. _save_json 寫完後，目標路徑必為完整合法 JSON；同目錄無對應 .tmp 殘留。
5. 以相同 session 資料，export 的 yearly-summaries/{year}.json 各項與 get_yearly_summary(include=["all"], 同公司過濾, size 涵蓋全量) 的 items 完全相等；index.json 的 years 與各年檔案一致、year_stats.count 等於各年檔 item 數、total_count 等於總和。
6. 以相同 session 資料，export 的 leaderboards.json 與 get_leaderboards 回應（model_dump mode=json）完全相等。
7. 違規榜 bottom_by_count：全體 total_count（labor+env 合計）> 0 的公司中取 total_count 最小的前 N 名升冪排列；bottom_by_fine 同理以 total_fine。top 榜為對應降冪前 N。歷年累計與每個年度榜皆適用。
8. aggregation 與 leaderboard 兩個 route 的對外 HTTP 介面（路徑、參數、回應 schema）不變；既有 tests/test_api_* 全數通過。

**介面 / 資料形狀**：

- build_yearly_summary_items(session, include: set[str] | list[str] | None, year=None, company_code=None, market_type=None, industry=None) -> list[YearlySummaryItem]，include 含 "all" 時展開為全部資料類別；回傳依 year 降冪、公司順序穩定。
- build_leaderboard_response(session, limit: int = 10, years_to_include: int = 3) -> LeaderboardResponse。
- ExportService 建構子簽名維持 ExportService(output_dir: Path)；export_all 可接受測試注入的 session。

**失敗模式**：

- export 失敗：例外冒泡（不吞）、舊資料完整保留 — 這是本 change 的核心保證。
- swap 兩次 rename 之間 crash：父目錄內存在 .bak（完整舊資料）與已 rename 的新資料其一；下次 export 自動清理殘留後重建。
- 防呆觸發（路徑不合規）：ValueError，不執行任何刪除。

**驗收**：

- cd backend && uv run pytest 全綠（含三個新測試檔）；uv run ruff check . 與 ruff format --check . 通過。
- 對真實 DB 執行 uv run python -m app.cli.main export --output-dir <temp 驗證目錄> exit 0；檔名集合與 frontend/public/data 一致；抽樣比對 company-catalog.json 與任一公司 profile 結構一致；leaderboards.json 的 bottom_by_count 內容為升冪小數值公司（語意修正後的預期差異）。
- frontend 既有 npm run test（exporter 語意對照測試）不受影響（public/data 未被覆寫）。

**範圍邊界**：

- In scope：backend/app/services/export_service.py、新增兩個 builder 模組、backend/app/api/routes/leaderboard.py、backend/app/api/routes/aggregation.py、三個新測試檔、docs 勾選。
- Out of scope：backend/app/cli/main.py 介面、ETL sync 程式、DB schema、frontend 任何檔案、public/data 資料內容。

## Risks / Trade-offs

- [Windows 上 rename 非空目錄需目標不存在，兩次 rename 間有 crash 視窗] → 順序設計保證視窗內 .bak（完整舊資料）一定存在；下次 export 啟動時自動回收殘留；測試覆蓋殘留回收路徑。
- [bottom/top 改全量 group by 後榜單內容改變（包含 top 榜邊界修正）] → 這是語意修正的預期結果；parity 測試保證 route 與 export 一致，REMEDIATION 完成判準明訂 bottom 必須反映全體最後 N 名。
- [route 重構等價性風險] → 既有 tests/test_api_aggregation / leaderboard 類測試 + 新 parity 測試雙重鎖定；include 解析邏輯原樣搬移。
- [exporter 與 route 對「年份過濾下的 available_years」語意差異] → exporter 全量呼叫不帶 year 過濾，沿用 route 的全量分支，無分歧點。
