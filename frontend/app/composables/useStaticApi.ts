import type { 
  Company, 
  CompanyProfile, 
  PaginatedResponse, 
  Violation, 
  YearlySummaryResponse,
  YearlySummaryIndex,
  EmployeeBenefit,
  NonManagerSalary,
  WelfarePolicy,
  SalaryAdjustment,
  CompanyCatalog,
  SystemSyncStatus,
  YearlySummaryItem,
  LeaderboardsResponse
} from '~/types/api'

export const useStaticApi = () => {
  const { $toast } = useNuxtApp()
  
  // Capture origin synchronously during composable initialization
  // to avoid "Nuxt instance lost" errors in async contexts during SSR.
  let ssrOrigin = ''
  if (import.meta.server) {
    try {
      ssrOrigin = useRequestURL().origin
    } catch (e) {
      console.warn('[useStaticApi] Could not capture request origin synchronously')
    }
  }
  
  // Helper for fetching JSON
  const fetchJson = async <T>(path: string): Promise<T> => {
    try {
      // In SSR, relative paths might fail to hit standard public assets in some envs.
      // Force absolute URL using current request origin.
      // Strategy:
      // 1. Prerender (npm run generate): Read from FS directly to avoid 404s.
      // 2. SSR (node server): Use absolute URL.
      // 3. Client: Use relative URL.
      
      if (import.meta.prerender) {
        try {
          const fs = await import('node:fs/promises')
          const { resolve } = await import('node:path')
          const filePath = resolve(process.cwd(), 'public', 'data', path)
          const content = await fs.readFile(filePath, 'utf-8')
          return JSON.parse(content)
        } catch (err) {
          console.warn(`[StaticApi] FS read failed for ${path}, falling back to fetch.`, err)
        }
      }

      if (import.meta.server && ssrOrigin) {
        return await $fetch<T>(`/data/${path}`, { baseURL: ssrOrigin })
      }
      return await $fetch<T>(`/data/${path}`)
    } catch (e) {
      console.error(`Failed to fetch static data: ${path}`, e)
      $toast.error('無法讀取靜態資料，請稍後再試')
      throw e
    }
  }

  // Client-side pagination helper
  const paginate = <T>(items: T[], page: number = 1, size: number = 20): PaginatedResponse<T> => {
    const total = items.length
    const total_pages = Math.ceil(total / size)
    const validPage = Math.max(1, Math.min(page, total_pages || 1)) // Handle case 0
    
    const start = (validPage - 1) * size
    const end = start + size
    const paginatedItems = items.slice(start, end)
    
    return {
      items: paginatedItems,
      total,
      page: validPage,
      size,
      total_pages
    }
  }

  return {
    // Companies (Client-side Search from Catalog)
    getCompanies: async (params?: any) => {
      let items = await fetchJson<CompanyCatalog[]>('company-catalog.json')
      
      // Filter by company codes (used by watchlist)
      // Support both 'company_code' (matching backend API) and 'code' (backwards compat)
      const codeFilter = params?.company_code || params?.code
      if (codeFilter) {
        const codes = Array.isArray(codeFilter) ? codeFilter : [codeFilter]
        const validCodes = codes.filter((c: string) => c !== '')
        
        if (validCodes.length > 0) {
          items = items.filter(c => validCodes.includes(c.code))
        }
      }
      
      // Filter Logic
      // Check for 'name' (used by companies page) or 'keyword' (fallback)
      const search = params?.name || params?.keyword
      if (search) {
        const k = search.toLowerCase()
        items = items.filter(c => 
          c.name.toLowerCase().includes(k) || 
          c.code.includes(k)
        )
      }
      
      // Handle Industry Filter (Array or String)
      if (params?.industry) {
        const industries = Array.isArray(params.industry) ? params.industry : [params.industry]
        // Filter out empty strings
        const validIndustries = industries.filter((i: string) => i !== '')
        
        if (validIndustries.length > 0) {
           items = items.filter(c => validIndustries.includes(c.industry))
        }
      }
      
      // Handle Market Type Filter (Array or String)
      if (params?.market_type) {
        const markets = Array.isArray(params.market_type) ? params.market_type : [params.market_type]
        const validMarkets = markets.filter((m: string) => m !== '')
        
        if (validMarkets.length > 0) {
          // Mapping frontend values to possible backend values
          // Listed -> listed, sii
          // OTC -> otc
          // Emerging -> rotc
          // Public -> pub, public
          const marketMapping: Record<string, string[]> = {
            'Listed': ['Listed', 'sii', 'SII'],
            'OTC': ['OTC', 'otc', 'OTC'],
            'Emerging': ['Emerging', 'rotc', 'ROTC'],
            'Public': ['Public', 'pub', 'PUB']
          }

          const targetValues = validMarkets.flatMap((m: string) => marketMapping[m] || [m])
          
          items = items.filter(c => targetValues.includes(c.market_type))
        }
      }

      // Sorting Logic
      if (params?.sort) {
        const sortKey = params.sort as string
        const isDesc = sortKey.startsWith('-')
        const key = isDesc ? sortKey.substring(1) : sortKey
        
        items.sort((a: any, b: any) => {
          let valA = a[key]
          let valB = b[key]
          
          // Handle null/undefined
          if (valA === null || valA === undefined) return 1
          if (valB === null || valB === undefined) return -1
          
          if (typeof valA === 'string' && typeof valB === 'string') {
            return isDesc ? valB.localeCompare(valA) : valA.localeCompare(valB)
          }
          
          return isDesc ? valB - valA : valA - valB
        })
      }

      // Convert Catalog to basic Company objects
      const companyItems = items.map(c => ({
        ...c,
        last_updated: new Date().toISOString()
      } as unknown as Company))

      return paginate(companyItems, Number(params?.page) || 1, Number(params?.size) || 20)
    },
    
    getCompanyCatalog: () => 
      fetchJson<CompanyCatalog[]>('company-catalog.json'),
    
    getCompanyProfile: (companyCode: string) => 
      fetchJson<CompanyProfile>(`companies/${companyCode}.json`),
      
    // Yearly Summaries Index (available years)
    getYearlySummaryIndex: async (): Promise<YearlySummaryIndex> => {
      try {
        return await fetchJson<YearlySummaryIndex>('yearly-summaries/index.json')
      } catch {
        // Fallback: return empty if index doesn't exist (old format)
        return { years: [], year_stats: [], total_count: 0, generated_at: '' }
      }
    },
    
    getYearlySummary: async (params?: any) => {
        const index = await fetchJson<{ years: number[] }>('yearly-summaries/index.json')
        
        // Determine which years to load
        let yearsToLoad: number[] = []
        if (params?.year) {
          const requestedYears = Array.isArray(params.year) ? params.year : [params.year]
          yearsToLoad = requestedYears.map(Number).filter((y: number) => index.years.includes(y))
        } else {
          // Default: load all available years
          yearsToLoad = [...index.years]
        }
        
        // Load data for each requested year
        let items: YearlySummaryItem[] = []
        for (const year of yearsToLoad) {
          const yearData = await fetchJson<YearlySummaryItem[]>(`yearly-summaries/${year}.json`)
          items = items.concat(yearData)
        }
        
        // Filter by company_code if specified
        if (params?.company_code) {
          const codes = Array.isArray(params.company_code) ? params.company_code : [params.company_code]
          items = items.filter(i => codes.includes(i.company_code))
        }
        
        return {
          items,
          total: items.length
        } as YearlySummaryResponse
    },

    // Violations (全站搜尋 - 目前暫無頁面使用，且靜態模式無全域導出)
    getViolations: async (params?: any) => {
      // 若未來需要全站搜尋，需後端提供按年分拆的 violations/ 目錄
      return {
        items: [],
        total: 0,
        page: Number(params?.page) || 1,
        size: Number(params?.size) || 20,
        pages: 0
      } as any
    },

    // MOPS Data
    getEmployeeBenefits: async (params?: any) => {
       const items = await fetchJson<EmployeeBenefit[]>('mops/employee-benefits.json')
       // Add filters if needed
       return paginate(items, Number(params?.page) || 1, Number(params?.size) || 20)
    },
      
    getNonManagerSalaries: async (params?: any) => {
       const items = await fetchJson<NonManagerSalary[]>('mops/non-manager-salaries.json')
       return paginate(items, Number(params?.page) || 1, Number(params?.size) || 20)
    },
      
    getWelfarePolicies: async (params?: any) => {
       const items = await fetchJson<WelfarePolicy[]>('mops/welfare-policies.json')
       return paginate(items, Number(params?.page) || 1, Number(params?.size) || 20)
    },

    getSalaryAdjustments: async (params?: any) => {
       const items = await fetchJson<SalaryAdjustment[]>('mops/salary-adjustments.json')
       return paginate(items, Number(params?.page) || 1, Number(params?.size) || 20)
    },

    getLeaderboards: () =>
      fetchJson<LeaderboardsResponse>('leaderboards.json'),

    getSystemSyncStatus: () =>
      fetchJson<SystemSyncStatus>('system-status.json'),
  }
}
