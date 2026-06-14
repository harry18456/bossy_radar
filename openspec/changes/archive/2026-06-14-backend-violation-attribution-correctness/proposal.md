## Why

平台指名公布上市櫃公司的勞動與環境違規。現行公司歸屬比對有兩個 correctness 缺陷，會把 A 公司（或某個自然人）的違規掛到 B 上市公司名下，構成對 B 的不實陳述（妨害名譽／商譽侵權，民法第 184、195 條）。網站免責聲明屬對「使用者」的契約性責任限制，無法免除對「被誤掛公司」這一第三方的侵權責任，因此必須從比對邏輯根本消除誤掛，而非以但書規避。

- 分公司前綴比對回傳第一個前綴命中，候選清單以無序 DB row 建立，跨 run／跨 DB 重建可能改變歸屬（非確定性）。
- 第四層董事長比對拿違規欄位的純人名直接比對董事長姓名，唯一即自動連到該上市公司、毫無佐證，導致自然人違規被誤掛上市公司。
- 比對邏輯有多份內聯複製且帶同樣 bug：違規同步服務與 MOPS 爬蟲各重寫一份，僅環境裁罰服務使用正典 CompanyMatcher。

真實 DB dry-run 的實證數字見設計文件。

## What Changes

- 分公司前綴比對改為確定性最長前綴加保守拒絕：取最長前綴候選；公司全名後接括號負責人、或公司全名後接廠區後綴，視為同一公司；剩餘部分若像另一家獨立法人（以股份有限公司／有限公司等法人標識起始）則拒絕；比對前先剝去法人後綴以解決公司主檔名稱缺後綴的特例；多個不同公司代號並列最長前綴時拒絕、不猜測。確定性是此演算法的自然結果，不再依賴 DB row 順序。
- 停用第四層董事長純人名自動連結：無公司全名背書的純人名不再自動連到上市公司，連不上即歸 archive（漏接無害、誤掛有害）。
- 三來源共用單一 CompanyMatcher：違規同步服務與 MOPS 爬蟲移除內聯比對複製、改委派 CompanyMatcher；CompanyMatcher 新增公司代號（原始 raw_company_code）精確比對層供 MOPS 使用。
- change 完成後全量重抓重建資料：以新邏輯重新同步所有來源，取代既有資料回溯腳本（重抓即重建正確歸屬）。
- 前端資料比對邏輯說明頁據實更新：負責人姓名不再用於自動連結，對外描述對齊實作。

## Non-Goals (optional)

詳見設計文件的 Goals / Non-Goals，重點包含：不做正規化／模糊比對救回 archive 漏接（實證顯示僅 0.1% 且會引入新誤掛）、不補抽勞動違規統編（降級為查證）、不更動擴充套件層的公司比對、不納入公開 API 前的安全強化。

## Capabilities

### New Capabilities

- `backend-company-attribution`: 後端 ETL 將勞動／環境／MOPS 違規與裁罰資料歸屬到上市櫃公司的比對行為——精確比對（統一編號／公司代號／公司全名）、確定性分公司前綴比對、以及無佐證不連結的保守歸屬原則，並由三來源共用單一實作。

### Modified Capabilities

(none)

## Impact

- Affected specs: backend-company-attribution (new)
- Affected code (modified):
  - backend/app/services/company_matcher.py
  - backend/app/services/violation_service.py
  - backend/app/services/mops_scraper.py
  - backend/scripts/analyze_attribution_impact.py
  - frontend/app/pages/data-sources.vue
  - frontend/DATA.md
- Affected code (new):
  - backend/tests/test_company_attribution.py
- Affected code (no source change, regression-tested only):
  - backend/app/services/environmental_service.py
- Data: change 完成後全量重抓重建 bossy_radar.db 與 archive.db；動資料前先備份。
