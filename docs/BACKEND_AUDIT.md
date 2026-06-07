# Bossy Radar 後端稽核報告

> 產出日期：2026-06-07
> 方法：8 個面向平行深讀 → 每個 critical/high/medium 發現派獨立 agent 對抗式驗證（讀真實程式碼嘗試反駁，部分實跑 SQLite/FastAPI 驗證）→ 跨面向綜整。
> 規模：48 個 agent、573 次工具呼叫。
> 結果：**61 個發現，60 個成立、1 個被推翻**（誤報率 1.6%）。
>
> 嚴重度為「對抗式驗證後的調整值」(adjusted_severity)，可能低於初判。
> 勾選框供逐項處理追蹤。

---

## 整體判斷

**做得好的部分（已驗證）**
- SQL 全程參數化，**無 SQL/ORM injection**；sort/include 以 `hasattr` + 白名單把關，使用者字串不進 raw SQL。
- HTTP 層**純唯讀**（grep `POST/PUT/DELETE/PATCH` 無任何結果），唯一變更路徑是 CLI。
- 無硬編碼 secret（`.env` 已 gitignore，只追蹤空的 `.env.template`）。
- scraper 解析有 per-row try/except、動態欄數、cell 存取防護，單列壞資料不會炸整個 sync。
- 依賴版本（FastAPI 0.128 / Starlette 0.50 / pydantic 2.12 / requests 2.32.5）皆新、無已知可利用 CVE。
- money 以 int 儲存（無 float 精度問題）；ROC↔西元轉換在 export 正確；中文 `ensure_ascii=False` 正確。

**真正的問題集中在四個系統性根因**
1. 輸入邊界缺失（分頁/篩選）
2. DB 層零完整性約束
3. ETL 靜默失敗、假性成功回報
4. ~1900 行寫入/匯出/CLI 程式碼零測試

---

## 🔴 五大最優先（高效益、可一次根治）

| # | 問題 | 位置 | 為何優先 |
|---|------|------|---------|
| P1 | `size=-1` → 全表傾印 DoS | 8 條分頁端點 | 最高嚴重度＋最低工時，一個共用 `PaginationParams` Depends 一次堵死全部 |
| P2 | DB 零完整性約束＋非冪等插入 | models + 3 個 upsert | 公開統計隨每次同步累積重複列；多數資料完整性問題的根 |
| P3 | ETL 靜默失敗、假性成功 | `_parse_json` + CLI | operator 無從得知資料正在流失 |
| P4 | export 非原子 `rmtree` 抹除公開資料 | `export_service.py` | 一次失敗就讓 SSG 網站資料下線；temp-swap 是小改動 |
| P5 | `retries=-1` 無限重試卡死 | `company_detail_scraper.py` | 被推薦的旗標會讓排程同步永不結束並打爆政府站 |

---

## 🔴 High（驗證後）

### [ ] H1. `size` 無下界 → `size=-1` 傾印整張表（DoS／分頁上限被繞過）
- **面向**：routes-api / security-config（雙面向獨立指出）
- **位置**：`backend/app/api/routes/companies.py:16`、`violations.py:26`、`environmental_violations.py:26`、`mops.py:70/109/148/184`、`aggregation.py:111`
- **問題**：所有分頁端點宣告 `size: int = Query(20, le=100)` 只有上界、缺 `ge=1`。負值通過 FastAPI 驗證，直接進 `.limit(size)`。**已實測**：SQLite `LIMIT -1` = 無上限，`GET /api/v1/violations?size=-1` 回傳全部 11,889 列（cap 100 被完全繞過）。
- **影響**：無認證、無 rate limit 的公開 API 上，單一請求即可耗盡記憶體/CPU/頻寬，並默默廢掉 `le=100` 這個安全控制。
- **修法**：所有 `size` 改 `Query(20, ge=1, le=100)`；建議抽共用 `PaginationParams` Depends，避免新路由再次漏掉。

