/**
 * 104 API 攔截器
 * 注入到頁面 main world，攔截含 custNo 的 XHR/fetch 請求
 * 取得統一編號後透過 CustomEvent 傳給 content script
 */

;(() => {
  'use strict'

  const extractCustNo = (url) => {
    const match = url.match(/custno=(\d+)/i)
    return match ? match[1] : null
  }

  const extractTaxId = (custNo) => {
    if (!custNo || custNo.length < 8) return null
    return custNo.substring(0, 8)
  }

  const dispatchTaxId = (taxId, source) => {
    window.dispatchEvent(
      new CustomEvent('bossy-radar-tax-id', {
        detail: { taxId, source },
      })
    )
  }

  const seen = new Set()

  const processUrl = (url, source) => {
    const custNo = extractCustNo(url)
    if (!custNo) return

    const taxId = extractTaxId(custNo)
    if (!taxId || seen.has(taxId)) return

    seen.add(taxId)
    // 存到 DOM data attribute，讓 content script 跨 world 讀取
    document.documentElement.setAttribute('data-bossy-tax-id', taxId)
    dispatchTaxId(taxId, source)
  }

  // Hook fetch
  const originalFetch = window.fetch
  window.fetch = async (...args) => {
    const url = (args[0]?.url || args[0] || '').toString()
    processUrl(url, 'fetch')
    return originalFetch(...args)
  }

  // Hook XMLHttpRequest
  const originalOpen = XMLHttpRequest.prototype.open
  XMLHttpRequest.prototype.open = function (method, url, ...rest) {
    processUrl(url?.toString() || '', 'xhr')
    return originalOpen.call(this, method, url, ...rest)
  }

})()
