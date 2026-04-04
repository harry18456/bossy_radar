## 1. interceptor.js — 限制掃描範圍與優先級重構

- [x] 1.1 新增 `is104Domain(url)` 輔助函式，確保 interceptor SHALL only scan 104 API responses（對應設計決策：限制 interceptor 只掃描 104 API response）
- [x] 1.2 移除 `dispatched` flag，以優先級取代 dispatched 鎖定，實作 custNo extraction SHALL use confidence-based priority 機制（priority 3: URL 參數 > priority 2: JSON 欄位 > priority 1: HTML 掃描）
- [x] 1.3 新增台灣統一編號校驗碼驗證函式 `isValidUBN(taxId)`，過濾 104 內部 custNo 格式，invalid tax ID prefixes SHALL be rejected
- [x] 1.4 將 `extractTaxId` 整合校驗碼驗證，無效統編不 dispatch

## 2. main.js — 交叉驗證邏輯

- [x] 2.1 main.js 加入交叉驗證：在 `handleMatch` 中加入 tax ID match SHALL be cross-validated against page company name 的邏輯，比較 catalog 公司名與 DOM 公司名
- [x] 2.2 當交叉驗證失敗時，清除 tax_id 比對結果並 fallback 至名稱比對

## 3. 測試與驗證

- [x] 3.1 手動測試：開啟已知有 `13000000` 前綴的公司頁面（如稜研科技），確認不會誤 dispatch 無效統編
- [x] 3.2 手動測試：開啟已知正確統編的公司頁面（如台灣三住 `23225712`），確認正常比對
- [x] 3.3 手動測試：同時開啟多個分頁，確認不會出現顯示錯誤公司的情況
- [x] 3.4 手動測試：go.104.com.tw 頁面仍可正常以名稱比對運作
