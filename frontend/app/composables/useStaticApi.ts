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
      if (params?.keyword) {
        const k = params.keyword.toLowerCase()
        items = items.filter(c => 
          c.name.toLowerCase().includes(k) || 
          c.code.includes(k)
        )
      }
      
      if (params?.industry) {
        items = items.filter(c => c.industry === params.industry)
      }
      
      if (params?.market_type) {
        items = items.filter(c => c.market_type === params.market_type)
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