### [ ] H2. `yearly-summary` 把全部資料預載進記憶體再 Python 排序分頁
- **面向**：routes-api
- **位置**：`backend/app/api/routes/aggregation.py:186-419`
- **問題**：無 filter 時 `select(Company).all()` 載入全部 2,615 公司，再對 4 張 MOPS 表各跑 `IN (所有 codes)` 載入完整 ORM 物件（實測 11,551 / 11,431 / 13,370 / 1,228 列，約 37K 列），在 Python 建 matrix → 排序 → **最後才切分頁**。`page`/`size` 完全無保護作用。前端 `useApi.ts:49` 確實會用無 filter 的 `getYearlySummary({size:1})` 呼叫此路徑。
- **影響**：記憶體/CPU 隨整個資料集成長（非分頁大小），公開端點的 DoS 放大器。
- **修法**：把 filter/join/sort/LIMIT 推進 SQL，或在 ETL/export 階段預算 matrix；至少強制一個收斂 filter，並把「存在性檢查」與「完整物件」拆開。

### [ ] H3. `retries=-1` 無限重試卡死整個 sync
- **面向**：scrapers / cli-etl（雙面向）
- **位置**：`backend/app/services/company_detail_scraper.py:164-206`；CLI `cli/main.py:288-290`；`backend/CLAUDE.md` 把 `--retries -1` 當範例
- **問題**：`while True` 只在 `retries >= 0 and attempt > retries` 時 break；retries<0 時 break 永不可達，唯一出口是成功 return。對 hard-down 或持續限流的主機會永遠重試（backoff 上限 60s）。更糟：MOPS 維護頁 `服務暫時無法提供`/`請稍後再試` 被當成 retryable，等於對正在限流的伺服器無限自旋。外層 per-company `try/except continue` 無法救（因為 inner loop 永不 raise/return）。
- **影響**：被文件推薦的旗標會讓排程 job 永不結束、持續打政府站、恐被 ban IP。
- **修法**：即使 infinite 模式也要有 wall-clock deadline 或總次數上限（如 50）＋ N 次連續維護頁後 circuit breaker；停止把 `-1` 當正常用法文件化。

### [ ] H4. export 非原子：先 `rmtree` 抹除全部好資料再重建，中途失敗 = 公開資料下線/損毀
- **面向**：export-service
- **位置**：`backend/app/services/export_service.py:71-91`（`_clean_output_dir` + `export_all`）；逐檔寫入 `_save_json:52-69`
- **問題**：`export_all()` 第一步 `shutil.rmtree(output_dir)`，再跑一長串 DB 驅動寫入（含逐公司數千檔、數十個 `model_validate` 可能丟例外），**無 temp-dir-then-rename、無交易、無 try/except 還原**。任何失敗（DB 例外、磁碟滿、Ctrl-C）→ 公開目錄被刪光或半寫。`_save_json` 用 `open(path,"w")` truncate-then-write，crash 中途 = 無效 JSON。
- **影響**：SSG `public/data` 直接消費這些檔，一次失敗讓網站資料下線或供應壞掉的子集。
- **修法**：寫進 temp 兄弟目錄，全部成功後原子 swap（rename old→.bak、tmp→output、刪 .bak）；`_save_json` 寫 temp 檔再 `os.replace`；`export_all` 包 try/except 失敗時保留舊目錄。

### [ ] H5. 無 `disposition_no` 的違規每次同步無條件重插（非冪等）
- **面向**：cli-etl
- **位置**：`backend/app/services/violation_service.py:191-218`；`environmental_service.py:252-255`
- **問題**：去重鍵為 `(data_source, disposition_no)`，但 `if not v.disposition_no: target_session.add(v); continue` 在無處分字號時直接無條件 add。`_parse_json:129` 用 `(row.get("處分字號") or "").strip()` → 缺欄位時為空字串（falsy），此分支可達。無任何 unique constraint 當後盾。
- **影響**：每次排程同步都對所有空處分字號的違規重插一份，膨脹計數、扭曲 leaderboard/aggregation，污染 SSG 匯出。
- **修法**：為空處分字號列建確定性合成鍵（hash of 公司名+處分日+法條+罰鍰+來源），或加 DB unique constraint + `INSERT OR IGNORE`/`ON CONFLICT`。永不無條件 add。

