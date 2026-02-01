import { defineStore } from 'pinia'
import type { Company } from '~/types/api'

export const useWatchlistStore = defineStore('watchlist', {
  state: () => ({
    // Only persist company codes - this is what gets saved to localStorage
    codes: [] as string[],
    // Hydrated company data - populated from API/catalog on page load
    // This is NOT persisted
    _companies: [] as Company[],
  }),
  
  getters: {
    count: (state) => state.codes.length,
    
    // Get hydrated companies (populated after fetch)
    companies: (state) => state._companies,
    
    // Check if a company is already in the watchlist
    isWatching: (state) => (companyCode: string) => {
      return state.codes.includes(companyCode)
    }
  },

  actions: {
    addCompany(company: Company) {
      if (!this.isWatching(company.code)) {
        this.codes.push(company.code)
        // Also add to hydrated list for immediate UI update
        this._companies.push(company)
      }
    },

    removeCompany(companyCode: string) {
      const codeIndex = this.codes.indexOf(companyCode)
      if (codeIndex !== -1) {
        this.codes.splice(codeIndex, 1)
      }
      // Also remove from hydrated list
      const companyIndex = this._companies.findIndex(c => c.code === companyCode)
      if (companyIndex !== -1) {
        this._companies.splice(companyIndex, 1)
      }
    },

    toggleCompany(company: Company) {
      if (this.isWatching(company.code)) {
        this.removeCompany(company.code)
      } else {
        this.addCompany(company)
      }
    },

    // Called by watchlist page to hydrate companies from fresh data
    hydrateCompanies(companies: Company[]) {
      this._companies = companies
    }
  },

  persist: {
    // Only persist the codes array, not the hydrated companies
    pick: ['codes'],
    // Use localStorage on client-side for persistence across browser restarts
    // On server-side (SSR), this will fall back to cookies automatically
    storage: typeof window !== 'undefined' ? localStorage : undefined
  }
})


