import { toast } from 'vue-sonner'

export default defineNuxtPlugin((_nuxtApp) => {
  return {
    provide: {
      toast
    }
  }
})
