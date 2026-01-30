import { defineStore } from 'pinia'
import type { CompanyCatalog } from '~/types/api'

export const useCompanyStore = defineStore('company', () => {
  const api = useApi()
  const catalog = ref<CompanyCatalog[]>([])
  const isLoading = ref(false)
  const lastFetched = ref<number | null>(null)

  const fetchCatalog = async (force = false) => {
    // Cache for 1 hour
    const oneHour = 60 * 60 * 1000
    if (!force && lastFetched.value && (Date.now() - lastFetched.value < oneHour)) {
      return
    }

    isLoading.value = true
    try {
      const data = await api.getCompanyCatalog()
      catalog.value = data
      lastFetched.value = Date.now()
    } catch (error) {
      console.error('Failed to fetch company catalog:', error)
    } finally {
      isLoading.value = false
    }
  }

  return {
    catalog,
    isLoading,
    fetchCatalog
  }
})