### [ ] H6. 全表零 `UniqueConstraint`，去重無 DB 後盾（TOCTOU）
- **面向**：cli-etl / models-db
- **位置**：`backend/app/models/*.py`（全 7 個 model，grep `UniqueConstraint|unique=True|__table_args__` 零命中）
- **問題**：所有 upsert 是 app 層 SELECT-then-INSERT。MOPS 鍵 `(raw_company_code, year, market_type)`、violation `(data_source, disposition_no)`、env `disposition_no` 都只有非唯一 index。dedup bug、並行/重試 sync、部分 commit 都可產生重複列，DB 一律接受。
- **影響**：下游所有 aggregation（yearly-summary、leaderboard）被重複列污染。
- **修法**：以 `__table_args__` 加 `UniqueConstraint` 於各自然鍵，並改用真正 upsert（SQLite `ON CONFLICT`）。讓冪等性由 DB 保證而非脆弱 Python。
- **註**：models-db 面向把此項調為 medium（CLI 文件化為循序執行，並行 TOCTOU 機率低），cli-etl 面向因「空鍵每次重插」確定性 bug 維持 high。

### [ ] H7. 整個 ETL/export/CLI 層零測試覆蓋，「85%」覆蓋率數字誤導
- **面向**：tests-quality
- **位置**：`export_service.py`(841)、`environmental_service.py`(368)、`company_detail_scraper.py`(291)、`crawler_service.py`(39)、`cli/main.py`(363)，約 1,900 行
- **問題**：`uv run pytest --cov=app` 回報 TOTAL 85%，但這些檔從未被任何測試 import，coverage.py 直接從分母排除（grep tests/ 對 `ExportService/CrawlerService/...` 零命中）。**實測**把它們算進去後真實功能覆蓋率 ≈ **55.9%**。最高風險的程式碼（DB 寫入、雙 DB archive、匯入時比對、URL 清理、SSG 匯出）可在全測試綠燈下 regress。
- **修法**：`pyproject.toml` 加 `[tool.coverage.run] source = ['app']` 讓 0% 檔現形；為 `ExportService.export_*`（對 tmp_path）、`EnvironmentalService`、`CompanyDetailScraper`、Typer CLI（`CliRunner`）補測試。

### [ ] H8. export→前端 JSON 合約無測試，且 export 複製 ~400 行路由邏輯會 drift
- **面向**：tests-quality
- **位置**：`export_service.py:461-841`(export_leaderboards)、`194-408`(export_yearly_summaries)
- **問題**：網站是 SSG，前端消費的是 export 出的靜態 JSON 而非 live API。`export_leaderboards` 幾乎逐行複製 `leaderboard.py` 路由（同 SQL、同 helper、同 all-time merge），`export_yearly_summaries` 複製 `aggregation.py`，無共用 helper、無測試斷言匯出檔形狀/值。對 `leaderboard.py` 修了 bug 卻沒同步 export → 出貨壞資料但測試全綠。
- **修法**：加整合測試 seed in-memory DB → `ExportService(tmp_path).export_all()` → 斷言各 JSON 結構/值對齊對應 API 回應。更好：把 leaderboard/yearly 邏輯抽成單一共用函式，路由與 exporter 共用，只測一次。

---

## 🟠 Medium（驗證後）

