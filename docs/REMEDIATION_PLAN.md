# 修正規劃

> 建立日期：2026-06-09
> 依據：`docs/LIVE_RECON.md` 對 `docs/FRONTEND_AUDIT.md`、`docs/BACKEND_AUDIT.md`、`docs/EXTENSION_AUDIT.md` 的生產環境校準。

## 排序原則

1. 先修已在線上生效的問題。
2. 先修每次 ETL/export 都會製造或放大資料風險的問題。
3. 先修低工時但能提高發布安全性的防線。
4. API 層 DoS 類問題目前因 FastAPI 未公開而降為 latent，改列為公開 API 前 gate。
5. DB constraint 不先硬上；必須先有 migration baseline 與既有資料清理。

## Spectra Change 切分

| 順序 | Change | 性質 | 範圍 | 觸發條件 |
|---:|---|---|---|---|
| 1 | `frontend-ssg-correctness-and-headers` | Bug Fix / Reliability | `dataMode=static`、`failOnError=true`、CI 跑 generate、安全標頭、移除 production console log、AdSense loader guard、首頁 leaderboards 改 SSG | 立即 |
| 2 | `frontend-watchlist-static-profile-loading` | Bug Fix / Performance | watchlist 改讀 `data/companies/{code}.json` 組年度資料；修 `page_size` / `limit` / `size` 參數契約 | 立即 |
| 3 | `backend-atomic-static-export` | Bug Fix / Reliability | `export_service.py` 改 temp dir + atomic swap；單檔 JSON temp write + `os.replace` | 下次正式 export 前 |
| 4 | `backend-etl-fail-loud-bounded` | Bug Fix / Observability | CLI exit code、source 成敗統計、`retries=-1` 上限、parser skip log、MOPS 維護頁/cache 驗證、單列失敗 rollback | 下次正式 ETL 前 |
| 5 | `backend-db-integrity-foundation` | Bug Fix / Data Integrity | migration baseline、清重複資料、unique constraints、upsert 改 DB conflict、SQLite WAL / busy_timeout / FK | ETL fail-loud 後 |
| 6 | `extension-widget-render-safety` | Security Fix | 移除 `main.js` render 的 raw `innerHTML` sink，改 DOM API / `textContent` | 擴充套件更新前 |
| 7 | `extension-trust-cache-privacy-boundaries` | Security / Compliance Fix | `custno=` 限 104 domain、bridge 每個讀取點驗證、SW schema/Content-Type/timeout、修隱私政策 | 擴充套件更新前 |
| 8 | `frontend-accessibility-error-boundaries` | Enhancement / A11y | `error.vue`、autocomplete ARIA、skip link、icon aria-label、tabs 語意 | 前端主缺陷修完後 |
| 9 | `backend-api-hardening-before-public-api` | Security / Scalability Gate | `size ge=1`、`yearly-summary` SQL 化、catalog 分頁、CORS/rate limit/docs 關閉 | FastAPI 對外公開前 |

## 第一批執行順序

1. `frontend-ssg-correctness-and-headers`
2. `frontend-watchlist-static-profile-loading`
3. `backend-atomic-static-export`
4. `backend-etl-fail-loud-bounded`
5. `backend-db-integrity-foundation`

第一批完成後再評估是否切入 extension 兩個 change。若近期不發布擴充套件，extension 可維持 parked；若要上架或更新商店版本，`extension-widget-render-safety` 必須先於 `extension-trust-cache-privacy-boundaries`。

## 依賴關係

- `frontend-watchlist-static-profile-loading` 不依賴新的 export 格式；現有 `public/data/companies/{code}.json` 已含 watchlist 圖表需要的 `non_manager_salaries`。
- `backend-db-integrity-foundation` 依賴 migration baseline 與資料清理；不得先直接加 DB unique constraint。
- `backend-api-hardening-before-public-api` 不阻擋目前 SSG production，但阻擋任何 dynamic API 公開部署。
- extension 的 XSS sink 修正優先於 bridge/cache 修正；sink 不消除，上游驗證只能降低觸發率，不能封閉漏洞類型。

## 暫緩項目

- Backend API `size=-1`、`yearly-summary` live API 記憶體爆量、`/companies/catalog` 無分頁：目前未公開，延到公開 API gate。
- soft-404：Vercel 對未預渲染路由已回真正 404，優先級下調。
- 前端 JSON-LD stored XSS：已被 unhead 轉義機制緩解；僅保留 defense-in-depth。

## 完成判準

- 第一批完成後，production SSG build 必須 fail-loud，首頁 HTML 必須含排行榜資料，watchlist 不得下載全量 yearly summaries。
- 下一次 ETL/export 失敗時必須非零 exit 或明確失敗摘要，且既有 `public/data` 不得被半寫或清空。
- DB 完整性 change 完成後，重跑 sync 不得累積重複違規或 MOPS 列。
- extension 安全 change 完成後，所有不可信文字不得經 raw `innerHTML` 插值進入 104 頁面 DOM。
