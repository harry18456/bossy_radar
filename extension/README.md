# Bossy Radar - 104 公司快查

瀏覽器擴充套件 (Chrome / Edge)，在瀏覽 104 人力銀行時自動顯示公司的勞動違規、環境違規與薪資資訊。

## 功能

- 瀏覽 104 公司頁面或職缺頁面時，自動彈出資訊卡片
- 顯示勞動違規次數、環境違規次數、累計罰款金額
- 顯示非主管員工中位數 / 平均年薪
- 一鍵連結至 [Bossy Radar](https://www.bossy.eraser.tw/) 查看完整報告
- 支援 www.104.com.tw 及 go.104.com.tw

## 比對方式

套件會依照以下優先順序比對公司：

1. **統一編號** — 攔截 104 API 請求中的 `custNo` 參數，取前 8 碼作為統編比對
2. **公司全名** — 從頁面 DOM 取得公司名稱，與資料庫精確比對
3. **名稱分段** — 處理 104 常見的「品牌名\_公司全名」格式

## 安裝

### 從商店安裝

- **Chrome**: [Chrome Web Store](https://chromewebstore.google.com/detail/bossy-radar-104-%E5%85%AC%E5%8F%B8%E5%BF%AB%E6%9F%A5/ofkcclhbelkcnaghcdigdljkeonebigj)
- **Edge**: [Microsoft Edge Add-ons](https://microsoftedge.microsoft.com/addons/detail/bossy-radar-104-%E5%85%AC%E5%8F%B8%E5%BF%AB%E6%9F%A5/hahgkkffopmbccnocmkhncpopnmphoik)

### 開發者模式

1. Clone 此專案
2. 開啟瀏覽器擴充功能頁面
   - Chrome: `chrome://extensions/`
   - Edge: `edge://extensions/`
3. 開啟「開發人員模式」
4. 點選「載入未封裝項目」，選擇 `extension/` 資料夾
5. 前往 [104 人力銀行](https://www.104.com.tw/) 瀏覽任意公司頁面

## 架構

```
extension/
├── manifest.json                # Manifest V3 設定
├── background/
│   └── service-worker.js        # 跨域資料請求、Catalog 快取
├── content-scripts/
│   ├── injector.js              # 將 interceptor 注入 main world
│   ├── interceptor.js           # 攔截 104 fetch/XHR 取得統編
│   ├── main.js                  # 比對邏輯與 Widget 渲染
│   └── widget.css               # Widget 樣式
└── icons/                       # 擴充套件圖示
```

## 權限說明

| 權限                                 | 用途                                  |
| ------------------------------------ | ------------------------------------- |
| `storage`                            | 快取公司目錄資料，避免重複下載        |
| `host_permissions` (bossy.eraser.tw) | 從 Bossy Radar 取得公司違規與薪資資料 |
| `content_scripts` (104.com.tw)       | 在 104 頁面上顯示資訊卡片             |

## 隱私權

詳見 [隱私權政策](./PRIVACY_POLICY.md)。

## 授權

[AGPL-3.0](../LICENSE)