### [ ] M1. branch-prefix 比對回傳「第一個」startswith 命中（非確定性、錯誤連結）
- **位置**：`company_matcher.py:97-101`，**同邏輯複製於** `violation_service.py:170-175`、`mops_scraper.py:758-762`（共 3 處）
- **問題**：`self.branch_list` 以 raw DB row 序建立（無 order_by），回傳第一個 name 是輸入前綴者，無最長前綴、無邊界字、無 tie-break。兩公司全名互為前綴時，連到哪家取決於 DB 順序、跨 DB 重建會變。
- **影響**：公開違規歸屬平台上，違規可能被默默掛到錯誤上市公司，且 run-to-run 不穩定。
- **修法**：選所有候選中**最長前綴**（並要求前綴後有 廠/分公司/營業所 等邊界字，或多個 code 符合時拒絕）；去重成單一實作，其他處委派 `CompanyMatcher`。

### [ ] M2. 董事長/負責人姓名比對可把個人違規錯掛到上市公司
- **位置**：`company_matcher.py:103-119`（Level-4 fallback）；勞動路徑實作於 `violation_service.py:177-182`
- **問題**：Level 4 拿違規 `company_name` 直接比對 chairman map，唯一候選即連結。勞動違規「事業單位名稱或負責人」欄常是個人姓名且**完全不抽 tax_id**，若該人名恰為某上市公司唯一董事長 → 違規被掛到該公司。唯一守門只有「chairman 字串唯一」。
- **影響**：sole-proprietor/個人違規被誤掛上市公司，誹謗級資料完整性風險。
- **修法**：Level 4 限定來源欄確為個人時才比對，或要求另一佐證訊號（tax_id），否則丟 archive 不自動連結。

### [ ] M3. bare/broad except 靜默丟棄壞違規列、無 log
- **位置**：`violation_service.py:137-139`
- **問題**：每列建構包在 `except Exception: pass`，註解寫「Log but continue」但**沒有 log**。對照 `environmental_service.py:221` 至少 debug log。無 skip 計數，上游 schema 改動可默默丟掉大量違規，下游仍印「Parsed N records」。
- **修法**：log 例外與列識別碼（warning），維護並輸出 skipped 計數。

### [ ] M4. MOPS 批次單列失敗在部分 commit 後中止整個年度/市場
- **位置**：`mops_scraper.py:690-739`（`_upsert_data`）+ `151-167`（per-(year,market) try/except）
- **問題**：per-record loop 無 try/except，`model_class(**record)` 等可丟 ValidationError；每 500 列 `commit()`。任一列失敗 → 例外冒泡到 per-(year,market) `except continue`，但已 flush 的 500-boundary 列已落地 → 半寫不一致、無 rollback、無紀錄哪些列被丟。額外風險：未 rollback 的 session 被下一市場重用可能 `PendingRollbackError`。
- **修法**：per-record body 包 try/except（仿 parser 的 per-row 防護）；或每 (year,market) 一次 commit / 用 savepoint，失敗乾淨 rollback。

### [ ] M5. MOPS 暫時性錯誤/維護頁被快取、當日所有 rerun 重用
- **位置**：`mops_scraper.py:216-243`
- **問題**：cache key 以今日日期命名，fetch 只 `raise_for_status()`（維護頁是 HTTP 200 過不了）就無條件寫入 cache，**無內容驗證**（不像 `CompanyDetailScraper` 會檢查維護字串與 >1000 byte）。當日後續 run 走 cache 分支重解析垃圾頁 → 0 列、靜默「成功」直到隔日。
- **修法**：寫 cache 前驗證內容（非空、有預期表格、無維護標記）；既有 cache 命中卻 parse 出 0 列時視為訊號重抓。

### [ ] M6. SQLite 無 `busy_timeout`、無 WAL → 並發讀寫時 `database is locked`
- **位置**：`backend/app/db/session.py:7-12`
- **問題**：兩引擎只設 `check_same_thread=False`，預設 rollback-journal + busy_timeout=0。FastAPI 同步路由走 threadpool（多連線），CLI sync 長交易每 500/1000 列 commit（程式註解自承「Batch commit to avoid long lock」）。sync 寫鎖期間任何 API 讀立即 `SQLITE_BUSY` → 未處理 500。
- **修法**：註冊 connect-event 每連線跑 `PRAGMA busy_timeout=5000; journal_mode=WAL; foreign_keys=ON;`（兩引擎）。WAL 讓讀寫並行，busy_timeout 讓寫者等待而非報錯。

