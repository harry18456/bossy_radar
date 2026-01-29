import { defineStore } from 'pinia'
import type { Company } from '~/types/api'

export const useWatchlistStore = defineStore('watchlist', {
  state: () => ({
    // Store saved companies
    companies: [] as Company[],
  }),
  
  getters: {
    count: (state) => state.companies.length,
    
    // Check if a company is already in the watchlist
    isWatching: (state) => (companyCode: string) => {
      return state.companies.some(c => c.code === companyCode)
    }
  },

  actions: {
    addCompany(company: Company) {
      if (!this.isWatching(company.code)) {
        this.companies.push(company)
      }
    },

    removeCompany(companyCode: string) {
      const index = this.companies.findIndex(c => c.code === companyCode)
      if (index !== -1) {
        this.companies.splice(index, 1)
      }
    },

    toggleCompany(company: Company) {
      if (this.isWatching(company.code)) {
        this.removeCompany(company.code)
      } else {
        this.addCompany(company)
      }
    }
  },

  persist: {
    storage: persistedState.localStorage,
  }
})
