import { readFileSync, readdirSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { describe, it, expect } from 'vitest'
import { buildYearlySummaryItems } from '~/utils/yearlySummary'
import type {
  Company,
  CompanyProfile,
  EnvironmentalViolation,
  NonManagerSalary,
  Violation,
  YearlySummaryItem
} from '~/types/api'

// Committed fixtures (trimmed export samples) so the frontend<->backend export
// parity test runs in CI without the gitignored public/data tree. Regenerate
// after an export-format change by copying the two companies' profiles and
// filtering each yearly-summaries/<year>.json down to those company codes.
const dataDir = fileURLToPath(new URL('../fixtures', import.meta.url))

let nextId = 0

const makeCompany = (overrides: Partial<Company> = {}): Company => ({
  code: '9999',
  name: '測試公司',
  market_type: 'Listed',
  industry: '23',
  last_updated: '2026-01-01T00:00:00',
  ...overrides
})

const makeViolation = (
  penalty_date: string | null,
  fine_amount: number
): Violation => ({
  id: ++nextId,
  company_name: '測試公司',
  data_source: 'test',
  penalty_date,
  fine_amount,
  company_code: '9999',
  created_at: '2026-01-01T00:00:00',
  last_updated: '2026-01-01T00:00:00'
})

const makeEnvViolation = (
  penalty_date: string,
  fine_amount: number
): EnvironmentalViolation => ({
  id: ++nextId,
  company_code: '9999',
  company_name: '測試公司',
  penalty_date,
  disposition_no: 'TEST-001',
  law_article: '測試條文',
  violation_reason: '測試違規',
  fine_amount,
  authority: '測試機關',
  created_at: '2026-01-01T00:00:00',
  last_updated: '2026-01-01T00:00:00'
})

const makeSalary = (year: number): NonManagerSalary => ({
  id: ++nextId,
  company_code: '9999',
  raw_company_code: '9999',
  company_name: '測試公司',
  year,
  market_type: 'sii',
  created_at: '2026-01-01T00:00:00',
  last_updated: '2026-01-01T00:00:00'
})

const makeProfile = (overrides: Partial<CompanyProfile> = {}): CompanyProfile => ({
  company: makeCompany(),
  violations: [],
  environmental_violations: [],
  employee_benefits: [],
  non_manager_salaries: [],
  welfare_policies: [],
  salary_adjustments: [],
  ...overrides
})

describe('buildYearlySummaryItems', () => {
  it('converts AD penalty dates to ROC years and computes totals across all years', () => {
    // Spec example: violations dated 2024-03-01 (fine 50000) and 2022-07-15
    // (fine 20000), plus a non-manager salary record for ROC year 113.
    const profile = makeProfile({
      violations: [
        makeViolation('2024-03-01', 50000),
        makeViolation('2022-07-15', 20000)
      ],
      non_manager_salaries: [makeSalary(113)]
    })

    const items = buildYearlySummaryItems(profile)
    const byYear = new Map(items.map(i => [i.year, i]))

    const y113 = byYear.get(113)
    expect(y113).toBeDefined()
    expect(y113?.violations_year_count).toBe(1)
    expect(y113?.violations_year_fine).toBe(50000)
    expect(y113?.violations_total_count).toBe(2)
    expect(y113?.violations_total_fine).toBe(70000)
    expect(y113?.non_manager_salary).toBeTruthy()

    const y111 = byYear.get(111)
    expect(y111).toBeDefined()
    expect(y111?.violations_year_count).toBe(1)
    expect(y111?.violations_year_fine).toBe(20000)
    expect(y111?.violations_total_count).toBe(2)
    expect(y111?.violations_total_fine).toBe(70000)
    expect(y111?.non_manager_salary).toBeNull()
  })

  it('produces no item for years without any data', () => {
    const profile = makeProfile({
      non_manager_salaries: [makeSalary(113), makeSalary(110)]
    })

    const items = buildYearlySummaryItems(profile)

    expect(items.map(i => i.year).sort()).toEqual([110, 113])
  })

  it('excludes null penalty_date from yearly buckets but counts it in totals', () => {
    const profile = makeProfile({
      violations: [
        makeViolation('2024-05-05', 100),
        makeViolation(null, 999)
      ]
    })

    const items = buildYearlySummaryItems(profile)

    expect(items).toHaveLength(1)
    const y113 = items[0]
    expect(y113?.year).toBe(113)
    expect(y113?.violations_year_count).toBe(1)
    expect(y113?.violations_year_fine).toBe(100)
    expect(y113?.violations_total_count).toBe(2)
    expect(y113?.violations_total_fine).toBe(1099)
  })

  it('buckets environmental violations independently from labor violations', () => {
    const profile = makeProfile({
      violations: [makeViolation('2024-01-01', 100)],
      environmental_violations: [makeEnvViolation('2023-01-15', 5000)]
    })

    const items = buildYearlySummaryItems(profile)
    const byYear = new Map(items.map(i => [i.year, i]))

    const y112 = byYear.get(112)
    expect(y112?.env_violations_year_count).toBe(1)
    expect(y112?.env_violations_year_fine).toBe(5000)
    expect(y112?.env_violations_total_count).toBe(1)
    expect(y112?.env_violations_total_fine).toBe(5000)
    expect(y112?.violations_year_count).toBe(0)

    const y113 = byYear.get(113)
    expect(y113?.env_violations_year_count).toBe(0)
    expect(y113?.env_violations_total_count).toBe(1)
  })

  it('orders items by year descending', () => {
    const profile = makeProfile({
      non_manager_salaries: [makeSalary(110), makeSalary(113), makeSalary(108)]
    })

    const items = buildYearlySummaryItems(profile)

    expect(items.map(i => i.year)).toEqual([113, 110, 108])
  })

  it('fills company identity fields from the profile company record', () => {
    const profile = makeProfile({
      company: makeCompany({ code: '8888', name: '示例公司', market_type: 'OTC', industry: '17' }),
      non_manager_salaries: [{ ...makeSalary(113), company_code: '8888', raw_company_code: '8888' }]
    })

    const items = buildYearlySummaryItems(profile)

    expect(items[0]?.company_code).toBe('8888')
    expect(items[0]?.company_name).toBe('示例公司')
    expect(items[0]?.market_type).toBe('OTC')
    expect(items[0]?.industry).toBe('17')
  })

  describe('assembled values equal exported values (real export samples)', () => {
    const sampleCodes = ['2330', '2002']

    const loadJson = <T>(relPath: string): T =>
      JSON.parse(readFileSync(`${dataDir}/${relPath}`, 'utf-8')) as T

    const exportedYears = (): number[] =>
      readdirSync(`${dataDir}/yearly-summaries`)
        .filter(f => /^\d+\.json$/.test(f))
        .map(f => Number.parseInt(f.replace('.json', ''), 10))

    it.each(sampleCodes)('matches exporter output for company %s', (code) => {
      const profile = loadJson<CompanyProfile>(`companies/${code}.json`)
      const assembled = buildYearlySummaryItems(profile)
      const assembledByYear = new Map(assembled.map(i => [i.year, i]))

      const exported = new Map<number, YearlySummaryItem>()
      for (const year of exportedYears()) {
        const yearItems = loadJson<YearlySummaryItem[]>(`yearly-summaries/${year}.json`)
        const item = yearItems.find(i => i.company_code === code)
        if (item) exported.set(year, item)
      }

      expect(exported.size).toBeGreaterThan(0)
      expect([...assembledByYear.keys()].sort()).toEqual([...exported.keys()].sort())

      for (const [year, exportedItem] of exported) {
        expect(assembledByYear.get(year), `year ${year}`).toEqual(exportedItem)
      }
    })
  })
})
