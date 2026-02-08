// https://nuxt.com/docs/api/configuration/nuxt-config
import tailwindcss from "@tailwindcss/vite";
import { readFileSync, existsSync } from 'fs';
import { resolve } from 'path';

import pkg from './package.json'

// Read company catalog at build time for sitemap generation
function getCompanyUrls(): string[] {
  const catalogPath = resolve(__dirname, 'public/data/company-catalog.json');
  if (!existsSync(catalogPath)) {
    console.warn('[Sitemap] company-catalog.json not found, skipping dynamic routes');
    return [];
  }
  
  try {
    const catalog = JSON.parse(readFileSync(catalogPath, 'utf-8')) as { code: string }[];
    // Filter out invalid codes (must be alphanumeric, no dots/slashes)
    const validCodes = catalog
      .map(c => c.code)
      .filter(code => code && /^[A-Za-z0-9]+$/.test(code));
    
    console.log(`[Sitemap] Loaded ${validCodes.length} company codes for sitemap`);
    return validCodes.map(code => `/companies/${code}`);
  } catch (e) {
    console.error('[Sitemap] Failed to read company catalog:', e);
    return [];
  }
}

export default defineNuxtConfig({
  future: {
    compatibilityVersion: 4,
  },
  runtimeConfig: {
    public: {
      appVersion: pkg.version,
      dataMode: process.env.NUXT_PUBLIC_DATA_MODE || 'dynamic',
      apiBase: process.env.NUXT_PUBLIC_API_BASE || "http://localhost:8000",
      googleAdSense: {
        id: process.env.NUXT_PUBLIC_GOOGLE_ADSENSE_ID || '',
        slots: {
          top: process.env.NUXT_PUBLIC_GOOGLE_ADSENSE_SLOT_TOP || '',
          bottom: process.env.NUXT_PUBLIC_GOOGLE_ADSENSE_SLOT_BOTTOM || ''
        }
      },
      googleAnalyticsId: process.env.NUXT_PUBLIC_GA4_ID || '',
    },
  },
  site: {
    url: 'https://www.bossy.eraser.tw',
    name: '慣老闆雷達 | Bossy Radar',
  },
  app: {
    head: {
      htmlAttrs: {
        lang: 'zh-TW',
      },
      script: [
        // Inline blocking script to prevent dark mode flash
        // This runs BEFORE any CSS is applied
        {
          innerHTML: `
            (function() {
              try {
                var colorMode = localStorage.getItem('nuxt-color-mode');
                if (colorMode === 'dark' || 
                    (!colorMode && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
                  document.documentElement.classList.add('dark');
                } else {
                  document.documentElement.classList.remove('dark');
                }
              } catch (e) {}
            })();
          `,
          tagPosition: 'head',
        },
        {
          src: `https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=${process.env.NUXT_PUBLIC_GOOGLE_ADSENSE_ID}`,
          async: true,
          crossorigin: "anonymous",
          tagPosition: 'bodyClose'
        }
      ]
    }
  },
  compatibilityDate: "2025-07-15",
  devtools: { enabled: true },
  css: ["~/assets/css/main.css"],
  modules: [
    "@pinia/nuxt",
    "pinia-plugin-persistedstate/nuxt",
    "@nuxt/icon",
    "@nuxtjs/color-mode",
    "@vueuse/nuxt",
    "@nuxtjs/sitemap",
  ],
  colorMode: {
    classSuffix: "",
  },
  sitemap: {
    urls: getCompanyUrls(),
    exclude: ['/privacy', '/data-sources'],
  },
  vite: {
    plugins: [tailwindcss()],
  },
  nitro: {
    prerender: {
      failOnError: false,
      // Ignore invalid company routes (non-alphanumeric codes)
      ignore: [
        /^\/companies\/[^A-Za-z0-9\/]+$/,
      ],
    },
    compressPublicAssets: {
      gzip: true,
      brotli: true
    }
  }
});


