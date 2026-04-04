## Context

Bossy Radar Chrome extension 在 104.com.tw 上透過攔截 API 請求/回應來取得公司統一編號（custNo），再與 catalog 比對顯示公司資訊。目前的 `interceptor.js` 存在三個設計缺陷導致顯示錯誤公司：

1. **掃描範圍過廣**：hook 所有 `fetch`/`XHR`，掃描所有 response body，包括 analytics、tracking、ads 等非 104 API 的回應
2. **首次鎖定機制**：`dispatched = true` 一旦觸發就永久鎖定，即使後續找到更可靠的 custNo 也無法修正
3. **custNo 格式假設錯誤**：104 有兩種 custNo 格式（傳統 `統編+xxx` 和新式 `13000000+xxx`），取前 8 碼的假設對新格式無效

當前架構：
```
injector.js (document_start) → 注入 interceptor.js 到 main world
interceptor.js (main world) → hook fetch/XHR，擷取 custNo，設定 DOM attribute
main.js (document_idle, isolated world) → 讀取 DOM attribute，比對 catalog，渲染 widget
```

## Goals / Non-Goals

**Goals:**

- 消除「顯示錯誤公司」的 bug
- 提高 custNo 擷取的準確度，只從可信來源取得
- 在 tax_id 比對結果與頁面公司名不一致時能自動降級為名稱比對

**Non-Goals:**

- SPA 導航狀態重設（獨立 issue）
- 重構跨 world 通訊機制
- 新增 debug UI 或 logging 面板

## Decisions

### 限制 interceptor 只掃描 104 API response

只處理 hostname 為 `*.104.com.tw` 的 fetch/XHR response body。其他 domain（analytics、tracking、ads CDN）的 response 完全跳過。

**替代方案**：白名單特定 API path（如 `/job/ajax/content/`）— 排除，因為 104 的 API path 可能隨時變動，hostname 篩選更穩定。

### 以優先級取代 dispatched 鎖定

移除 `dispatched` boolean，改用 `confidence` 等級：

| 優先級 | 來源 | 說明 |
|--------|------|------|
| 3 (最高) | URL `custno=` 參數 | 直接且明確 |
| 2 | response body JSON `custNo` 欄位 | 結構化資料 |
| 1 (最低) | HTML 掃描 / regex 泛用比對 | 容易誤判 |

高優先級可覆蓋低優先級。同優先級以第一個為準。

**替代方案**：保留 dispatched 但加上 timeout（如 3 秒後才鎖定）— 排除，因為本質問題是來源可信度而非時序。

### 過濾 104 內部 custNo 格式

104 有些公司使用 `13000000xxxxxxxxx` 格式的內部 ID，前 8 碼 `13000000` 不是有效統編。新增驗證邏輯：

- 若 custNo 前 8 碼全為 `X0000000` 模式（後 7 碼皆 0），判定為無效統編，跳過 tax_id 比對
- 改用統編校驗碼驗算（台灣統編有固定的檢查碼規則），無效者降級為名稱比對

採用校驗碼方式，因為更通用且不依賴特定前綴假設。

### main.js 加入交叉驗證

當 tax_id 比對成功後，將 catalog 中的公司名與 DOM 上取得的公司名進行比較。若完全不相關（非子字串關係），降級為名稱比對。

這是最後一道防線，確保即使 interceptor 抓到的 custNo 碰巧在 catalog 中有對應，也不會顯示明顯錯誤的公司。

## Risks / Trade-offs

- **[Risk] 限制掃描範圍可能漏掉部分 custNo 來源** → 保留 `fetchTaxIdBySlug` 作為 fallback，名稱比對作為最終手段。實測中 104 自身 API 已涵蓋所有需要的 custNo。
- **[Risk] 統編校驗碼可能排除少數特殊格式的有效統編** → 校驗碼演算法是公開標準，只有不合法的才會被排除。若擔心，可加上白名單機制。
- **[Trade-off] 交叉驗證會增加比對延遲** → 僅在 tax_id 比對成功時做一次字串比較，開銷可忽略。
- **[Trade-off] 部分公司可能從 tax_id 比對降級為名稱比對** → 準確度優先。名稱比對在大多數情況下也能正確匹配。
