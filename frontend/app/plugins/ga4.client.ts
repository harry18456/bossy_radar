export default defineNuxtPlugin((_nuxtApp) => {
  const config = useRuntimeConfig()
  const gaId = config.public.googleAnalyticsId

  if (!gaId) {
    return
  }

  // Initialize dataLayer
  const w = window as any
  w.dataLayer = w.dataLayer || []

  // Define gtag function (Real vs Mock)
  let gtag: (...args: any[]) => void

  if (import.meta.dev) {
    // Mock mode for Development
    gtag = () => {}
  } else {
    // Real mode for Production
    // Use useHead to inject the script tag
    useHead({
      script: [
        {
          src: `https://www.googletagmanager.com/gtag/js?id=${gaId}`,
          async: true,
          tagPosition: 'head'
        }
      ]
    })

    // Standard implementation
    gtag = function() {
      w.dataLayer.push(arguments)
    }
  }

  // Expose to window for global access/debugging
  w.gtag = gtag

  // Initialize
  gtag('js', new Date())
  gtag('config', gaId)

  // Track route changes
  const router = useRouter()
  router.afterEach((to) => {
    gtag('config', gaId, {
      page_path: to.fullPath,
      page_title: document.title
    })
  })
})
