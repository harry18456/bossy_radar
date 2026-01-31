export default defineNuxtPlugin((nuxtApp) => {
  const config = useRuntimeConfig()
  const gaId = config.public.googleAnalyticsId

  if (!gaId) {
    console.warn('Google Analytics 4 ID not found')
    return
  }

  // Define local gtag interface
  let gtag: (...args: any[]) => void

  if (import.meta.dev) {
    // Mock mode for Development
    console.log('[GA4] running in Dev Mode (events will be logged to console)')
    gtag = (...args: any[]) => {
      console.log('[GA4 Event]:', ...args)
    }
  } else {
    // Production: Use global gtag function (injected by nuxt.config.ts)
    // If initialization hasn't run yet for some reason, we fallback to dataLayer push
    const w = window as any
    w.dataLayer = w.dataLayer || []
    
    gtag = (...args: any[]) => {
       if (typeof w.gtag === 'function') {
         w.gtag(...args)
       } else {
         w.dataLayer.push(args)
       }
    }
  }

  // Track route changes
  const router = useRouter()
  router.afterEach((to) => {
    // We don't need to re-initialize config here (done in head), just page_view updates
    // But Google convention says sending 'config' again with page_path updates the page view.
    gtag('config', gaId, {
      page_path: to.fullPath,
      page_title: document.title
    })
  })
})
