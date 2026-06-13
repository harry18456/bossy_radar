# 修正規劃

> 建立日期：2026-06-09
> 依據：`docs/LIVE_RECON.md` 對 `docs/FRONTEND_AUDIT.md`、`docs/BACKEND_AUDIT.md`、`docs/EXTENSION_AUDIT.md` 的生產環境校準。
>
> **更新（2026-06-10，第二輪複查）**：`frontend-ssg-correctness-and-headers`（commit `fc6478b`）已完成並 archive。第二輪對抗式驗證確認其餘所有 High/Medium 仍成立、零誤判，並新增以下項目（詳見各 audit 報告的「🔁 第二輪複查」段）：
> - ✅ **CSP 形同虛設（已修，change 0，待部署）**：fc6478b 加的 `vercel.json` CSP 缺 `script-src`/`default-src`，自稱的「XSS 最後防線」未建立 → change `0` `frontend-csp-hardening` 已補完整 script-src allowlist（定案 allowlist + `'unsafe-inline'`）並收斂 console/footer/JSON-LD。
> - ⚖️ **違規歸屬法律暴露**：M1/M2 把違規掛到錯誤上市公司是妨害名譽風險，從 medium 散項升為獨立 change `5b`，拉進第一批。
> - 🟠 backend 新發現 NF1（yearly export 已 drift）、NF2（leaderboard bottom 榜語意錯）併入 change `3`；NF3（sync-mops 不 rollback）併入 change `4`。

## 排序原則

1. 先修已在線上生效的問題。
2. 先修每次 ETL/export 都會製造或放大資料風險的問題。
3. 先修低工時但能提高發布安全性的防線。
4. API 層 DoS 類問題目前因 FastAPI 未公開而降為 latent，改列為公開 API 前 gate。
5. DB constraint 不先硬上；必須先有 migration baseline 與既有資料清理。

## Spectra Change 切分

| 順序 | Change | 性質 | 範圍 | 觸發條件 |
|---:|---|---|---|---|
| ✅1 | `frontend-ssg-correctness-and-headers` | Bug Fix / Reliability | `dataMode=static`、`failOnError=true`、CI 跑 generate、安全標頭、移除 production console log、AdSense loader guard、首頁 leaderboards 改 SSG | **已完成（fc6478b，待部署）** |
| ✅0 | `frontend-csp-hardening` | Security Fix | **補 change 1 缺口**：`vercel.json` CSP 補明確 `script-src`（self + 列明 AdSense/GA 網域；SSG 無 per-request nonce，**定案採 allowlist + `'unsafe-inline'`**，殘餘風險記於 design.md）+ `connect-src`/`frame-src`/`img-src`，先盤點廣告網域避免擋廣告；清乾淨殘留 console（`AdSenseUnit.vue` 等）、footer `rel=noopener`、JSON-LD 主動轉義 `<` | **✅ 已完成（待部署）** |
| ✅2 | `frontend-watchlist-static-profile-loading` | Bug Fix / Performance | watchlist 改讀 `data/companies/{code}.json` 組年度資料；修 `page_size` / `limit` / `size` 參數契約 | **✅ 已完成（2026-06-13，含 vitest 測試基礎 + typecheck 全綠）** |
| ✅3 | `backend-atomic-static-export` | Bug Fix / Reliability | `export_service.py` 改 temp dir + atomic swap；單檔 JSON temp write + `os.replace`；**抽 leaderboard/yearly 組裝為 route+export 共用函式（含 `include` 集合，修 NF1 yearly drift）；修 NF2 `bottom_by_*` 改獨立 `order by asc`** | **✅ 已完成（2026-06-13，含 L13/L14；parity 測試鎖定 route=export）** |
| ✅4 | `backend-etl-fail-loud-bounded` | Bug Fix / Observability | CLI exit code、source 成敗統計、`retries=-1` 上限、parser skip log、MOPS 維護頁/cache 驗證、單列失敗 rollback、**NF3：`sync-mops` 例外路徑對兩 session `rollback()`（防 `PendingRollbackError` 連環失敗）** | **✅ 已完成（2026-06-13，含 export atomic-swap 的 Windows rename race 修正；真實 sync-mops 煙霧驗證 fail-loud + exit 0 兩路徑）** |
| 5 | `backend-db-integrity-foundation` | Bug Fix / Data Integrity | migration baseline、清重複資料、unique constraints、upsert 改 DB conflict、SQLite WAL / busy_timeout / FK | ETL fail-loud 後 |
| 5b | `backend-violation-attribution-correctness` | ⚖️ Correctness / Legal | **M1/M2**：branch-prefix 取最長前綴 + 邊界字、多候選拒絕；Level-4 董事長姓名比對要求佐證訊號（tax_id）否則丟 archive 不自動連結；去重成單一 `CompanyMatcher` 實作 | **第一批內（法律暴露）** |
| 6 | `extension-widget-render-safety` | Security Fix | 移除 `main.js` render 的 raw `innerHTML` sink，改 DOM API / `textContent` | 擴充套件更新前 |
| 7 | `extension-trust-cache-privacy-boundaries` | Security / Compliance Fix | `custno=` 限 104 domain、bridge 每個讀取點驗證、SW schema/Content-Type/timeout、`fetchTaxIdBySlug` 加 timeout/大小上限（NF2）、修隱私政策（揭露 per-company + slug 主動帶 cookie 探測，NF1）、更新 `CLAUDE.md` 移除 `dispatched` latch（NF3） | 擴充套件更新前 |
| 8 | `frontend-accessibility-error-boundaries` | Enhancement / A11y | `error.vue`、autocomplete ARIA、skip link、icon aria-label、tabs 語意 | 前端主缺陷修完後 |
| 9 | `backend-api-hardening-before-public-api` | Security / Scalability Gate | `size ge=1`、`yearly-summary` SQL 化、catalog 分頁、CORS/rate limit/docs 關閉；**加 backend 啟動/CI 硬性 assert，強制本 change 在開 API 前完成（不靠純文件約束）** | FastAPI 對外公開前 |

