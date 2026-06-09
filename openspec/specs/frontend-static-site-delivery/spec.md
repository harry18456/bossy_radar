# frontend-static-site-delivery Specification

## Purpose

TBD - created by archiving change 'frontend-ssg-correctness-and-headers'. Update Purpose after archive.

## Requirements

### Requirement: Frontend runtime SHALL default to static data mode

The frontend runtime SHALL use static data mode when NUXT_PUBLIC_DATA_MODE is unset or empty. The frontend runtime SHALL use dynamic API mode only when NUXT_PUBLIC_DATA_MODE is explicitly set to dynamic.

#### Scenario: Runtime mode is unset

- **WHEN** the frontend is built or served without NUXT_PUBLIC_DATA_MODE
- **THEN** useApi SHALL select the static API implementation

#### Scenario: Runtime mode is empty

- **WHEN** the frontend is built or served with NUXT_PUBLIC_DATA_MODE set to an empty string
- **THEN** useApi SHALL select the static API implementation

#### Scenario: Runtime mode is dynamic

- **WHEN** the frontend is built or served with NUXT_PUBLIC_DATA_MODE set to dynamic
- **THEN** useApi SHALL select the dynamic API implementation


<!-- @trace
source: frontend-ssg-correctness-and-headers
updated: 2026-06-09
code:
  - frontend/app/components/common/AppFooter.vue
  - .github/workflows/ci.yml
  - frontend/nuxt.config.ts
  - frontend/app/composables/useApi.ts
  - frontend/README.md
  - frontend/.env.example
  - frontend/CLAUDE.md
  - frontend/app/pages/companies/[id].vue
  - frontend/vercel.json
  - docs/REMEDIATION_PLAN.md
  - frontend/app/pages/index.vue
  - frontend/app/plugins/ga4.client.ts
  - frontend/app/components/home/IndustryEps.vue
-->

---
### Requirement: Static generation SHALL fail loud

Frontend static generation SHALL fail the command when a prerendered route fails. Continuous integration SHALL run frontend static generation so failed prerender output blocks a pull request or main branch build.

#### Scenario: Prerendered company route fails

- **WHEN** static generation encounters an error while prerendering a configured company route
- **THEN** the generation command SHALL exit non-zero

#### Scenario: Frontend CI runs

- **WHEN** the frontend CI job runs after dependency installation and Nuxt preparation
- **THEN** the job SHALL execute the static generation command


<!-- @trace
source: frontend-ssg-correctness-and-headers
updated: 2026-06-09
code:
  - frontend/app/components/common/AppFooter.vue
  - .github/workflows/ci.yml
  - frontend/nuxt.config.ts
  - frontend/app/composables/useApi.ts
  - frontend/README.md
  - frontend/.env.example
  - frontend/CLAUDE.md
  - frontend/app/pages/companies/[id].vue
  - frontend/vercel.json
  - docs/REMEDIATION_PLAN.md
  - frontend/app/pages/index.vue
  - frontend/app/plugins/ga4.client.ts
  - frontend/app/components/home/IndustryEps.vue
-->

---
### Requirement: Homepage leaderboards SHALL be prerendered into HTML

The generated homepage HTML SHALL contain real leaderboard content from the static leaderboards data file. The homepage SHALL NOT rely on ClientOnly fallback skeletons as the only rendered content for leaderboard sections.

#### Scenario: Homepage is generated with leaderboard data

- **WHEN** static generation reads frontend/public/data/leaderboards.json containing a company with code 6505
- **THEN** frontend/.output/public/index.html SHALL contain a link to /companies/6505

##### Example: leaderboard company link

- **GIVEN** leaderboards.json contains an all-time violation item with company_code 6505 and company_name Formosa Petrochemical Corporation
- **WHEN** static generation completes
- **THEN** index.html contains /companies/6505 and the company name from that leaderboard item

#### Scenario: Homepage generation renders leaderboard sections

- **WHEN** static generation completes for the homepage
- **THEN** the leaderboard sections SHALL contain rendered list rows instead of only animate-pulse skeleton placeholders


<!-- @trace
source: frontend-ssg-correctness-and-headers
updated: 2026-06-09
code:
  - frontend/app/components/common/AppFooter.vue
  - .github/workflows/ci.yml
  - frontend/nuxt.config.ts
  - frontend/app/composables/useApi.ts
  - frontend/README.md
  - frontend/.env.example
  - frontend/CLAUDE.md
  - frontend/app/pages/companies/[id].vue
  - frontend/vercel.json
  - docs/REMEDIATION_PLAN.md
  - frontend/app/pages/index.vue
  - frontend/app/plugins/ga4.client.ts
  - frontend/app/components/home/IndustryEps.vue
-->

---
### Requirement: Production deployment SHALL apply response hardening headers

