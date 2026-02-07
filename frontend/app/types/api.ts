export interface Company {
  code: string;
  name: string;
  abbreviation?: string | null;
  market_type: string;
  industry?: string | null;
  tax_id?: string | null;
  chairman?: string | null;
  manager?: string | null;
  establishment_date?: string | null;
  listing_date?: string | null;
  capital?: number | null;
  address?: string | null;
  website?: string | null;
  email?: string | null;
  stakeholder_url?: string | null;
  governance_url?: string | null;
  last_updated: string;
}

export interface Violation {
  id: number;
  company_name: string;
  data_source: string;
  authority?: string | null;
  penalty_date?: string | null;
  announcement_date?: string | null;
  disposition_no?: string | null;
  law_article?: string | null;
  violation_content?: string | null;
  fine_amount: number;
  company_code?: string | null;
  created_at: string;
  last_updated: string;
}

export interface EmployeeBenefit {
  id: number;
  company_code?: string | null;
  raw_company_code: string;
  company_name: string;
  year: number;
  market_type: string;
  industry?: string | null;
  employee_count?: number | null;
  employee_salary?: number | null;
  salary_per_employee?: number | null;
  supervisor_salary?: number | null;
  median_employee_salary?: number | null;
  non_supervisor_count?: number | null;
  non_supervisor_salary?: number | null;
  salary_per_non_supervisor?: number | null;
  salary_change_rate?: number | null;
  company_category?: string | null;
  created_at: string;
  last_updated: string;
}

export interface NonManagerSalary {
  id: number;
  company_code?: string | null;
  raw_company_code: string;
  company_name: string;
  year: number;
  market_type: string;
  industry?: string | null;
  employee_count?: number | null;
  avg_salary?: number | null;
  median_salary?: number | null;
  avg_salary_change?: number | null;
  median_salary_change?: number | null;
  eps?: number | null;
  industry_avg_eps?: number | null;
  is_avg_salary_under_500k?: string | null;
  is_better_eps_lower_salary?: string | null;
  is_eps_growth_salary_decrease?: string | null;
  industry_avg_salary?: number | null;
  industry_median_salary?: number | null;
  performance_salary_relation_note?: string | null;
  improvement_measures_note?: string | null;
  created_at: string;
  last_updated: string;
}

export interface WelfarePolicy {
  id: number;
  company_code?: string | null;
  raw_company_code: string;
  company_name: string;
  year: number;
  market_type: string;
  planned_salary_increase?: string | null;
  planned_salary_increase_note?: string | null;
  actual_salary_increase?: string | null;
  actual_salary_increase_note?: string | null;
  non_manager_salary_increase?: string | null;
  non_manager_salary_increase_note?: string | null;
  manager_salary_increase?: string | null;
  manager_salary_increase_note?: string | null;
  entry_salary_master?: string | null;
  entry_salary_bachelor?: string | null;
  entry_salary_highschool?: string | null;
  entry_salary_note?: string | null;
  created_at: string;
  last_updated: string;
}

export interface SalaryAdjustment {
  id: number;
  company_code?: string | null;
  raw_company_code: string;
  company_name: string;
  year: number;
  market_type: string;
  industry?: string | null;
  pretax_net_profit?: number | null;
  allocation_ratio_min?: string | null;
  allocation_ratio_max?: string | null;
  board_resolution_date?: string | null;
  actual_allocation_ratio?: string | null;
  basic_employee_definition?: string | null;
  basic_employee_count?: number | null;
  total_allocation_amount?: number | null;
  allocation_method?: string | null;
  difference_amount?: string | null;
  difference_reason?: string | null;
  difference_handling?: string | null;
  note?: string | null;
  created_at: string;
  last_updated: string;
}

