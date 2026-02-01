import type { Script } from '@unhead/schema'

interface WebSiteSchema {
  name: string
  url: string
  description?: string
}

interface OrganizationSchema {
  name: string
  url: string
  logo?: string
  description?: string
}

interface LocalBusinessSchema {
  name: string
  description?: string
  url?: string
  address?: string
}

/**
 * Composable for injecting JSON-LD structured data into the page head.
 * This helps Google Search Console understand the content of your pages.
 */
export const useStructuredData = () => {
  const siteUrl = 'https://www.bossy.eraser.tw'

  /**
   * Inject WebSite schema - recommended for homepage
   */
  const injectWebSiteSchema = (options: Partial<WebSiteSchema> = {}) => {
    const schema = {
      '@context': 'https://schema.org',
      '@type': 'WebSite',
      name: options.name || '慣老闆雷達 | Bossy Radar',
      url: options.url || siteUrl,
      description: options.description || '查詢台灣上市櫃公司薪資、福利與勞動違規紀錄，透明化職場資訊。',
      potentialAction: {
        '@type': 'SearchAction',
        target: {
          '@type': 'EntryPoint',
          urlTemplate: `${siteUrl}/companies?name={search_term_string}`
        },
        'query-input': 'required name=search_term_string'
      }
    }

    useHead({
      script: [
        {
          type: 'application/ld+json',
          innerHTML: JSON.stringify(schema),
        } as Script
      ]
    })
  }

  /**
   * Inject Organization schema - recommended for about or homepage
   */
  const injectOrganizationSchema = (options: Partial<OrganizationSchema> = {}) => {
    const schema = {
      '@context': 'https://schema.org',
      '@type': 'Organization',
      name: options.name || '慣老闆雷達',
      url: options.url || siteUrl,
      logo: options.logo || `${siteUrl}/og-image.png`,
      description: options.description || '台灣上市櫃公司薪資福利與違規紀錄查詢平台',
    }

    useHead({
      script: [
        {
          type: 'application/ld+json',
          innerHTML: JSON.stringify(schema),
        } as Script
      ]
    })
  }

  /**
   * Inject LocalBusiness/Organization schema for individual company pages
   */
  const injectCompanySchema = (company: LocalBusinessSchema) => {
    const schema = {
      '@context': 'https://schema.org',
      '@type': 'Organization',
      name: company.name,
      description: company.description,
      url: company.url,
      address: company.address ? {
        '@type': 'PostalAddress',
        streetAddress: company.address
      } : undefined
    }

    useHead({
      script: [
        {
          type: 'application/ld+json',
          innerHTML: JSON.stringify(schema),
        } as Script
      ]
    })
  }

  /**
   * Inject BreadcrumbList schema for navigation
   */
  const injectBreadcrumbSchema = (items: Array<{ name: string; url: string }>) => {
    const schema = {
      '@context': 'https://schema.org',
      '@type': 'BreadcrumbList',
      itemListElement: items.map((item, index) => ({
        '@type': 'ListItem',
        position: index + 1,
        name: item.name,
        item: item.url.startsWith('http') ? item.url : `${siteUrl}${item.url}`
      }))
    }

    useHead({
      script: [
        {
          type: 'application/ld+json',
          innerHTML: JSON.stringify(schema),
        } as Script
      ]
    })
  }

  return {
    injectWebSiteSchema,
    injectOrganizationSchema,
    injectCompanySchema,
    injectBreadcrumbSchema,
  }
}
