## 1. Review Gate

- [x] 1.1 Resolve "Record stricter CSP alternatives without applying them by default" by confirming that this change implements方案 A: Vercel allowlist + 'unsafe-inline'; verification: reviewer sign-off is recorded before frontend/vercel.json is changed.

## 2. CSP Policy

- [x] 2.1 Implement "Use Vercel CSP allowlist with SSG-compatible inline handling" and "Include observed runtime third-party domains" so Production deployment SHALL apply response hardening headers with default-src, non-wildcard script-src, connect-src, img-src, frame-src, style-src, font-src, object-src, base-uri, and frame-ancestors in frontend/vercel.json; verification: manually parse the Content-Security-Policy value and confirm every required directive and listed runtime host is present.
- [x] 2.2 Verify the CSP blocks unknown script origins while preserving allowed production resources; verification: serve frontend/.output/public with the final CSP header, load / and /companies/2619/ in Chrome, and confirm GA4, AdSense, Nuxt Icon, and Nuxt application resources produce zero blocking CSP security log entries.

## 3. Production Diagnostics

- [x] 3.1 [P] Implement "Clean production diagnostics without changing user-facing fallback behavior" for AdSenseUnit so Production browser console SHALL not expose debug diagnostics from AdSense retry or unexpected-error paths while retry/fallback behavior remains unchanged; verification: code review confirms console.warn/error are removed or gated by import.meta.dev, and production browser console no longer shows AdSense diagnostics.
- [x] 3.2 [P] Implement "Clean production diagnostics without changing user-facing fallback behavior" for useStaticApi so static data toast/rethrow behavior remains active while StaticApi/useStaticApi diagnostics are absent in production; verification: code review confirms the known console.warn/error calls are removed or dev-gated, and a forced fetch failure path still triggers the existing user-facing error handling.
- [x] 3.3 [P] Implement "Clean production diagnostics without changing user-facing fallback behavior" for the company store so catalog fetch failure still clears loading state while production console output is suppressed; verification: code review confirms the known console.error is removed or dev-gated and the finally block still sets loading false.

## 4. DOM And Structured Data Safety

- [x] 4.1 [P] Implement External blank-target footer links SHALL prevent opener access for the footer donation and repository links; verification: generated HTML or component review confirms every footer external target="_blank" link has rel="noopener noreferrer".
- [x] 4.2 [P] Implement "Escape JSON-LD through a shared serializer" so JSON-LD structured data SHALL escape script breakout characters across WebSite, Organization, Company, and Breadcrumb schemas; verification: serializer inspection or generated HTML with a < payload confirms output contains \u003c and remains valid JSON.

## 5. Final Verification

- [x] 5.1 Run cd frontend && npm run generate after implementation; verification: command exits 0 and nitro.prerender.failOnError remains true.
- [x] 5.2 Inspect generated SSG output for CSP-relevant sources; verification: .output/public/index.html and one .output/public/companies/*/index.html document inline script classes, AdSense loader, Nuxt module script, JSON-LD, window.__NUXT__.config, and data-nuxt-data payload.
- [x] 5.3 Re-run production-like browser verification for "Production deployment SHALL apply response hardening headers"; verification: Chrome loads / and /companies/2619/ with final CSP, hasGtag is true, GA collect and AdSense resources are observed, AdSense iframes are created, and console/security logs contain no blocking CSP violations.