### [ ] M7. FK 宣告但 `PRAGMA foreign_keys` 未開，約束純裝飾
- **位置**：`db/session.py`（無 PRAGMA）；FK 定義於 6 個 child model
- **問題**：每張子表宣告 `foreign_key="company.code"`，但 SQLite 預設不強制、程式從未 `PRAGMA foreign_keys=ON`。`company_code` 可指向不存在公司而被接受。archive DB 的 company 表恆空更明顯。
- **修法**：同 M6 的 connect-event 開 `foreign_keys=ON`；明確決定 archive DB 是否該帶 FK。

### [ ] M8. 僅 `create_all()`、無 migration → 改 model 必然 schema drift
- **位置**：`company_service.py:128` + `violation_service.py:39-40`、`mops_scraper.py:140-141`、`environmental_service.py:116-117`（4 個 service）
- **問題**：`create_all()` 只建不存在的表，永不 ALTER。任何 model 變更（新欄、新 index、新 unique、改型）對既有 `bossy_radar.db`(~40MB)/`archive.db`(~320MB) 不生效。無 Alembic。
- **影響**：上面建議加的 unique/index 不會套用到既有 DB，會出現 `no such column` 或需手動清庫（資料遺失）。
- **修法**：導入 Alembic（或等價），移除散落的 `create_all()` 改成版本化 migration。

### [ ] M9. CORS env var 用直覺格式會 boot crash（`list[str]` 需 JSON）
- **位置**：`core/config.py:8`；消費於 `main.py:9-16`
- **問題**：pydantic-settings v2 對 list 型 env 以 JSON 解析。**實測**在 .env 填純 URL / 逗號清單 / `*` 皆 `SettingsError` boot crash，只有 JSON 陣列 `["http://a.com"]` 可。已 commit 的 .env 正是用 JSON，顯示開發者已踩過坑。（註：空值 `BACKEND_CORS_ORIGINS=` 從 .env 檔讀會 fallback 為 `[]`，不 crash → 故由 high 降 medium。）
- **修法**：改用 CSV 友善 validator（`str | list[str]` + `field_validator` 以逗號切），並在 `.env.template` 註明確切格式。

### [ ] M10. `/companies/catalog` 無分頁、整表序列化
- **位置**：`companies.py:50-56` → `company_service.py:81-119`
- **問題**：`select(8 欄).order_by(code)` 無 LIMIT、無分頁參數，回傳整個公司宇宙（數千列）＋ per-row Python loop。無 rate limit。
- **修法**：此端點本為搜尋建議用，加硬上限/快取，或直接走已存在的靜態 JSON export（ETag/gzip）。
- **註**：SSG 部署下前端與擴充功能實際讀的是靜態 `company-catalog.json`，live 端點較少用 → routes-api 面向把此項降為 low，security-config 面向維持 medium（端點仍公開可重複呼叫）。

### [ ] M11. CLI 各 source 失敗被吞、整體仍報成功、exit 0
- **位置**：`mops_scraper.py:149-167`（per-(year,market) `except continue`）；`cli/main.py:98/168/229`（無條件印 completed）；`violation_service.py:137-139`（bare pass）
- **問題**：`sync-mops`/`sync-companies`/`sync-violations` 下載或解析失敗只 log，不 abort、不設非零 exit，最後印「completed successfully」。只有 `sync-env`（`cli/main.py:263-267`）會 `raise typer.Exit(1)`。
- **影響**：半數來源失敗的 run 仍 exit 0，排程器/CI 把部分或空 sync 當健康。
- **修法**：追蹤 per-source 成功/失敗計數並在摘要呈現；任何 source 失敗或異常 0 列時 exit 非零；`sync-companies/violations` 比照 `sync-env` 失敗即響。

