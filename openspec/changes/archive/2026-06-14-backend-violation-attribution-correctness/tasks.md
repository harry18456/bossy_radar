## 1. 準備與備份

- [x] 1.1 將 bossy_radar.db 與 archive.db 複製為帶時間戳的備份檔，作為動資料前的回滾點（決策四：以全量重抓重建取代既有資料回溯 的前置）。驗證：列出備份檔且大小與原檔相符。

## 2. CompanyMatcher 核心比對邏輯（TDD：先紅後綠）

- [x] 2.1 在 backend/tests/test_company_attribution.py 撰寫 table-driven 失敗測試，覆蓋 design 邊界案例表全部列（括號負責人、廠區後綴、臺灣土地銀行型主檔缺後綴、純人名、廣達型不模糊救回、多候選並列拒絕、確定性、公司代號層）。行為：每個輸入明確斷言期望的公司代號或 None。驗證：`uv run pytest tests/test_company_attribution.py` 全部紅（功能未實作）。
- [x] 2.2 實作公司代號精確比對層與統編層優先序，使 MOPS 原始代號命中即連結並優先於名稱、統編先於名稱（spec: Company code exact match takes highest priority；spec: Tax ID exact match precedes name matching；決策三：三來源比對收斂為單一 CompanyMatcher 並新增公司代號層）。驗證：對應子測試由紅轉綠。
- [x] 2.3 實作確定性最長前綴分公司比對，取最長前綴且結果不依賴公司載入順序（spec: Deterministic longest-prefix branch matching；決策一：分公司前綴比對改為確定性最長前綴與保守拒絕）。驗證：最長前綴與「同輸入跨兩次打亂順序結果一致」子測試轉綠。
- [x] 2.4 實作最長前綴後的尾綴（括號負責人、廠區、主檔缺後綴）一律歸同一公司，不需白名單或剝後綴，僅靠「公司全名為前綴」涵蓋（spec: Trailing annotations after a full-name prefix do not change attribution）。驗證：南山人壽保險股份有限公司(尹崇堯) 連 5874、臺灣土地銀行股份有限公司(何英明) 連 5857 子測試轉綠。
- [x] 2.5 實作多候選拒絕：多個不同代號並列最長前綴時回 None 以保確定性（spec: Reject ambiguous prefix matches when companies tie）。驗證：多候選並列子測試回 None。
- [x] 2.6 確保不做正規化或模糊救回：非上市的「有限公司」不因縮短為簡稱而連到上市公司（spec: No fuzzy or normalized recall that risks mis-attribution；決策五：不以正規化或模糊比對救回 archive 漏接）。驗證：廣達有限公司(曾坤升) 子測試回 None。
- [x] 2.7 移除第四層董事長純人名自動連結，純人名一律回 None（spec: No automatic linkage from bare personal names；決策二：停用第四層董事長純人名自動連結）。驗證：劉正忠、陳國寶 子測試回 None。

## 3. 三來源收斂與歸檔

- [x] 3.1 [P] 違規同步服務改委派 CompanyMatcher、移除內聯比對（含內聯 branch 第一個命中與 chairman 邏輯），未匹配寫入 archive（spec: Single shared matcher across all ETL sources；spec: Unmatched records are archived, not dropped；決策三：三來源比對收斂為單一 CompanyMatcher 並新增公司代號層）。驗證：違規同步服務測試綠，且 grep 確認 _upsert_violations 不再含內聯比對。
- [x] 3.2 [P] MOPS 爬蟲改委派 CompanyMatcher、移除 _match_company 內聯比對（spec: Single shared matcher across all ETL sources）。驗證：MOPS 測試綠，且 grep 確認 _match_company 內聯比對移除。
- [x] 3.3 [P] 環境裁罰服務維持委派 CompanyMatcher 並新增回歸測試，確認新規則下既有正確連結不退化（spec: Unmatched records are archived, not dropped）。驗證：環境服務回歸測試綠。

## 4. 實證一：對備份 DB 做 dry-run（不只單元測試）

- [x] 4.1 更新 backend/scripts/analyze_attribution_impact.py 使其反映最終比對規則，對備份 DB 跑出新邏輯 vs 現況的逐筆轉移統計。行為：腳本輸出三來源的保留／改連／移 archive／救回筆數。驗證：實際執行腳本，勞動主庫保留 11,874、移 archive 15（全為董事長純人名）；環境移 archive 1；MOPS 0（與 design 預測相符，偏差須解釋）。

## 5. 前端說明頁同步

- [x] 5.1 [P] 更新前端資料比對邏輯說明頁（frontend/app/pages/data-sources.vue）與 frontend/DATA.md，據實描述負責人姓名不再用於自動連結、改以統編／公司代號／公司全名／分公司前綴為準。行為：對外描述與新比對邏輯一致。驗證：內容 review，且 step 8 generate 後頁面文字正確。

## 6. 全量重抓重建（真實來源）

- [x] 6.1 依序執行真實來源同步並逐一驗 exit code：sync-companies、sync-violations、sync-env、sync-mops，使 DB 以新邏輯重建歸屬（決策四：以全量重抓重建取代既有資料回溯）。驗證：各 CLI exit code 為 0 且 SyncReport 無失敗來源。

## 7. 實證二：重抓後抽樣驗證

- [x] 7.1 重抓後再次執行 analyze_attribution_impact.py 並抽樣檢查歸屬結果。行為：純人名位於 archive、公司全名(負責人) 正確連結、無新誤掛、臺灣土地銀行型未被誤殺。驗證：抽樣輸出符合預期（劉正忠在 archive、南山人壽保險股份有限公司(尹崇堯) 連 5874）。

## 8. 匯出與前端部署驗證

- [x] 8.1 執行 export 產生靜態 JSON 並前端 generate，使比對結果反映於公司頁。驗證：export 與 generate exit code 0、抽查公司頁 JSON 含正確違規歸屬。
- [x] 8.2 部署 production 後用 claude-in-chrome 開公司頁、read_console_messages 確認 console 零錯誤並抽查違規顯示正確（依 verification-deploy-workflow）。驗證：production console 零錯誤、抽查公司違規顯示正確。
