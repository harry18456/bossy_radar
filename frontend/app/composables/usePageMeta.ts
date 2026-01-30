interface PageMetaOptions {
  title: string
  description?: string
  image?: string
}

export const usePageMeta = ({ title, description, image }: PageMetaOptions) => {
  const siteName = 'Bossy Radar'
  const defaultDescription = '查詢台灣上市櫃公司薪資、福利與勞動違規紀錄，透明化職場資訊。'
  const defaultImage = '/og-image.png' // Make sure to add this file to public/ later

  useSeoMeta({
    title,
    titleTemplate: (t) => t ? `${t} | ${siteName}` : siteName,
    
    description: description || defaultDescription,
    
    // Open Graph
    ogTitle: title,
    ogDescription: description || defaultDescription,
    ogSiteName: siteName,
    ogImage: image || defaultImage,
    
    // Twitter Card
    twitterCard: 'summary_large_image',
    twitterTitle: title,
    twitterDescription: description || defaultDescription,
    twitterImage: image || defaultImage,
  })
}
