## Why

Production is a Vercel-hosted static site, but the frontend still defaults to dynamic API mode, allows prerender failures to ship, and renders the homepage leaderboards as client-only skeletons. Live reconnaissance also confirmed missing security headers and production debug logging, so the current release path can silently publish incomplete HTML and weaker response protections.

## What Changes

- Make static data mode the default frontend runtime mode unless dynamic API mode is explicitly configured.
- Make static generation fail-loud when prerendered routes fail, and add CI coverage that runs the static generation path.
- Render homepage leaderboards during SSG so generated index HTML contains real leaderboard company links instead of only skeleton placeholders.
- Add deployable response headers for static production assets and align the Vercel deployment entrypoint so those headers actually apply to the published output.
- Remove production console logging from GA4, dynamic API mode, sitemap generation, and home leaderboard components while preserving development-only diagnostics where useful.
- Guard AdSense script injection so missing ad client configuration does not publish a client=undefined network request.
- Record a CSP baseline that does not claim strict nonce-based CSP in this change; strict CSP remains separate work because the current SSG deployment cannot generate per-response nonces.

## Capabilities

### New Capabilities

- frontend-static-site-delivery: Defines SSG release behavior, static data defaults, homepage prerender content, production response headers, and production logging constraints for the frontend site.

### Modified Capabilities

(none)

## Impact

- Affected code:
  - Modified: frontend/nuxt.config.ts
  - Modified: frontend/app/pages/index.vue
  - Modified: frontend/app/plugins/ga4.client.ts
  - Modified: frontend/app/composables/useApi.ts
  - Modified: frontend/app/components/home/IndustryEps.vue
  - Modified: frontend/.env.example
  - Modified: frontend/README.md
  - Modified: frontend/CLAUDE.md
  - Modified: .github/workflows/ci.yml
  - New: frontend/vercel.json
  - Removed: none
- Affected systems:
  - Vercel static deployment flow for frontend output
  - GitHub Actions frontend CI
  - Production HTTP response headers for the public site