## 第一批執行順序

0. ✅ ~~`frontend-ssg-correctness-and-headers`~~（已完成，commit fc6478b，待重新部署）
1. ✅ ~~`frontend-csp-hardening`~~（已完成，待部署；補上 script-src allowlist + console/footer/JSON-LD 收斂，11/11 tasks）
2. ✅ ~~`frontend-watchlist-static-profile-loading`~~（已完成，2026-06-13；watchlist 改 per-company profile、25 間實測不截斷、12/頁、typed params、vitest 對照 exporter 語意 8 測試）
3. ✅ ~~`backend-atomic-static-export`~~（已完成，2026-06-13；原子 swap + 共用 builder + bottom 榜語意修正，73 測試全綠、真實 DB 煙霧測試 2636 檔零結構差異）
4. ✅ ~~`backend-etl-fail-loud-bounded`~~（已完成，2026-06-13；SyncReport fail-loud、retries 上限 50 + 維護頁斷路、MOPS per-record 防護 + (year,market) commit/rollback + cache 驗證、parser skip log；順帶修 export atomic-swap 的 Windows rename race。96 測試全綠 + 真實 MOPS 雙路徑驗證）
5. `backend-db-integrity-foundation`
6. `backend-violation-attribution-correctness`（5b，法律暴露，不可留在 medium 散項）

第一批完成後再評估是否切入 extension 兩個 change。若近期不發布擴充套件，extension 可維持 parked；若要上架或更新商店版本，`extension-widget-render-safety` 必須先於 `extension-trust-cache-privacy-boundaries`。

## 依賴關係

- `frontend-csp-hardening` 與 change 1 同屬 SSG 出貨設定，但因 change 1 已 archive 故獨立成 change；CSP 與 AdSense/GA 網域需一次盤點，避免擋掉廣告。
- `frontend-watchlist-static-profile-loading` 不依賴新的 export 格式；現有 `public/data/companies/{code}.json` 已含 watchlist 圖表需要的 `non_manager_salaries`。
- `backend-atomic-static-export` 的 leaderboard/yearly 共用函式抽取（NF1/NF2）同時讓 route 與 exporter 收斂，避免 H8 的 drift 再發生。
- `backend-db-integrity-foundation` 依賴 migration baseline 與資料清理；不得先直接加 DB unique constraint。
- `backend-violation-attribution-correctness`（5b）獨立於 DB 完整性：change 5 修「不重複插入」，5b 修「不掛錯公司」，兩者不可互相取代。
- `backend-api-hardening-before-public-api` 不阻擋目前 SSG production，但阻擋任何 dynamic API 公開部署；其 gate 條件須落成 backend 啟動/CI 的硬性 assert，不靠純文件約束（避免未來開 API 時遺忘）。
- extension 的 XSS sink 修正優先於 bridge/cache 修正；sink 不消除，上游驗證只能降低觸發率，不能封閉漏洞類型。

## 暫緩項目

- Backend API `size=-1`、`yearly-summary` live API 記憶體爆量、`/companies/catalog` 無分頁：目前未公開，延到公開 API gate。
- soft-404：Vercel 對未預渲染路由已回真正 404，優先級下調。
- 前端 JSON-LD stored XSS：已被 unhead 轉義機制緩解；僅保留 defense-in-depth。
- **defense-in-depth / low 項的明確歸宿（避免正確建議系統性蒸發）**：前端主動轉義 JSON-LD 併入 change 0；其餘各報告 low/defense-in-depth 項，發布擴充或開 API 時隨對應 change 一併處理；不單獨開 change 但須在對應 change 的 tasks 明列，不得默默丟棄。

## 完成判準

- 第一批完成後，production SSG build 必須 fail-loud，首頁 HTML 必須含排行榜資料，watchlist 不得下載全量 yearly summaries。
- **CSP（change 0）完成後，`vercel.json` 的 CSP 必須實際限制 `script-src`（非空、非萬用），且 AdSense/GA 仍正常載入；不得停留在只有 `object-src`/`base-uri`/`frame-ancestors` 的半套狀態。**
- 下一次 ETL/export 失敗時必須非零 exit 或明確失敗摘要，且既有 `public/data` 不得被半寫或清空。
- DB 完整性 change 完成後，重跑 sync 不得累積重複違規或 MOPS 列。
- **違規歸屬 change（5b）完成後，個人/負責人違規不得在無佐證訊號下自動連結到上市公司；branch-prefix 比對須跨 run 確定性、不得因 DB 順序改變歸屬。**
- export 的 leaderboard/yearly 形狀必須與對應 route（帶相同 `include`）一致；`bottom_by_*` 必須反映全體最後 N 名而非 top 池尾端。
- extension 安全 change 完成後，所有不可信文字不得經 raw `innerHTML` 插值進入 104 頁面 DOM。
