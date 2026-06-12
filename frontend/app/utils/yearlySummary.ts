import type { CompanyProfile, YearlySummaryItem } from '~/types/api'

// Mirrors backend export_service.export_yearly_summaries semantics:
// - MOPS records are keyed by their ROC year as-is.
// - Violation buckets use penalty_date AD year minus 1911; null dates stay
//   out of yearly buckets but still count toward the all-years totals.
// - total_count / total_fine span ALL years (not cumulative to the item year).
// - A (company, year) item exists only when at least one source has data.

interface YearBucket {
  count: number
  fine: number
}

const rocYearOf = (penaltyDate: string | null | undefined): number | null => {
  if (!penaltyDate) return null
  const adYear = Number.parseInt(penaltyDate.slice(0, 4), 10)
  if (Number.isNaN(adYear)) return null
  return adYear - 1911
}

const bucketByRocYear = (
  records: { penalty_date?: string | null, fine_amount: number }[]
): { byYear: Map<number, YearBucket>, total: YearBucket } => {
  const byYear = new Map<number, YearBucket>()
  const total: YearBucket = { count: 0, fine: 0 }

  for (const record of records) {
    const fine = record.fine_amount ?? 0
    total.count += 1
    total.fine += fine

    const year = rocYearOf(record.penalty_date)
    if (year === null) continue

    const bucket = byYear.get(year) ?? { count: 0, fine: 0 }
    byYear.set(year, { count: bucket.count + 1, fine: bucket.fine + fine })
  }

  return { byYear, total }
}

export const buildYearlySummaryItems = (
  profile: CompanyProfile
): YearlySummaryItem[] => {
  const { company } = profile

  const violations = bucketByRocYear(profile.violations)
  const envViolations = bucketByRocYear(profile.environmental_violations)

  const benefitsByYear = new Map(profile.employee_benefits.map(r => [r.year, r]))
  const salariesByYear = new Map(profile.non_manager_salaries.map(r => [r.year, r]))
  const policiesByYear = new Map(profile.welfare_policies.map(r => [r.year, r]))
  const adjustmentsByYear = new Map(profile.salary_adjustments.map(r => [r.year, r]))

  const years = new Set<number>([
    ...benefitsByYear.keys(),
    ...salariesByYear.keys(),
    ...policiesByYear.keys(),
    ...adjustmentsByYear.keys(),
    ...violations.byYear.keys(),
    ...envViolations.byYear.keys()
  ])

  return [...years]
    .sort((a, b) => b - a)
    .map((year) => {
      const violationYear = violations.byYear.get(year) ?? { count: 0, fine: 0 }
      const envYear = envViolations.byYear.get(year) ?? { count: 0, fine: 0 }

      return {
        company_code: company.code,
        company_name: company.name,
        market_type: company.market_type ?? null,
        industry: company.industry ?? null,
        year,
        violations_year_count: violationYear.count,
        violations_year_fine: violationYear.fine,
        violations_total_count: violations.total.count,
        violations_total_fine: violations.total.fine,
        env_violations_year_count: envYear.count,
        env_violations_year_fine: envYear.fine,
        env_violations_total_count: envViolations.total.count,
        env_violations_total_fine: envViolations.total.fine,
        employee_benefit: benefitsByYear.get(year) ?? null,
        non_manager_salary: salariesByYear.get(year) ?? null,
        welfare_policy: policiesByYear.get(year) ?? null,
        salary_adjustment: adjustmentsByYear.get(year) ?? null
      }
    })
}