export interface EnvironmentalViolation {
  id: number;
  company_code: string;
  company_name: string;
  penalty_date: string;
  disposition_no: string;
  law_article: string;
  violation_reason: string;
  fine_amount: number;
  authority: string;
  is_illegal_profit?: string | null;
  illegal_profit?: number | null;
  other_penalty?: string | null;
  is_serious?: string | null;
  created_at: string;
  last_updated: string;
}

export interface CompanyProfile {
  company: Company;
  violations: Violation[];
  environmental_violations: EnvironmentalViolation[];
  employee_benefits: EmployeeBenefit[];
  non_manager_salaries: NonManagerSalary[];
  welfare_policies: WelfarePolicy[];
  salary_adjustments: SalaryAdjustment[];
}

export interface YearlySummaryItem {
  company_code: string;
  company_name: string;
  year: number;
  market_type?: string | null;
  industry?: string | null;
  violations_year_count?: number | null;
  violations_year_fine?: number | null;
  violations_total_count?: number | null;
  violations_total_fine?: number | null;
  env_violations_year_count?: number | null;
  env_violations_year_fine?: number | null;
  env_violations_total_count?: number | null;
  env_violations_total_fine?: number | null;
  employee_benefit?: EmployeeBenefit | null;
  non_manager_salary?: NonManagerSalary | null;
  welfare_policy?: WelfarePolicy | null;
  salary_adjustment?: SalaryAdjustment | null;
}

export interface CompanyCatalog {
  code: string;
  name: string;
  abbreviation?: string | null;
  market_type: string;
  industry?: string | null;
  capital?: number | null;
  establishment_date?: string | null;
  listing_date?: string | null;
}

export interface YearlySummaryYearStat {
  year: number;
  count: number;
}

export interface YearlySummaryIndex {
  years: number[];
  year_stats: YearlySummaryYearStat[];
  total_count: number;
  generated_at: string;
}

export interface YearlySummaryResponse {
  items: YearlySummaryItem[];
  total: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  total_pages: number;
}

export interface CategorySyncStatus {
  last_updated: string | null;
  count: number;
}

export interface SystemSyncStatus {
  companies: Record<string, CategorySyncStatus>;
  violations: Record<string, CategorySyncStatus>;
  mops: Record<string, CategorySyncStatus>;
  environmental_violations: Record<string, CategorySyncStatus>;
}

// Leaderboards API Types
export interface ViolationLeaderboardItem {
  company_code: string;
  company_name: string;
  labor_count: number;
  labor_fine: number;
  env_count: number;
  env_fine: number;
  total_count: number;
  total_fine: number;
}

export interface SalaryLeaderboardItem {
  company_code: string;
  company_name: string;
  avg_salary: number;
  median_salary: number;
  eps?: number;
}

export interface IndustrySalaryLeaderboardItem extends SalaryLeaderboardItem {
  industry: string;
}

export interface ViolationLeaderboardSet {
  top_by_count: ViolationLeaderboardItem[];
  bottom_by_count: ViolationLeaderboardItem[];
  top_by_fine: ViolationLeaderboardItem[];
  bottom_by_fine: ViolationLeaderboardItem[];
}

export interface SalaryLeaderboardSet {
  top_by_avg: SalaryLeaderboardItem[];
  bottom_by_avg: SalaryLeaderboardItem[];
  top_by_median: SalaryLeaderboardItem[];
  bottom_by_median: SalaryLeaderboardItem[];
}

export interface IndustrySalaryLeaderboardSet {
  top_by_median: IndustrySalaryLeaderboardItem[];
  bottom_by_median: IndustrySalaryLeaderboardItem[];
  top_by_eps: IndustrySalaryLeaderboardItem[];
  bottom_by_eps: IndustrySalaryLeaderboardItem[];
}

export interface LeaderboardsResponse {
  latest_year: number;
  violation_all_time: ViolationLeaderboardSet;
  violation_yearly: Record<string, ViolationLeaderboardSet>;
  salary: Record<string, SalaryLeaderboardSet>;
  salary_by_industry: Record<string, Record<string, IndustrySalaryLeaderboardSet>>;
}
