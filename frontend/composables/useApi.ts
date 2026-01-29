import type { 
  Company, 
  CompanyProfile, 
  PaginatedResponse, 
  Violation, 
  YearlySummaryResponse,
  EmployeeBenefit,
  NonManagerSalary,
  WelfarePolicy,
  SalaryAdjustment 
} from '~/types/api'

export const useApi = () => {
  const config = useRuntimeConfig()
  const baseURL = config.public.apiBase as string

  const { $toast } = useNuxtApp()

  const api = $fetch.create({
    baseURL,
    headers: {
      'Accept': 'application/json'
    },
    onResponseError({ response }) {
      // Try to extract error message from common API error formats
      const errorMessage = response._data?.detail || response._data?.message || '發生未知錯誤'
      
      // If detail is an array (Pydantic validation error), show the first one
      if (Array.isArray(errorMessage)) {
        const firstError = errorMessage[0]
        $toast.error(`資料驗證錯誤: ${firstError.msg} (${firstError.loc?.join('.')})`)
      } else {
        $toast.error(errorMessage)
      }
    }
  })

  return {
    // Companies
    getCompanies: (params?: any) => 
      api<PaginatedResponse<Company>>('/api/v1/companies/', { params }),
    
    getCompanyProfile: (companyCode: string) => 
      api<CompanyProfile>(`/api/v1/companies/${companyCode}/profile`),
      
    getYearlySummary: (params?: any) => 
      api<YearlySummaryResponse>('/api/v1/companies/yearly-summary', { params }),

    // Violations
    getViolations: (params?: any) => 
      api<PaginatedResponse<Violation>>('/api/v1/violations/', { params }),

    // MOPS Data
    getEmployeeBenefits: (params?: any) => 
      api<PaginatedResponse<EmployeeBenefit>>('/api/v1/mops/employee-benefits', { params }),
      
    getNonManagerSalaries: (params?: any) => 
      api<PaginatedResponse<NonManagerSalary>>('/api/v1/mops/non-manager-salaries', { params }),
      
    getWelfarePolicies: (params?: any) => 
      api<PaginatedResponse<WelfarePolicy>>('/api/v1/mops/welfare-policies', { params }),

    getSalaryAdjustments: (params?: any) => 
      api<PaginatedResponse<SalaryAdjustment>>('/api/v1/mops/salary-adjustments', { params }),
  }
}
