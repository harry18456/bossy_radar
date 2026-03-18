/**
 * 104 API 攔截器
 * 注入到頁面 main world，攔截含 custNo 的 XHR/fetch 請求及回應
 * 取得統一編號後透過 CustomEvent 傳給 content script
 */

(() => {
  "use strict";

  const extractCustNo = (url) => {
    const match = url.match(/custno=(\d+)/i);
    return match ? match[1] : null;
  };

  const extractTaxId = (custNo) => {
    if (!custNo || custNo.length < 8) return null;
    return custNo.substring(0, 8);
  };

  const dispatchTaxId = (taxId, source) => {
    window.dispatchEvent(
      new CustomEvent("bossy-radar-tax-id", {
        detail: { taxId, source },
      }),
    );
  };

  const seen = new Set();
  // 只 dispatch 第一個找到的 custno，避免相似公司列表等 API 回應覆蓋當前頁面公司
  let dispatched = false;

  const processUrl = (url, source) => {
    const custNo = extractCustNo(url);
    if (!custNo) return;
    handleDiscoveredCustNo(custNo, source);
  };

  const handleDiscoveredCustNo = (custNo, source) => {
    if (dispatched) return;
    const taxId = extractTaxId(custNo);
    if (!taxId || seen.has(taxId)) return;

    seen.add(taxId);
    dispatched = true;
    // 存到 DOM data attribute，讓 content script 跨 world 讀取
    document.documentElement.setAttribute("data-bossy-tax-id", taxId);
    dispatchTaxId(taxId, source);
  };

  const processResponseText = (text, source) => {
    try {
      if (!text) return;
      
      const patterns = [
        /(?:ads-)?cust[Nn]o["']?\s*[:=]\s*["']?(\d{8,})["']?/i,
        /["']?company["']?\s*:\s*\{\s*["']?name["']?\s*:\s*["']?(\d{8,})["']?/i
      ];
      
      for (const pattern of patterns) {
        const match = text.match(pattern);
        if (match) {
          handleDiscoveredCustNo(match[1], source);
          break;
        }
      }
    } catch {}
  };

  const scanInlineHtml = () => {
    try {
      const html = document.documentElement.innerHTML;
      processResponseText(html, "html");
    } catch {}
  };

  // Hook fetch
  const originalFetch = window.fetch;
  window.fetch = async (...args) => {
    const url = (args[0]?.url || args[0] || "").toString();
    processUrl(url, "fetch_req");

    try {
      const response = await originalFetch(...args);
      const cloned = response.clone();
      cloned
        .text()
        .then((text) => processResponseText(text, "fetch_res"))
        .catch(() => {});
      return response;
    } catch (e) {
      throw e;
    }
  };

  // Hook XMLHttpRequest
  const originalOpen = XMLHttpRequest.prototype.open;
  const originalSend = XMLHttpRequest.prototype.send;
  XMLHttpRequest.prototype.open = function (method, url, ...rest) {
    this._bossyUrl = url?.toString() || "";
    processUrl(this._bossyUrl, "xhr_req");
    return originalOpen.call(this, method, url, ...rest);
  };
  XMLHttpRequest.prototype.send = function (...args) {
    this.addEventListener("load", function () {
      processResponseText(this.responseText, "xhr_res");
    });
    return originalSend.apply(this, args);
  };

  // 頁面載入時掃描一次初始 HTML
  scanInlineHtml();
  window.addEventListener("DOMContentLoaded", scanInlineHtml);
})();
