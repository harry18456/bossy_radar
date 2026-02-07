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
  LeaderboardsResponse
} from '~/types/api'

export const useApi = () => {
  const config = useRuntimeConfig()
  const mode = config.public.dataMode

  // Dynamic API Implementation (Original)
  const useDynamicApi = () => {
    const baseURL = config.public.apiBase as string
    console.log('[useApi] Dynamic mode, baseURL:', baseURL)
    const { $toast } = useNuxtApp()

    const api = $fetch.create({
      baseURL,
      headers: {
        'Accept': 'application/json'
      },
      onResponseError({ response }) {
        const errorMessage = response._data?.detail || response._data?.message || '發生未知錯誤'
        if (Array.isArray(errorMessage)) {
          const firstError = errorMessage[0]
          $toast.error(`資料驗證錯誤: ${firstError.msg} (${firstError.loc?.join('.')})`)
        } else {
          $toast.error(errorMessage)
        }
      }
    })

    return {
      getCompanies: (params?: any) => api<PaginatedResponse<Company>>('/api/v1/companies/', { params }),
      getCompanyCatalog: () => api<CompanyCatalog[]>('/api/v1/companies/catalog'),
      getCompanyProfile: (companyCode: string) => api<CompanyProfile>(`/api/v1/companies/${companyCode}/profile`),
      getYearlySummary: (params?: any) => api<YearlySummaryResponse>('/api/v1/companies/yearly-summary', { params }),
      getYearlySummaryIndex: async () => {
        // Fetch yearly summary without filters to get available years from backend
        const response = await api<YearlySummaryResponse>('/api/v1/companies/yearly-summary', { params: { size: 1 } })
        // Extract unique years from the response
        const years = [...new Set((response.items || []).map((item: any) => item.year))].sort((a, b) => b - a)
        return { years, year_stats: [], total_count: response.total || 0, generated_at: new Date().toISOString() }
      },
      getLeaderboards: () => api<LeaderboardsResponse>('/api/v1/leaderboards'),
      getViolations: (params?: any) => api<PaginatedResponse<Violation>>('/api/v1/violations/', { params }),
      getEmployeeBenefits: (params?: any) => api<PaginatedResponse<EmployeeBenefit>>('/api/v1/mops/employee-benefits', { params }),
      getNonManagerSalaries: (params?: any) => api<PaginatedResponse<NonManagerSalary>>('/api/v1/mops/non-manager-salaries', { params }),
      getWelfarePolicies: (params?: any) => api<PaginatedResponse<WelfarePolicy>>('/api/v1/mops/welfare-policies', { params }),
      getSalaryAdjustments: (params?: any) => api<PaginatedResponse<SalaryAdjustment>>('/api/v1/mops/salary-adjustments', { params }),
      getSystemSyncStatus: () => api<SystemSyncStatus>('/api/v1/system/sync-status'),
    }
  }

  // Switch based on mode
  if (mode === 'static') {
    return useStaticApi()
  } else {
    return useDynamicApi()
  }
}
