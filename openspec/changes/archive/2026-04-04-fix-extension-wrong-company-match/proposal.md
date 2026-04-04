## Why

Extension 使用者回報在 104 job page 上顯示了錯誤的公司資訊（實際瀏覽「新技術供應鏈與物流」卻顯示「元富證券」）。經調查確認是 `interceptor.js` 的 custNo 擷取邏輯有缺陷：掃描範圍過廣（所有 fetch/XHR response body）、首次命中即鎖定（`dispatched` flag）、且 104 的 `13000000` 前綴內部 custNo 格式被錯誤當作統一編號。

## What Changes

- **重構 interceptor 的 custNo 擷取邏輯**：僅掃描 `*.104.com.tw` 的 API response，不再掃描所有 fetch/XHR
- **移除 `dispatched` 一次性鎖定機制**：改用優先級制度（URL 參數 > response body JSON 欄位 > HTML 掃描），允許更高可信度的來源覆蓋低可信度的結果
- **過濾無效的 custNo 前綴**：識別並跳過 104 內部格式的 `13000000` 前綴 custNo，避免錯誤比對
- **main.js 加入 tax_id 與頁面公司名交叉驗證**：當 tax_id 比對到的公司名與 DOM 上的公司名不一致時，降級為名稱比對

## Non-Goals (optional)

- 不處理 SPA 導航狀態重設（屬於獨立改進，另案處理）
- 不重構 widget 渲染邏輯
- 不新增 debug/logging UI

## Capabilities

### New Capabilities

- `extension-company-matching`: 涵蓋 extension 的公司識別與比對邏輯，包括 custNo 擷取規則、比對優先級、以及交叉驗證機制

### Modified Capabilities

（無既有 spec）

## Impact

- 受影響程式碼：
  - `extension/content-scripts/interceptor.js` — custNo 擷取邏輯重構
  - `extension/content-scripts/main.js` — 比對邏輯加入交叉驗證
- 受影響行為：custNo 偵測的時序與優先級改變，部分過去能透過 tax_id 比對的公司可能改為名稱比對（但準確度更高）
- 無 API 或依賴變更