### [ ] M12. 批次 commit 無 run 級交易，crash 無 checkpoint/resume
- **位置**：`violation_service.py:221-224`、`mops_scraper.py:732-735`、`environmental_service.py:297-300`
- **問題**：每 N 列 commit，無 run 級交易、無 checkpoint（grep `checkpoint|resume|cursor|sync_state` 無）。crash 後 DB 半更新；同日重跑又因 date-stamped cache 跳過重抓 **並** 重插空處分字號列（與 H5 複合）。有處分字號的列因 keyed upsert 是冪等的（部分自癒）。
- **修法**：每 source 包單一交易（或 stage 進暫存表再 swap），記錄 sync-run/checkpoint 列供 resume，使重跑冪等收斂。

### [ ] M13. 分頁 `size` 下界（0/負）從未驗證、從未測試
- **位置**：8 條 list 端點；`test_api_companies.py` 只測 page=1&size=2
- **問題**：與 H1 同根，但這裡聚焦測試缺口。**實測**：size=0 → `LIMIT 0` 靜默空頁＋`total_pages=0`（但 total>0，回應自相矛盾）；size=-5 → `LIMIT -5` 回傳整表＋`total_pages` 為負數洩漏進回應。
- **修法**：加 `ge=1`（同 H1）；補 parametrized 邊界測試（size=0/-1/101、page=0、page 超過 total_pages）。

### [ ] M14. filter/sort 與 error 分支幾乎無測試（mops 47%、violations/env 69%、aggregation 66%）
- **位置**：`mops.py`、`violations.py`、`environmental_violations.py`、`aggregation.py`
- **問題**：3/4 MOPS 端點整個 body 從未被呼叫；違規/環境的所有 filter where-clause（`in_`、`extract('year')`、罰鍰/日期 range）與 sort loop 未測；yearly-summary 的 `include_violations/include_env_violations` aggregation 區塊未測。既有測試只抓預設無 filter 清單並斷言 total==1。
- **修法**：每端點補各 filter 參數、多值 filter、year(extract)、罰鍰/日期 range、invalid sort（應忽略不 500）、有效 sort 的測試；yearly-summary 測 `include=violations/env_violations/all` 與 invalid include。

### [ ] M15. in-memory SQLite + StaticPool 把雙引擎 main/archive 路由與鎖定行為藏住
- **位置**：`tests/conftest.py:20-30`；`test_mops_scraper.py:160`（archive_session 傳同一個 test_session）
- **問題**：全測試用單一共用 in-memory 連線，無法重現 `database is locked` 與雙引擎 commit 交錯；MOPS 測試把 main 與 archive 設成同一 session → matched→engine / unmatched→archive 路由從未真正驗證，路由錯了也會通過。
- **修法**：至少一個整合測試用兩個 tmp_path 檔案 DB 分別當 engine/archive_engine，斷言 matched 落主庫、unmatched 落 archive，並跑 >1000 列的 batch-commit 路徑。

### [ ] M16. 無空 DB／負向測試（leaderboards / sync-status / catalog / aggregation）
- **位置**：`test_api_leaderboard.py`（僅一個 happy-path）；`test_api_routes.py:75-84`
- **問題**：只用 seeded 資料測。sync-status 測試甚至 `pytest.skip()` on 404 並 `assert status in [200, 500]` → 500 regression 也通過。（實測空 DB 下這些端點目前回 200，故影響部分屬推測，但測試缺口與「接受 500」屬實。）
- **修法**：加空 DB 測試斷言 200＋well-formed 空 payload；收緊 sync-status 測試為 `== 200` 並驗 schema，移除 skip-on-404 與 500-OK。

