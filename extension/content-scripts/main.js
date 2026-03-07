/**
 * Bossy Radar Content Script
 * 在 104.com.tw 頁面上顯示公司勞動違規、薪資等快速資訊
 *
 * 比對策略（優先順序）：
 * 1. 統一編號 (tax_id) — 從 104 API 的 custNo 參數取得
 * 2. 公司全名 — 從 DOM h1 取得
 *
 * 所有 fetch 透過 background service worker 執行，避免 CORS
 */

;(() => {
  'use strict'

  const BOSSY_RADAR_URL = 'https://www.bossy.eraser.tw'

  // ── State ──

  let taxIdIndex = null
  let nameIndex = null
  let currentMatch = null
  let matchMethod = null // 'tax_id' | 'name' | 'name_split'
  let detectedTaxId = null
  let widgetVisible = false

  // ── Background messaging ──

  const sendMessage = (message) =>
    new Promise((resolve) => {
      chrome.runtime.sendMessage(message, resolve)
    })

  // ── Catalog ──

  const loadCatalog = async () => {
    try {
      const res = await sendMessage({ type: 'GET_CATALOG' })
      if (!res?.ok) throw new Error(res?.error || 'Unknown error')

      const catalog = res.data
      taxIdIndex = new Map()
      nameIndex = new Map()

      for (const item of catalog) {
        if (item.tax_id) taxIdIndex.set(item.tax_id, item)
        if (item.name) nameIndex.set(item.name, item)
      }

      return true
    } catch (err) {
      console.error('[Bossy Radar] Failed to load catalog:', err)
      return false
    }
  }

  // ── Matching ──

  const matchByTaxId = (taxId) =>
    taxIdIndex?.get(taxId) || null

  const matchByName = (name) => {
    if (!nameIndex || !name) return null
    return nameIndex.get(name.trim()) || null
  }

  const RESERVED_PATHS = ['main', 'search', 'salary', 'topic', 'list']

  // 從 DOM 找到 104 公司頁 slug（如 7m9vnu8）
  const getCompanySlugFromDOM = () => {
    const links = document.querySelectorAll('a[href*="/company/"]')
    for (const link of links) {
      const href = link.getAttribute('href') || ''
      const slugMatch = href.match(/\/company\/([a-zA-Z0-9]+)/)
      if (!slugMatch) continue
      if (RESERVED_PATHS.includes(slugMatch[1])) continue
      if (href.includes('reviews.104.com.tw')) continue
      return slugMatch[1]
    }
    return null
  }

  const getCompanyNameFromDOM = () => {
    const jobPage = isJobPage()
    const goSite = isGoSite()

    // go.104: 沒有 h1，從 og:title 解析
    if (goSite) {
      const ogTitle = document.querySelector('meta[property="og:title"]')?.content
      if (!ogTitle) return null

      if (jobPage) {
        // go.104 job: "職缺名 | 公司名 | 外國人才工作機會｜104 外籍求職專區"
        const parts = ogTitle.split('|').map((s) => s.trim())
        // 公司名通常在第二段（排除最後的 "外國人才..." 和 "104 外籍..."）
        if (parts.length >= 3) return parts[1]
      } else {
        // go.104 company: "公司名 ｜ 友善企業職缺｜104 外籍求職專區"
        const match = ogTitle.match(/^(.+?)\s*[｜|]/)
        if (match) return match[1].trim()
      }

      // fallback: 找 custno 連結的文字
      const links = document.querySelectorAll('a[href*="custno="]')
      for (const link of links) {
        const text = link.textContent.trim()
        if (text && text.length >= 2 && text.length <= 50 && !['English', 'More', 'All Jobs'].includes(text)) {
          return text
        }
      }

      return null
    }

    // www.104 job 頁面
    if (jobPage) {
      // 方法 1: 找直接連到 /company/{slug} 的連結
      const links = document.querySelectorAll('a[href*="/company/"]')
      for (const link of links) {
        const href = link.getAttribute('href') || ''
        const text = link.textContent.trim()
        if (!text || text.length < 2 || text.length > 50) continue
        const slugMatch = href.match(/\/company\/([a-zA-Z0-9]+)/)
        if (!slugMatch) continue
        if (RESERVED_PATHS.includes(slugMatch[1])) continue
        if (href.includes('reviews.104.com.tw')) continue
        return text
      }

      // 方法 2: 從 og:title 解析 「職缺名｜公司名－104 人力銀行」
      const ogTitle = document.querySelector('meta[property="og:title"]')?.content
      if (ogTitle) {
        const match = ogTitle.match(/[｜|](.+?)[－\-–—]104/)
        if (match) return match[1].trim()
      }

      return null
    }

    // www.104 company 頁面：公司名在 h1
    return document.querySelector('h1')?.textContent?.trim() || null
  }

  // 透過 104 公司 slug 去要統編
  const fetchTaxIdBySlug = async (slug) => {
    const commonHeaders = {
      'Referer': `https://www.104.com.tw/company/${slug}`,
      'X-Requested-With': 'XMLHttpRequest',
    }

    // 在 JSON response 中遞迴搜尋含 custNo 的欄位
    const findCustNo = (obj, depth = 0) => {
      if (!obj || typeof obj !== 'object' || depth > 5) return null
      for (const [key, value] of Object.entries(obj)) {
        // custNo 值可能是 string 或 number
        if (/custno/i.test(key) && value) {
          const str = String(value)
          if (str.length >= 8) return str.substring(0, 8)
        }
        if (typeof value === 'object' && !Array.isArray(value)) {
          const found = findCustNo(value, depth + 1)
          if (found) return found
        }
      }
      return null
    }

    // 嘗試多個 API 端點
    const endpoints = [
      `/company/ajax/content/${slug}`,
      `/company/ajax/summary/${slug}`,
    ]

    for (const endpoint of endpoints) {
      try {
        const res = await fetch(`https://www.104.com.tw${endpoint}`, {
          headers: commonHeaders,
        })
        if (!res.ok) continue

        const text = await res.text()

        // 先嘗試 JSON 解析
        try {
          const data = JSON.parse(text)
          const custNo = findCustNo(data)
          if (custNo) return custNo
        } catch {
          // 非 JSON，用 regex 找
        }

        // 從原始文字中找 custNo 模式
        const patterns = [
          /custNo[=:"'\s]+(\d{8,})/i,
          /cust_no[=:"'\s]+(\d{8,})/i,
          /invoiceNo[=:"'\s]+(\d{8})/i,
        ]
        for (const pattern of patterns) {
          const match = text.match(pattern)
          if (match) return match[1].substring(0, 8)
        }
      } catch {
        // ignore
      }
    }

    // 最後手段：fetch 公司頁 HTML
    try {
      const htmlRes = await fetch(`https://www.104.com.tw/company/${slug}`)
      const html = await htmlRes.text()
      const custMatch = html.match(/custNo[=:"'\s]+(\d{8,})/i)
      if (custMatch) return custMatch[1].substring(0, 8)
    } catch {
      // ignore
    }

    return null
  }

  // ── Data Loading ──

  const loadCompanyData = async (code) => {
    try {
      const res = await sendMessage({ type: 'GET_COMPANY', code })
      return res?.ok ? res.data : null
    } catch {
      return null
    }
  }

  // ── Widget ──

  const formatCurrency = (amount) => {
    if (amount >= 100000000) return `${(amount / 100000000).toFixed(1)} 億`
    if (amount >= 10000) return `${(amount / 10000).toFixed(0)} 萬`
    return amount.toLocaleString()
  }

  const createWidget = () => {
    document.getElementById('bossy-radar-widget')?.remove()
    document.getElementById('bossy-radar-toggle')?.remove()

    const widget = document.createElement('div')
    widget.id = 'bossy-radar-widget'
    widget.innerHTML = `
      <div class="br-card">
        <div class="br-header">
          <div class="br-header-title">
            <span class="br-logo">BR</span> Bossy Radar
          </div>
          <button class="br-close" id="bossy-radar-close">&times;</button>
        </div>
        <div id="bossy-radar-body">
          <div class="br-loading">載入中...</div>
        </div>
      </div>
    `

    document.body.appendChild(widget)
    widgetVisible = true

    document
      .getElementById('bossy-radar-close')
      .addEventListener('click', () => {
        widget.style.display = 'none'
        widgetVisible = false
        showToggleButton()
      })
  }

  const showToggleButton = () => {
    document.getElementById('bossy-radar-toggle')?.remove()

    const btn = document.createElement('button')
    btn.id = 'bossy-radar-toggle'
    btn.textContent = 'BR'
    btn.title = 'Bossy Radar'
    btn.addEventListener('click', () => {
      const widget = document.getElementById('bossy-radar-widget')
      if (widget) {
        widget.style.display = 'block'
        widgetVisible = true
        btn.remove()
      }
    })

    document.body.appendChild(btn)
  }

  const renderCompanyData = (catalogItem, companyData) => {
    const body = document.getElementById('bossy-radar-body')
    if (!body) return

    const company = companyData?.company || {}
    const violations = companyData?.violations || []
    const envViolations = companyData?.environmental_violations || []
    const salaries = companyData?.non_manager_salaries || []

    const totalViolations = violations.length
    const totalEnvViolations = envViolations.length
    const totalFines =
      violations.reduce((sum, v) => sum + (v.fine_amount || 0), 0) +
      envViolations.reduce((sum, v) => sum + (v.fine_amount || 0), 0)

    const latestSalary = salaries.length > 0
      ? salaries.reduce((a, b) => (a.year > b.year ? a : b))
      : null

    // 薪資單位：千元 (1837 = 183.7 萬)，年份為民國年
    const salaryYear = latestSalary ? latestSalary.year + 1911 : null
    const salaryYearLabel = salaryYear ? ` (${salaryYear})` : ''

    const medianSalaryText = latestSalary?.median_salary
      ? `${(latestSalary.median_salary / 10).toFixed(1)} 萬`
      : '-'

    const avgSalaryText = latestSalary?.avg_salary
      ? `${(latestSalary.avg_salary / 10).toFixed(1)} 萬`
      : '-'

    const marketLabel =
      catalogItem.market_type === 'Listed' ? '上市' :
      catalogItem.market_type === 'OTC' ? '上櫃' :
      catalogItem.market_type === 'Emerging' ? '興櫃' :
      catalogItem.market_type === 'Public' ? '公開發行' :
      catalogItem.market_type

    body.innerHTML = `
      <div class="br-company">
        <div class="br-company-name">${catalogItem.name}</div>
        <div class="br-company-meta">
          ${catalogItem.code} | ${marketLabel}${company.tax_id ? ` | 統編 ${company.tax_id}` : ''}
        </div>
        <div class="br-match-method">
          ${matchMethod === 'tax_id' ? '統一編號比對' : matchMethod === 'name' ? '名稱比對' : '名稱模糊比對'}
        </div>
      </div>
      <div class="br-stats">
        <div class="br-stat ${totalViolations > 0 ? 'br-stat--danger' : 'br-stat--success'}">
          <div class="br-stat-value">${totalViolations}</div>
          <div class="br-stat-label">勞動違規</div>
        </div>
        <div class="br-stat ${totalEnvViolations > 0 ? 'br-stat--warning' : 'br-stat--success'}">
          <div class="br-stat-value">${totalEnvViolations}</div>
          <div class="br-stat-label">環境違規</div>
        </div>
        <div class="br-stat br-stat--info">
          <div class="br-stat-value">${medianSalaryText}</div>
          <div class="br-stat-label">非主管中位數年薪${salaryYearLabel}</div>
        </div>
        <div class="br-stat br-stat--info">
          <div class="br-stat-value">${avgSalaryText}</div>
          <div class="br-stat-label">非主管平均年薪${salaryYearLabel}</div>
        </div>
      </div>
      ${
        totalFines > 0
          ? `<div class="br-stat" style="border-bottom:1px solid #f0f0f0">
               <div class="br-stat-value" style="color:#e74c3c;font-size:16px">
                 累計罰款 ${formatCurrency(totalFines)}
               </div>
             </div>`
          : ''
      }
      <div class="br-footer">
        <a class="br-link"
           href="${BOSSY_RADAR_URL}/companies/${catalogItem.code}"
           target="_blank"
           rel="noopener noreferrer">
          查看完整報告
        </a>
      </div>
    `
  }

  const renderNotFound = (name, taxId) => {
    const body = document.getElementById('bossy-radar-body')
    if (!body) return

    body.innerHTML = `
      <div class="br-not-found">
        <div style="font-weight:600;font-size:14px;color:#333;margin-bottom:8px">
          ${name || '未知公司'}
        </div>
        ${taxId ? `<div style="margin-bottom:8px;font-size:13px;color:#555">統一編號：${taxId}</div>` : ''}
        <div style="color:#aaa;font-size:12px">
          此公司不在 Bossy Radar 資料庫中
        </div>
      </div>
    `
  }

  // ── Main Flow ──

  const handleMatch = async (catalogItem) => {
    if (currentMatch?.code === catalogItem.code) return
    currentMatch = catalogItem

    if (!document.getElementById('bossy-radar-widget')) createWidget()
    const data = await loadCompanyData(catalogItem.code)
    renderCompanyData(catalogItem, data)
  }

  const tryMatchFromDOM = () => {
    const rawName = getCompanyNameFromDOM()
    if (!rawName) return false

    // 直接比對
    const directMatch = matchByName(rawName)
    if (directMatch) {
      matchMethod = 'name'
      handleMatch(directMatch)
      return true
    }

    // 104 常見格式：「品牌名_公司全名」，嘗試用底線後的部分比對
    const parts = rawName.split('_')
    for (const part of parts) {
      const trimmed = part.trim()
      if (!trimmed) continue
      const match = matchByName(trimmed)
      if (match) {
        matchMethod = 'name_split'
        handleMatch(match)
        return true
      }
    }

    return false
  }

  const isGoSite = () => location.hostname === 'go.104.com.tw'

  const isCompanyOrJobPage = () => {
    const path = location.pathname
    if (path.includes('/search') || path.includes('/list')) return false

    if (isGoSite()) {
      return path.includes('/expats/company/') || path.includes('/expats/job/')
    }

    if (location.hostname !== 'www.104.com.tw') return false
    return path.startsWith('/company/') || path.startsWith('/job/')
  }

  const isJobPage = () => {
    if (isGoSite()) return location.pathname.includes('/expats/job/')
    return location.pathname.startsWith('/job/')
  }

  const init = async () => {
    if (!isCompanyOrJobPage()) return

    // go.104: 只能用名稱比對（custno 是加密的）

    createWidget() // 立刻顯示 loading

    const ok = await loadCatalog()
    if (!ok) {
      renderNotFound('載入失敗', null)
      return
    }

    // 讀取 interceptor 已偵測到的 taxId（透過 DOM attribute 跨 world）
    const readTaxIdFromDOM = () =>
      document.documentElement.getAttribute('data-bossy-tax-id') || null

    const tryMatchByTaxId = (taxId) => {
      if (!taxId) return false
      detectedTaxId = taxId
      const match = matchByTaxId(taxId)
      if (match) {
        matchMethod = 'tax_id'
        handleMatch(match)
        return true
      }
      return false
    }

    // 先檢查 interceptor 是否已抓到（在 catalog 載入期間發生的）
    tryMatchByTaxId(readTaxIdFromDOM())

    // 監聽後續的 tax_id 事件
    window.addEventListener('bossy-radar-tax-id', (event) => {
      tryMatchByTaxId(event.detail.taxId)
    })

    // 持續觀察 DOM attribute 變化（跨 world 備用）
    const observer = new MutationObserver(() => {
      const taxId = readTaxIdFromDOM()
      if (taxId && taxId !== detectedTaxId) {
        tryMatchByTaxId(taxId)
      }
    })
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['data-bossy-tax-id'],
    })

    // 用 MutationObserver 偵測 SPA 渲染完成，立刻比對
    const jobPage = isJobPage()
    let trying = false

    const tryMatch = async () => {
      if (currentMatch || trying) return
      trying = true

      try {
        // 先嘗試直接從頁面 HTML 獲取 (不需網路請求)
        const html = document.documentElement.innerHTML
        const patterns = [
          /(?:ads-)?cust[Nn]o["']?\s*[:=]\s*["']?(\d{8,})["']?/i,
          /["']?company["']?\s*:\s*\{\s*["']?name["']?\s*:\s*["']?(\d{8,})["']?/i
        ]
        
        for (const pattern of patterns) {
          const match = html.match(pattern)
          if (match) {
             const taxId = match[1].substring(0, 8)
             if (tryMatchByTaxId(taxId)) return
             break
          }
        }

        if (jobPage) {
          // Job 頁面：再試 slug → 統編，再 fallback 名稱
          const slug = getCompanySlugFromDOM()
          if (slug) {
            const taxId = await fetchTaxIdBySlug(slug)
            if (taxId) {
              if (tryMatchByTaxId(taxId)) return
            }
          }
        }

        // Company 頁面 或 Job 頁面統編失敗 → 名稱比對
        tryMatchFromDOM()
      } finally {
        trying = false
      }
    }

    // 立刻試一次（可能 DOM 已經 ready）
    await tryMatch()

    // 還沒命中就觀察 DOM 變化
    if (!currentMatch) {
      let contentSeenAt = 0

      const showNotFound = () => {
        if (currentMatch) return
        const finalTaxId = detectedTaxId || readTaxIdFromDOM()
        renderNotFound(getCompanyNameFromDOM(), finalTaxId)
      }

      const domObserver = new MutationObserver(() => {
        if (currentMatch) { domObserver.disconnect(); return }

        const hasContent = jobPage
          ? !!getCompanySlugFromDOM()
          : !!document.querySelector('h1')?.textContent?.trim()

        if (hasContent) {
          if (!contentSeenAt) contentSeenAt = Date.now()
          tryMatch().then(() => {
            // 內容出現 2 秒後仍比對不到 → 顯示 not found
            if (!currentMatch && Date.now() - contentSeenAt > 2000) {
              domObserver.disconnect()
              showNotFound()
            }
          })
        }
      })
      domObserver.observe(document.body, {
        childList: true,
        subtree: true,
      })

      // 安全網：最多等 5 秒
      setTimeout(() => {
        domObserver.disconnect()
        if (!currentMatch) {
          tryMatch().then(() => showNotFound())
        }
      }, 5000)
    }
  }

  init()
})()
