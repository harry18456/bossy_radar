/**
 * 104 API 攔截器
 * 注入到頁面 main world，攔截含 custNo 的 XHR/fetch 請求及回應
 * 取得統一編號後透過 CustomEvent 傳給 content script
 */

(() => {
  "use strict";

  // ── 台灣統一編號校驗碼驗算 (isValidUBN) ──
  // 權重：1, 2, 1, 2, 1, 2, 4, 1；各位相乘後十位與個位相加，總和須被 10 整除
  // 特例：第 7 碼為 7 時，總和 -1 能被 10 整除也視為有效

  const isValidUBN = (taxId) => {
    if (!taxId || taxId.length !== 8 || !/^\d{8}$/.test(taxId)) return false;
    const weights = [1, 2, 1, 2, 1, 2, 4, 1];
    let sum = 0;
    for (let i = 0; i < 8; i++) {
      const product = parseInt(taxId[i], 10) * weights[i];
      sum += Math.floor(product / 10) + (product % 10);
    }
    if (sum % 10 === 0) return true;
    if (taxId[6] === "7" && (sum - 1) % 10 === 0) return true;
    return false;
  };

  // ── 104 domain 判斷 (is104Domain) ──
  // 僅掃描 *.104.com.tw 的 response body，過濾 analytics/tracking/ads 等外部 domain

  const is104Domain = (url) => {
    if (!url) return false;
    try {
      return new URL(url).hostname.endsWith(".104.com.tw");
    } catch {
      // 相對路徑：依當前頁面 domain 判斷
      return location.hostname.endsWith(".104.com.tw");
    }
  };

  // ── custNo 擷取 ──

  const extractCustNoFromUrl = (url) => {
    const match = url.match(/custno=(\d+)/i);
    return match ? match[1] : null;
  };

  const extractTaxId = (custNo) => {
    if (!custNo || custNo.length < 8) return null;
    const taxId = custNo.substring(0, 8);
    return isValidUBN(taxId) ? taxId : null;
  };

  // ── Priority-based dispatch (取代 dispatched flag) ──
  // Priority 3: URL 參數 custno=（最可靠，明確指向當前頁面公司）
  // Priority 2: 104 API response body 的 JSON custNo 欄位（結構化資料）
  // Priority 1: HTML 掃描 / regex 泛用比對（最低可信度）
  // 高優先級可覆蓋低優先級；同優先級以第一個為準

  const PRIORITY = { URL_PARAM: 3, JSON_FIELD: 2, HTML_SCAN: 1 };
  let currentPriority = 0;

  const dispatchTaxId = (taxId, source) => {
    window.dispatchEvent(
      new CustomEvent("bossy-radar-tax-id", {
        detail: { taxId, source },
      }),
    );
  };

  const handleDiscoveredCustNo = (custNo, source, priority) => {
    if (priority <= currentPriority) return; // 同優先級以第一個為準；低優先級忽略
    const taxId = extractTaxId(custNo);
    if (!taxId) return; // 未通過 UBN 校驗，跳過
    currentPriority = priority;
    document.documentElement.setAttribute("data-bossy-tax-id", taxId);
    dispatchTaxId(taxId, source);
  };

  // ── Response body 掃描（只處理 104 API） ──

  const findCustNoInJson = (obj, depth = 0) => {
    if (!obj || typeof obj !== "object" || depth > 5) return null;
    for (const [key, value] of Object.entries(obj)) {
      if (/^(?:ads-)?cust[Nn]o$/i.test(key) && value) {
        const str = String(value);
        if (str.length >= 8) return str;
      }
      if (typeof value === "object" && !Array.isArray(value)) {
        const found = findCustNoInJson(value, depth + 1);
        if (found) return found;
      }
    }
    return null;
  };

  const processResponseText = (text, source) => {
    try {
      if (!text) return;

      // 先嘗試 JSON 結構化解析（priority 2）
      try {
        const data = JSON.parse(text);
        const custNo = findCustNoInJson(data);
        if (custNo) {
          handleDiscoveredCustNo(custNo, source, PRIORITY.JSON_FIELD);
          return;
        }
      } catch {
        // 非 JSON，fallback 到 regex（priority 2 — 仍在 104 domain 範圍內）
      }

      const patterns = [
        /(?:ads-)?cust[Nn]o["']?\s*[:=]\s*["']?(\d{8,})["']?/i,
        /["']?company["']?\s*:\s*\{\s*["']?name["']?\s*:\s*["']?(\d{8,})["']?/i,
      ];

      for (const pattern of patterns) {
        const match = text.match(pattern);
        if (match) {
          handleDiscoveredCustNo(match[1], source, PRIORITY.JSON_FIELD);
          break;
        }
      }
    } catch {}
  };

  const scanInlineHtml = () => {
    try {
      const html = document.documentElement.innerHTML;
      // HTML 掃描為最低優先級
      const patterns = [
        /(?:ads-)?cust[Nn]o["']?\s*[:=]\s*["']?(\d{8,})["']?/i,
        /["']?company["']?\s*:\s*\{\s*["']?name["']?\s*:\s*["']?(\d{8,})["']?/i,
      ];
      for (const pattern of patterns) {
        const match = html.match(pattern);
        if (match) {
          handleDiscoveredCustNo(match[1], "html", PRIORITY.HTML_SCAN);
          break;
        }
      }
    } catch {}
  };

  // ── Hook fetch ──

  const originalFetch = window.fetch;
  window.fetch = async (...args) => {
    const url = (args[0]?.url || args[0] || "").toString();

    // URL 參數：最高優先級，不限 domain
    const urlCustNo = extractCustNoFromUrl(url);
    if (urlCustNo) handleDiscoveredCustNo(urlCustNo, "fetch_req", PRIORITY.URL_PARAM);

    try {
      const response = await originalFetch(...args);
      // 只掃描 104 domain 的 response body
      if (is104Domain(url)) {
        const cloned = response.clone();
        cloned
          .text()
          .then((text) => processResponseText(text, "fetch_res"))
          .catch(() => {});
      }
      return response;
    } catch (e) {
      throw e;
    }
  };

  // ── Hook XMLHttpRequest ──

  const originalOpen = XMLHttpRequest.prototype.open;
  const originalSend = XMLHttpRequest.prototype.send;

  XMLHttpRequest.prototype.open = function (method, url, ...rest) {
    this._bossyUrl = url?.toString() || "";
    const urlCustNo = extractCustNoFromUrl(this._bossyUrl);
    if (urlCustNo) handleDiscoveredCustNo(urlCustNo, "xhr_req", PRIORITY.URL_PARAM);
    return originalOpen.call(this, method, url, ...rest);
  };

  XMLHttpRequest.prototype.send = function (...args) {
    this.addEventListener("load", function () {
      if (is104Domain(this._bossyUrl || "")) {
        processResponseText(this.responseText, "xhr_res");
      }
    });
    return originalSend.apply(this, args);
  };

  // 頁面載入時掃描一次初始 HTML
  scanInlineHtml();
  window.addEventListener("DOMContentLoaded", scanInlineHtml);
})();
