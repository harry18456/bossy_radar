export default defineNuxtPlugin((nuxtApp) => {
  const config = useRuntimeConfig()
  const gaId = config.public.googleAnalyticsId

  if (!gaId) {
    console.warn('Google Analytics 4 ID not found')
    return
  }

  // Disable in development
  if (import.meta.dev) {
    console.log('[GA4] Disabled in development mode')
    return
  }

  // Helper to append script
  const addScript = (src: string) => {
    const script = document.createElement('script')
    script.async = true
    script.src = src
    document.head.appendChild(script)
  }

  // Load gtag.js
  addScript(`https://www.googletagmanager.com/gtag/js?id=${gaId}`)

  // Initialize dataLayer
  const w = window as any
  w.dataLayer = w.dataLayer || []
  function gtag(...args: any[]) {
    w.dataLayer.push(args)
  }
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
