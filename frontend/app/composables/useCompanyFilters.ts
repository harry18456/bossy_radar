import { z } from 'zod'

// Define the filter schema for validation and type inference
const filterSchema = z.object({
  page: z.number().int().min(1).default(1),
  size: z.number().int().min(1).max(100).default(20),
  sort: z.string().optional(), // e.g. "-capital"
  name: z.string().optional(),
  
  // Multi-select filters
  industry: z.array(z.string()).optional(),
  market_type: z.array(z.string()).optional(),
})

export type CompanyFilters = z.infer<typeof filterSchema>

export const useCompanyFilters = () => {
  const route = useRoute()
  const router = useRouter()

  // Helper to parse array from query (it can be string | string[] | undefined)
  const parseArray = (val: string | string[] | undefined): string[] => {
    if (!val) return []
    return Array.isArray(val) ? val : [val]
  }

  // Reactive state initialized from URL
  const filters = reactive({
    page: Number(route.query.page) || 1,
    size: Number(route.query.size) || 20,
    sort: (route.query.sort as string) || undefined,
    name: (route.query.name as string) || undefined,
    
    // Arrays
    industry: parseArray(route.query.industry as string | string[]),
    market_type: parseArray(route.query.market_type as string | string[])
  })

  // Reset page to 1 when any search filter shifts, but NOT when only the page number changes
  watch(
    () => ({ 
      name: filters.name, 
      industry: [...filters.industry], 
      market_type: [...filters.market_type], 
      sort: filters.sort 
    }),
    (newVal, oldVal) => {
      // Deep comparison to see if filters actually changed
      const changed = JSON.stringify(newVal) !== JSON.stringify(oldVal)
      if (changed && filters.page !== 1) {
        filters.page = 1
      }
    }
  )

  // Watch filters and update URL
  // Use debounced watch for text input, standard watch for others could be immediate
  // But for simplicity, we watch standardly here. The UI component should handle debounce for text input binding.
  watch(
    filters,
    (newFilters) => {
      // Clean up empty/default values to keep URL clean
      const query: Record<string, any> = {
        ...route.query,
        page: newFilters.page > 1 ? newFilters.page : undefined,
        size: newFilters.size !== 20 ? newFilters.size : undefined,
        sort: newFilters.sort,
        name: newFilters.name || undefined,
        industry: newFilters.industry.length > 0 ? newFilters.industry : undefined,
        market_type: newFilters.market_type.length > 0 ? newFilters.market_type : undefined,
      }

      // Remove undefined keys
      Object.keys(query).forEach(key => query[key] === undefined && delete query[key])

      router.push({ query })
    },
    { deep: true }
  )

  // Watch URL changes (e.g. back/forward button) and sync back to state
  watch(
    () => route.query,
    (newQuery) => {
      if (newQuery.page) filters.page = Number(newQuery.page)
      if (newQuery.size) filters.size = Number(newQuery.size)
      filters.sort = (newQuery.sort as string) || undefined
      filters.name = (newQuery.name as string) || undefined
      filters.industry = parseArray(newQuery.industry as string | string[])
      filters.market_type = parseArray(newQuery.market_type as string | string[])
    }
  )

  const resetFilters = () => {
    filters.page = 1
    filters.sort = undefined
    filters.name = undefined
    filters.industry = []
    filters.market_type = []
  }

  const updateFilter = (key: keyof CompanyFilters, value: any) => {
    // @ts-ignore
    filters[key] = value
  }

  return {
    filters,
    ...toRefs(filters),
    updateFilter,
    resetFilters
  }
}
