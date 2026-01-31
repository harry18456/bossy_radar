import type { 
  Company, 
  CompanyProfile, 
  PaginatedResponse, 
  Violation, 
  YearlySummaryResponse,
  EmployeeBenefit,
  NonManagerSalary,
  WelfarePolicy,
  SalaryAdjustment,
  CompanyCatalog,
  SystemSyncStatus,
  YearlySummaryItem
} from '~/types/api'

export const useStaticApi = () => {
  const { $toast } = useNuxtApp()
  
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

      if (import.meta.server) {
        const { origin } = useRequestURL()
        return await $fetch<T>(`/data/${path}`, { baseURL: origin })
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
        const validIndustries = industries.filter(i => i !== '')
        
        if (validIndustries.length > 0) {
           items = items.filter(c => validIndustries.includes(c.industry))
        }
      }
      
      // Handle Market Type Filter (Array or String)
      if (params?.market_type) {
        const markets = Array.isArray(params.market_type) ? params.market_type : [params.market_type]
        const validMarkets = markets.filter(m => m !== '')
        
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

          const targetValues = validMarkets.flatMap(m => marketMapping[m] || [m])
          
          items = items.filter(c => targetValues.includes(c.market_type))
        }
      }

      // Convert Catalog to basic Company objects (missing fields will be undefined, but acceptable for list view)
      // Ideally catalog should match Company lists, or we map it. 
      // The current Company interface has more fields, but list view mostly needs name/code/market/industry.
      const companyItems = items.map(c => ({
        ...c,
        last_updated: new Date().toISOString() // Mock
      } as unknown as Company))

      return paginate(companyItems, Number(params?.page) || 1, Number(params?.size) || 20)
    },
    
    getCompanyCatalog: () => 
      fetchJson<CompanyCatalog[]>('company-catalog.json'),
    
    getCompanyProfile: (companyCode: string) => 
      fetchJson<CompanyProfile>(`companies/${companyCode}.json`),
      
    getYearlySummary: async (params?: any) => {
      let items = await fetchJson<YearlySummaryItem[]>('yearly-summaries.json')
      
      // Filter by Companies
      if (params?.company_code) {
        const codes = Array.isArray(params.company_code) ? params.company_code : [params.company_code]
        items = items.filter(i => codes.includes(i.company_code))
      }
      
      // Filter by Year
      if (params?.year) {
        const years = Array.isArray(params.year) ? params.year : [params.year]
        items = items.filter(i => years.includes(Number(i.year)))
      }

      return {
        items,
        total: items.length
      } as YearlySummaryResponse
    },

    // Violations
    getViolations: async (params?: any) => {
      // NOTE: Assuming violations-all.json exists. If split by pages, this logic needs change.
      let items = await fetchJson<Violation[]>('violations-all.json')
      
      if (params?.search) {
        const k = params.search.toLowerCase()
        items = items.filter(v => 
          v.company_name.toLowerCase().includes(k) ||
          v.violation_content?.toLowerCase().includes(k)
        )
      }

      return paginate(items, Number(params?.page) || 1, Number(params?.size) || 20)
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

    getSystemSyncStatus: () =>
      fetchJson<SystemSyncStatus>('system-status.json'),
  }
}
