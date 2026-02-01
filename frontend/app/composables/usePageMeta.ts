interface PageMetaOptions {
  title: string
  description?: string
  image?: string
  /** Optional path for canonical URL, e.g. '/companies/2330' */
  path?: string
}

export const usePageMeta = ({ title, description, image, path }: PageMetaOptions) => {
  const siteName = '慣老闆雷達 | Bossy Radar'
  const siteUrl = 'https://www.bossy.eraser.tw'
  const defaultDescription = '查詢台灣上市櫃公司薪資、福利與勞動違規紀錄，透明化職場資訊。'
  const defaultImage = '/og-image.png'

  // Build canonical URL
  const route = useRoute()
  const canonicalPath = path || route.path
  const canonicalUrl = `${siteUrl}${canonicalPath}`

  useSeoMeta({
    title,
    titleTemplate: (t) => t ? `${t} | ${siteName}` : siteName,
    
    description: description || defaultDescription,
    
    // Open Graph
    ogTitle: title,
    ogDescription: description || defaultDescription,
    ogSiteName: siteName,
    ogImage: image || defaultImage,
    ogUrl: canonicalUrl,
    ogLocale: 'zh_TW',
    ogType: 'website',
    
    // Twitter Card
    twitterCard: 'summary_large_image',
    twitterTitle: title,
    twitterDescription: description || defaultDescription,
    twitterImage: image || defaultImage,
  })

  // Add canonical link tag
  useHead({
    link: [
      { rel: 'canonical', href: canonicalUrl }
    ]
  })
}

