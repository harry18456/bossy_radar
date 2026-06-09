## Context

Production is currently a Vercel-hosted SSG site. The frontend still defaults to dynamic API mode when NUXT_PUBLIC_DATA_MODE is unset, the generated homepage contains only ClientOnly fallback skeletons for leaderboard sections, and nitro prerender is configured to continue after route failures. Live reconnaissance also found missing response hardening headers and production console output from GA4 and the home EPS leaderboard.

The existing README deployment command deploys frontend/.output/public as the Vercel project root. That path-based deployment can bypass a committed project-level vercel.json unless the deploy entrypoint is changed. Header work therefore includes the deployment contract, not only the header file.

## Goals / Non-Goals

**Goals:**

- Default the frontend to static data mode when no explicit runtime mode is configured.
- Make SSG generation fail-loud locally and in CI when prerendered routes fail.
- Render homepage leaderboards during SSG so generated HTML contains real leaderboard rows and company links.
- Add production response hardening headers through a Vercel configuration that is actually used by the deployment flow.
- Remove production console output while keeping intentional development diagnostics behind import.meta.dev.
- Prevent AdSense script injection when the ad client ID is empty.
- Update frontend docs and env examples so local development and deployment instructions match the new defaults.

**Non-Goals:**

- Do not change watchlist yearly summary loading; that belongs to frontend-watchlist-static-profile-loading.
- Do not expose or harden FastAPI endpoints; backend API hardening is a separate public API gate.
- Do not implement strict nonce-based CSP in this change. The current SSG deployment does not generate per-response nonces, and AdSense officially documents strict CSP as nonce-based work.
- Do not add frontend unit or browser test frameworks. Use existing lint, generate, and artifact inspection commands.
- Do not redesign the homepage leaderboard UI beyond making existing components render during SSG.

## Decisions

### Use static mode as the default and require explicit dynamic mode

The runtime config will resolve NUXT_PUBLIC_DATA_MODE to static unless it is explicitly set to dynamic. This matches the production architecture and the checked-in local .env value, and it prevents clean checkouts or CI builds from silently targeting localhost:8000.

Alternative considered: keep dynamic as the default and update only production env. Rejected because the failure mode remains silent for clean checkouts, new CI, and contributors without the private .env file.

### Make the Vercel project root explicit for headers

The Vercel configuration will live in frontend/vercel.json and define the generated static output as the output directory. Documentation will instruct deploys from the frontend project root so Vercel consumes this configuration and applies headers to the published static files.

Alternative considered: add a root-level vercel.json while keeping the README command that deploys frontend/.output/public directly. Rejected because the specified path can become the project root for that deploy, leaving the root config unused.

### Use an enforced minimal CSP baseline, not strict CSP

The first CSP will enforce only low-risk directives that do not block existing GA4 or AdSense loading: object-src 'none', base-uri 'self', and frame-ancestors 'self'. Other headers will carry the immediate hardening: X-Content-Type-Options, Referrer-Policy, X-Frame-Options, and Permissions-Policy.

Alternative considered: domain allowlist CSP for all scripts, connections, images, frames, and styles. Rejected because AdSense documents that its domains can change and strict CSP requires nonce-based integration. A broad allowlist would be brittle and could break ads without warning.

### Render homepage leaderboards server-side using the existing static API

The homepage will allow useAsyncData for leaderboards to run during prerender and will remove ClientOnly wrappers around the five leaderboard cards. The home leaderboard components use props, computed state, refs, watches, and NuxtLink; they do not depend on browser-only APIs.

Alternative considered: leave ClientOnly and add crawler-only fallback markup. Rejected because it duplicates presentation and keeps the production user flow dependent on client-side hydration for primary homepage content.

### Keep diagnostics development-only

Production console output from GA4 initialization, dynamic API mode, sitemap route loading, and IndustryEps data scanning will be removed or gated by import.meta.dev. Build-time warnings for missing required static data remain allowed because they are operator signals, not browser console noise.

Alternative considered: remove all console usage. Rejected because missing build inputs and development analytics debugging are useful signals when they are not shipped to production browsers.

## Implementation Contract

**Behavior:**

