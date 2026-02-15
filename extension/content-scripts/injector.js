/**
 * Injector - 將 interceptor.js 注入到頁面的 main world
 *
 * Manifest V3 的 content script 跑在隔離環境，
 * 無法直接 hook 頁面的 fetch/XHR。
 * 這個 script 透過 <script> 標籤將 interceptor 注入到頁面 context。
 */

;(() => {
  'use strict'

  const script = document.createElement('script')
  script.src = chrome.runtime.getURL('content-scripts/interceptor.js')
  script.onload = () => script.remove()
  ;(document.head || document.documentElement).appendChild(script)
})()