### [ ] M17. CSV 損毀根因（標為 uncertain，建議查證但別照單全收）
- **位置**：`company_service.py:159-213`（`_parse_csv`）；`scripts/fix_corrupted_data.py`
- **問題**：原發現主張 header 偵測（掃 `公司代號`）脆弱導致整欄錯位，但驗證者認為更可能是 CSV 引號/內嵌逗號（`download_file` 原樣寫 `response.content` 無 dialect 處理）或**舊版 parser** 寫入。目前 `_parse_csv` 已有 market_type 強制覆寫(`:200`)、code 格式驗證(`:176`)、address-URL guard(`:188-193`)。`fix_corrupted_data.py` 反映歷史 bug，非當前路徑。
- **修法**：驗證偵測到的 header 含完整已知欄位、每列欄數符合預期否則 fail loud；確認 url-shaped 值只落 網址 欄；別在疑似損毀時靜默 continue。**處理前先確認真正成因**。

---

## 🟡 Low（多為未獨立驗證，集中列出）

| # | 問題 | 位置 | 修法摘要 |
|---|------|------|---------|
| [ ] L1 | `page` 無上界，巨大 OFFSET 濫用 | 各 list 端點 | 加 `le=10000` 或改 keyset 分頁 |
| [ ] L2 | filter 接受任意字串無 enum；`name=%` LIKE 萬用字元逼全表掃 | `violations.py:30-37`、`company_service.py:50` | 改 `Literal/Enum` 回 422；escape LIKE metachar |
| [ ] L3 | `size=0` 回應形狀自相矛盾（total>0 但 total_pages=0） | 各端點 | 加 `ge=1` 後自動解決 |
| [ ] L4 | CORS `allow_credentials=True` 配 `*` methods/headers | `main.py:10-16` | 唯讀 API 設 `allow_credentials=False`、methods 限 `GET/OPTIONS` |
| [ ] L5 | ROC 日期盲切末 4 碼、錯誤靜默回 None | `company_service.py:251-273`、`violation_service.py:232-256` | 抽共用 date util、明確驗證格式、失敗 warning log |
| [ ] L6 | 雙 DB 各自獨立 commit 無原子性 | `violation_service.py:221-227` 等 | upsert loop 包 try/except 兩 session rollback |
| [ ] L7 | 比對鍵無正規化（全/半形、空白、大小寫）→ 漏 dedup | `company_matcher.py:36-81` | 共用 canonicalize（NFKC、whitespace collapse、suffix 正規化） |
| [ ] L8 | `_parse_money` 剝除所有非數字、串接多段數字 | `company_service.py:275-288` | 取第一個連續數字 token，非空卻失敗時 log |
| [ ] L9 | service 層分頁無上限、接受非正 size | `company_service.py:74-77` | 服務內 clamp 1..100 |
| [ ] L10 | 無連線池，每次 new httpx.Client | 三個 scraper | 每 scraper 一個共用 Client/Session |
| [ ] L11 | MOENV API 回應無上限累積在記憶體 | `environmental_service.py:60-95` | 加 max-page/record 上限、串流寫檔 |
| [ ] L12 | ROC/西元年啟發式 `<1000` 模糊 | `violation_service.py:232-256` | 依來源契約明確判定，驗證年份落合理區間 |
| [ ] L13 | `output_dir` 未驗證直接 `rmtree`（foot-gun） | `export_service.py:75` | resolve 絕對路徑並 assert 在預期 base 內 |
| [ ] L14 | 逐檔 JSON truncate-then-write | `export_service.py:52-69` | 寫 temp 檔 + `os.replace` |
| [ ] L15 | `export_company_details` N+1（每公司 6 query） | `export_service.py:117-129` | bulk-fetch 各表一次、記憶體 group |
| [ ] L16 | system-status 只報 4 張 MOPS 表中的 1 張 | `export_service.py:448-458` | 補 non_manager_salary/welfare_policy/salary_adjustment |
| [ ] L17 | 熱迴圈中建丟棄式 Company ORM 當 name fallback | `export_service.py:724-797` | 用字串 fallback，不建 ORM |
| [ ] L18 | MOPS upsert 查詢 `(code,year,market_type)` 缺複合 index | `mops_scraper.py:712-718` | 加複合 index（並設為 unique，見 H6） |
| [ ] L19 | archive DB 帶空 company 表與 dangling FK | `mops_scraper.py:141` 等 | archive 用無 FK model 或明文記載 |
| [ ] L20 | `capital` 在 catalog 被轉 float | `company_service.py:110` | 保持 int |
| [ ] L21 | 無 rate limit；`/docs`、OpenAPI 預設公開 | `main.py:7` | 加 slowapi + 反代 body 上限；prod 關 `/docs` |
| [ ] L22 | 6 個會打 live MOPS 的探索腳本被 commit | `scripts/test_mops_*.py` 等 | 刪除或移出版控（含重複的 `firstin='ture'` typo config） |
| [ ] L23 | CLI 無 dry-run、觀測性弱、成功訊息與實況不符 | `cli/main.py` | 加 `--dry-run`、持久化 sync-run 摘要、exit code 反映實況 |
| [ ] L24 | MOPS prefix/branch 比對無唯一性守門 | `mops_scraper.py:741-764` | 要求前綴唯一才連結，否則 archive（同 M1） |
| [ ] L25 | MOPS parser 測試用 OR 斷言、整合測試無斷言 | `test_mops_scraper.py:44-89/169-193` | 釘死預期值移除 OR；mock sync 後斷言 DB 列 |
| [ ] L26 | 殘留 hello/goodbye CLI 與註解化敘事 | `cli/main.py:42-49/137-163` | 移除；補 CliRunner 測試與 include 文件對齊 |

