# 隱私權政策 / Privacy Policy

**Bossy Radar - 104 公司快查**
最後更新：2026-02-15

## 資料收集

本擴充套件**不會收集、傳送或儲存任何個人資料**。

本套件僅在使用者瀏覽 104 人力銀行 (104.com.tw) 的公司或職缺頁面時，從頁面中讀取公司相關資訊（公司名稱、統一編號），用於比對 Bossy Radar 資料庫。

## 本機儲存

本套件使用 Chrome 的 `storage` API 快取以下資料：

- **公司目錄 (company catalog)**：包含上市櫃公司的股票代碼、名稱、統一編號等公開資訊，快取效期 1 天

此資料僅儲存於使用者本機裝置，不會傳送至任何第三方。

## 網路請求

本套件會向以下來源發送請求：

| 目的地 | 用途 |
|--------|------|
| `www.bossy.eraser.tw` | 取得公司目錄及個別公司的違規、薪資等公開資料 |
| `www.104.com.tw` | 在職缺頁面透過 104 公開 API 取得公司統一編號 |

所有請求均透過 HTTPS 加密傳輸。本套件不會將使用者的瀏覽行為、個人資料或任何識別資訊傳送至任何伺服器。

## 第三方服務

本套件使用的資料來自 [Bossy Radar](https://www.bossy.eraser.tw/)，該平台彙整台灣政府公開資料（勞動部、環境部、公開資訊觀測站）。所有資料皆為政府公開資訊。

## 權限用途

- **storage**：在本機快取公司目錄，減少網路請求
- **host_permissions (bossy.eraser.tw)**：從 Bossy Radar 取得公開資料
- **content_scripts (104.com.tw)**：在 104 頁面上顯示資訊卡片

## 資料刪除

解除安裝本擴充套件即會自動清除所有本機快取資料。

## 變更通知

本隱私權政策如有變更，將於本頁面更新。

## 聯絡方式

如有任何隱私相關問題，請至 [GitHub Issues](https://github.com/erase2004/bossy_radar/issues) 提出。

---

# Privacy Policy (English)

**Bossy Radar - 104 Company Quick Check**
Last updated: 2026-02-15

## Data Collection

This extension **does not collect, transmit, or store any personal data**.

The extension only reads company-related information (company name, tax ID) from 104 Job Bank (104.com.tw) pages to match against the Bossy Radar database.

## Local Storage

This extension uses Chrome's `storage` API to cache:

- **Company catalog**: Public information about listed companies (stock codes, names, tax IDs), cached for 1 day

This data is stored locally on the user's device and is never sent to any third party.

## Network Requests

| Destination | Purpose |
|-------------|---------|
| `www.bossy.eraser.tw` | Retrieve company catalog and public violation/salary data |
| `www.104.com.tw` | Retrieve company tax ID via 104's public API on job pages |

All requests use HTTPS encryption. This extension does not transmit browsing behavior, personal data, or any identifying information to any server.

## Permissions

- **storage**: Cache company catalog locally to reduce network requests
- **host_permissions (bossy.eraser.tw)**: Fetch public data from Bossy Radar
- **content_scripts (104.com.tw)**: Display information widget on 104 pages

## Data Deletion

Uninstalling the extension automatically removes all locally cached data.

## Contact

For privacy concerns, please open an issue at [GitHub Issues](https://github.com/erase2004/bossy_radar/issues).
