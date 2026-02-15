/**
 * Background Service Worker
 * 負責 fetch Bossy Radar 資料（不受 CORS 限制）
 */

const BOSSY_RADAR_URL = 'https://www.bossy.eraser.tw'
const CATALOG_CACHE_KEY = 'bossy_radar_catalog_v2' // v2: 包含 tax_id
const CATALOG_TTL = 24 * 60 * 60 * 1000 // 1 day

const fetchCatalog = async () => {
  const cached = await chrome.storage.local.get([
    CATALOG_CACHE_KEY,
    `${CATALOG_CACHE_KEY}_ts`,
  ])

  const cachedAt = cached[`${CATALOG_CACHE_KEY}_ts`] || 0
  if (cached[CATALOG_CACHE_KEY] && Date.now() - cachedAt < CATALOG_TTL) {
    return cached[CATALOG_CACHE_KEY]
  }

  const res = await fetch(`${BOSSY_RADAR_URL}/data/company-catalog.json`)
  if (!res.ok) throw new Error(`Catalog fetch failed: ${res.status}`)

  const catalog = await res.json()
  await chrome.storage.local.set({
    [CATALOG_CACHE_KEY]: catalog,
    [`${CATALOG_CACHE_KEY}_ts`]: Date.now(),
  })

  return catalog
}

const fetchCompanyData = async (code) => {
  const res = await fetch(
    `${BOSSY_RADAR_URL}/data/companies/${code}.json`
  )
  if (!res.ok) return null
  return res.json()
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.type === 'GET_CATALOG') {
    fetchCatalog()
      .then((catalog) => sendResponse({ ok: true, data: catalog }))
      .catch((err) => sendResponse({ ok: false, error: err.message }))
    return true // keep channel open for async
  }

  if (message.type === 'GET_COMPANY') {
    fetchCompanyData(message.code)
      .then((data) => sendResponse({ ok: true, data }))
      .catch((err) => sendResponse({ ok: false, error: err.message }))
    return true
  }
})