- A generated production homepage contains leaderboard company links such as /companies/6505 from frontend/public/data/leaderboards.json and does not render only skeleton placeholders for the leaderboard sections.
- A frontend build with no NUXT_PUBLIC_DATA_MODE configured uses static data mode. Dynamic mode remains available only when NUXT_PUBLIC_DATA_MODE is explicitly set to dynamic.
- Static generation exits non-zero when prerendered routes fail.
- CI runs the frontend static generation path after installing frontend dependencies and preparing Nuxt.
- Production browser console output does not include GA4 initialization messages, useApi dynamic mode messages, sitemap route loading messages, or IndustryEps data dumps.
- When NUXT_PUBLIC_GOOGLE_ADSENSE_ID is empty, the generated HTML does not contain an adsbygoogle loader URL with client=undefined or an empty client value.
- Deployed frontend responses include response hardening headers from the Vercel configuration. Verification must inspect actual HTTP response headers from a Vercel preview or production URL, not only the committed config file.

**Interface / configuration shape:**

- NUXT_PUBLIC_DATA_MODE accepts static or dynamic. Empty or unset resolves to static.
- frontend/vercel.json is the Vercel project configuration for the frontend deployment. It defines the output directory for generated static files and a wildcard headers rule for public routes.
- frontend/.env.example documents NUXT_PUBLIC_DATA_MODE=static.
- frontend/README.md and frontend/CLAUDE.md document the static-first local and deployment flow.

**Failure modes:**

- Missing frontend/public/data/company-catalog.json during generate remains a build/operator problem. The build must not silently publish a partial site if required prerendered routes fail.
- Missing optional GA4 or AdSense IDs must skip the related script injection without breaking the site.
- Strict CSP is intentionally absent. The presence of a minimal CSP baseline must not be interpreted as completion of nonce-based CSP hardening.

**Acceptance criteria:**

- npm run lint succeeds in frontend.
- npm run generate succeeds in frontend with the checked-in static data.
- The generated index HTML under frontend/.output/public contains at least one /companies/ leaderboard link from leaderboards.json and does not contain five ClientOnly skeleton cards as the only leaderboard content.
- CI workflow includes a frontend generation step that would fail the pull request when generation fails.
- A Vercel preview or production deployment made from the documented frontend project-root flow returns X-Content-Type-Options, Referrer-Policy, X-Frame-Options or equivalent CSP frame-ancestors, Permissions-Policy, and Content-Security-Policy headers.

**Scope boundaries:**

- In scope: frontend runtime config, Nuxt prerender settings, homepage leaderboard SSR behavior, Vercel frontend deployment config, frontend CI, frontend docs, and production console cleanup.
- Out of scope: watchlist loading performance, backend ETL/export correctness, browser extension security, runtime schema validation for static JSON, consent banner implementation, and strict nonce CSP.

## Risks / Trade-offs

- [Risk] Vercel deployment config is committed but not used by the actual deploy command. -> Mitigation: update deployment docs and require preview/production header verification as part of the task list.
- [Risk] Minimal CSP provides less protection than strict CSP. -> Mitigation: enforce safe low-risk directives now and explicitly leave strict nonce CSP as a separate security change.
- [Risk] Removing ClientOnly from homepage cards exposes hidden SSR assumptions. -> Mitigation: inspect all home leaderboard components for browser-only APIs and require npm run generate to pass.
- [Risk] CI generate increases runtime and may be sensitive to static data size. -> Mitigation: keep it in the frontend job after npm ci and treat the extra runtime as the cost of catching broken SSG output before deployment.
- [Risk] Static default changes contributor expectations for local dev. -> Mitigation: update .env.example, README, and CLAUDE.md so dynamic API work requires explicit NUXT_PUBLIC_DATA_MODE=dynamic.

## Migration Plan

1. Update frontend configuration and docs so static mode and Vercel project-root deployment are the default path.
2. Update homepage data fetching and remove unnecessary ClientOnly wrappers.
3. Add or update Vercel headers configuration.
4. Run frontend lint and generate locally.
5. Deploy a Vercel preview using the documented flow and inspect response headers.
6. If deployment headers are absent, roll back to the previous deployment command and do not promote the change until the deployment entrypoint is corrected.

## Open Questions

None.