---

## ✅ 被推翻的誤報（驗證價值示例）

**「政府 CSV 是 Big5/MS950 卻用 UTF-8 讀 → 靜默亂碼」** — 初判 High，看似就是 `fix_corrupted_data.py` 的存在原因。
驗證 agent **實際下載 4 個 live CSV**（`t187ap03_L/O/R/P.csv`），逐位元組檢查為 **UTF-8 帶 BOM**，`decode('utf-8')` 全成功，硬編碼修補的 000638/000104 欄位完全對齊（`WWW.KUANZHO.COM.TW` 是 網址 欄的合法值，非錯位）→ 機制不成立，**推翻**。
→ 結論：`fix_corrupted_data.py` 反映歷史 parser bug，非當前下載/解析路徑。（殘留小瑕疵：未用 `utf-8-sig`，第一欄名帶 BOM，但該欄從不被讀取。）

---

## 待後續確認（建議下一輪稽核）

- [ ] **Stored-XSS via static JSON**：scraped 的 `company_name` 等 → DB → 公開 JSON → Nuxt。查前端是否有 `v-html` 消費這些欄位（後端不轉義，屬前端面向）。
- [ ] **`yearly-summary` 正確性**（非僅效能）：6 表記憶體 join/排序/分頁、`include` 過濾、tie-break、跨年合併的正確性未被測試。
- [ ] **MOENV_API_KEY query 傳遞**：`environmental_service.py:56,62` 金鑰入 URL，恐落上游/代理存取日誌（gov API 多僅支援此法；目前自家 log 未印金鑰，OK，但值得記載）。
- [ ] **前端面向整體稽核**：本報告僅涵蓋 backend。

---

## 附錄：跨面向系統性根因

1. **輸入邊界從未集中** — 每條新路由重複漏掉 `ge=1`、catalog 無分頁、sort 無 enum。
2. **DB 零結構性完整性** — 無 unique、FK pragma off、無 WAL、無 migration、非冪等插入。
3. **靜默吞例外＋假性成功** — 從 `_parse_*` 的 `return None/0` 到 CLI 無條件「completed successfully」。
4. **比對邏輯 4 份複製且都帶同樣 bug** — `CompanyMatcher` 是正典，但 violation_service 內聯重寫、MOPS、export 各一份。
5. **多步驟寫入無 all-or-nothing 邊界** — 雙 DB 各自 commit、export 先刪後寫、JSON truncate-then-write。
6. **過度貪婪的 string/number/date 強制轉換** — money 串接、ROC 盲切、CSV header 一變版就錯位。
