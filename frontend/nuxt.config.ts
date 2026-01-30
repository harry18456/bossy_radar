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
      apiBase: process.env.NUXT_PUBLIC_API_BASE || "http://localhost:8000",
      googleAdSense: {
        id: process.env.NUXT_PUBLIC_GOOGLE_ADSENSE_ID || '',
        slots: {
          top: process.env.NUXT_PUBLIC_GOOGLE_ADSENSE_SLOT_TOP || '',
          bottom: process.env.NUXT_PUBLIC_GOOGLE_ADSENSE_SLOT_BOTTOM || ''
        }
      },
    },
  },
  app: {
    head: {
      script: [
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
  ],
  colorMode: {
    classSuffix: "",
  },
  vite: {
    plugins: [tailwindcss()],
  },
});