The frontend Vercel deployment SHALL apply response hardening headers to public routes through a project configuration that is used by the documented deployment flow. The deployment SHALL expose X-Content-Type-Options, Referrer-Policy, Permissions-Policy, and either X-Frame-Options or an enforced Content-Security-Policy frame-ancestors directive. The deployment SHALL expose an enforced Content-Security-Policy baseline containing object-src 'none' and base-uri 'self'.

#### Scenario: Public route response is inspected

- **WHEN** an HTTP GET request is sent to the deployed homepage
- **THEN** the response SHALL include X-Content-Type-Options with value nosniff
- **THEN** the response SHALL include Referrer-Policy with value strict-origin-when-cross-origin
- **THEN** the response SHALL include Permissions-Policy
- **THEN** the response SHALL include X-Frame-Options with value SAMEORIGIN or a Content-Security-Policy frame-ancestors 'self' directive
- **THEN** the response SHALL include a Content-Security-Policy directive object-src 'none'
- **THEN** the response SHALL include a Content-Security-Policy directive base-uri 'self'

#### Scenario: Documented deployment flow uses frontend project configuration

- **WHEN** an operator follows the documented Vercel deployment flow
- **THEN** Vercel SHALL consume the committed frontend project configuration that defines headers for the generated static output


<!-- @trace
source: frontend-ssg-correctness-and-headers
updated: 2026-06-09
code:
  - frontend/app/components/common/AppFooter.vue
  - .github/workflows/ci.yml
  - frontend/nuxt.config.ts
  - frontend/app/composables/useApi.ts
  - frontend/README.md
  - frontend/.env.example
  - frontend/CLAUDE.md
  - frontend/app/pages/companies/[id].vue
  - frontend/vercel.json
  - docs/REMEDIATION_PLAN.md
  - frontend/app/pages/index.vue
  - frontend/app/plugins/ga4.client.ts
  - frontend/app/components/home/IndustryEps.vue
-->

---
### Requirement: Production browser console SHALL not expose debug diagnostics

Production browser execution SHALL NOT write debug diagnostics for GA4 initialization, dynamic API base URL selection, sitemap route loading, or IndustryEps data scanning. Development-only diagnostics SHALL be gated so they execute only in development mode.

#### Scenario: Production homepage executes

- **WHEN** the production homepage runs in a browser
- **THEN** the browser console SHALL NOT contain GA4 initialization messages
- **THEN** the browser console SHALL NOT contain IndustryEps data scanning messages

#### Scenario: Dynamic API mode runs in production

- **WHEN** the frontend runs in production with NUXT_PUBLIC_DATA_MODE set to dynamic
- **THEN** the browser console SHALL NOT contain the dynamic API base URL diagnostic


<!-- @trace
source: frontend-ssg-correctness-and-headers
updated: 2026-06-09
code:
  - frontend/app/components/common/AppFooter.vue
  - .github/workflows/ci.yml
  - frontend/nuxt.config.ts
  - frontend/app/composables/useApi.ts
  - frontend/README.md
  - frontend/.env.example
  - frontend/CLAUDE.md
  - frontend/app/pages/companies/[id].vue
  - frontend/vercel.json
  - docs/REMEDIATION_PLAN.md
  - frontend/app/pages/index.vue
  - frontend/app/plugins/ga4.client.ts
  - frontend/app/components/home/IndustryEps.vue
-->

---
### Requirement: Optional analytics and ads configuration SHALL fail closed

Missing optional GA4 or AdSense configuration SHALL skip the related script injection without publishing broken third-party request URLs.

#### Scenario: AdSense client ID is empty

- **WHEN** the frontend is generated with NUXT_PUBLIC_GOOGLE_ADSENSE_ID unset or empty
- **THEN** generated HTML SHALL NOT contain an adsbygoogle loader URL with client=undefined
- **THEN** generated HTML SHALL NOT contain an adsbygoogle loader URL with an empty client parameter

#### Scenario: GA4 ID is empty

- **WHEN** the production frontend runs with NUXT_PUBLIC_GA4_ID unset or empty
- **THEN** the GA4 plugin SHALL NOT inject a Google tag script

<!-- @trace
source: frontend-ssg-correctness-and-headers
updated: 2026-06-09
code:
  - frontend/app/components/common/AppFooter.vue
  - .github/workflows/ci.yml
  - frontend/nuxt.config.ts
  - frontend/app/composables/useApi.ts
  - frontend/README.md
  - frontend/.env.example
  - frontend/CLAUDE.md
  - frontend/app/pages/companies/[id].vue
  - frontend/vercel.json
  - docs/REMEDIATION_PLAN.md
  - frontend/app/pages/index.vue
  - frontend/app/plugins/ga4.client.ts
  - frontend/app/components/home/IndustryEps.vue
-->