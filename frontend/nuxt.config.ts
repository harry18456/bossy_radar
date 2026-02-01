// https://nuxt.com/docs/api/configuration/nuxt-config
import tailwindcss from "@tailwindcss/vite";

import pkg from './package.json'

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
    exclude: ['/privacy', '/data-sources'],
  },
  vite: {
    plugins: [tailwindcss()],
  },
  nitro: {
    prerender: {
      failOnError: false
    },
    compressPublicAssets: {
      gzip: true,
      brotli: true
    }
  }
});

