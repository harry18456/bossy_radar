## MODIFIED Requirements

### Requirement: Production deployment SHALL apply response hardening headers

The frontend Vercel deployment SHALL apply response hardening headers to public routes through a project configuration that is used by the documented deployment flow. The deployment SHALL expose X-Content-Type-Options, Referrer-Policy, Permissions-Policy, and either X-Frame-Options or an enforced Content-Security-Policy frame-ancestors directive. The deployment SHALL expose an enforced Content-Security-Policy containing default-src, script-src, connect-src, img-src, frame-src, style-src, font-src, object-src, base-uri, and frame-ancestors directives. The CSP script-src directive SHALL restrict scripts to self and explicitly listed third-party origins required by the production frontend. The CSP script-src directive SHALL NOT contain * and SHALL NOT contain https: as a blanket source. If script-src contains 'unsafe-inline', the change design SHALL document the SSG constraint and residual risk.

#### Scenario: Public route response is inspected

- **WHEN** an HTTP GET request is sent to the deployed homepage
- **THEN** the response SHALL include X-Content-Type-Options with value nosniff
- **THEN** the response SHALL include Referrer-Policy with value strict-origin-when-cross-origin
- **THEN** the response SHALL include Permissions-Policy
- **THEN** the response SHALL include X-Frame-Options with value SAMEORIGIN or a Content-Security-Policy frame-ancestors 'self' directive
- **THEN** the response SHALL include a Content-Security-Policy directive default-src
- **THEN** the response SHALL include a Content-Security-Policy directive script-src
- **THEN** the response SHALL include a Content-Security-Policy directive connect-src
- **THEN** the response SHALL include a Content-Security-Policy directive img-src
- **THEN** the response SHALL include a Content-Security-Policy directive frame-src
- **THEN** the response SHALL include a Content-Security-Policy directive style-src
- **THEN** the response SHALL include a Content-Security-Policy directive font-src
- **THEN** the response SHALL include a Content-Security-Policy directive object-src 'none'
- **THEN** the response SHALL include a Content-Security-Policy directive base-uri 'self'

#### Scenario: CSP script policy is inspected

- **WHEN** the deployed homepage Content-Security-Policy header is parsed
- **THEN** the script-src directive SHALL contain 'self'
- **THEN** the script-src directive SHALL contain at least one explicit third-party origin needed by the production frontend
- **THEN** the script-src directive SHALL NOT contain *
- **THEN** the script-src directive SHALL NOT contain https:

#### Scenario: Production browser loads analytics and ads under CSP

- **WHEN** the generated homepage and one generated company page are loaded in a production browser with the deployed CSP
- **THEN** the Nuxt application SHALL hydrate without a CSP violation that blocks application scripts
- **THEN** GA4 SHALL load its Google tag script from an allowed origin
- **THEN** GA4 SHALL send collect requests to an allowed analytics origin
- **THEN** AdSense SHALL load its loader/runtime scripts from allowed origins
- **THEN** AdSense SHALL create frames from allowed frame origins when ad slots are eligible to load
- **THEN** the browser security log SHALL contain no blocking CSP violations for GA4, AdSense, Nuxt Icon, or Nuxt application resources

#### Scenario: Documented deployment flow uses frontend project configuration

- **WHEN** an operator follows the documented Vercel deployment flow
- **THEN** Vercel SHALL consume the committed frontend project configuration that defines headers for the generated static output

---

### Requirement: Production browser console SHALL not expose debug diagnostics

Production browser execution SHALL NOT write debug diagnostics for GA4 initialization, dynamic API base URL selection, sitemap route loading, IndustryEps data scanning, AdSense retry/error paths, static API fetch fallback/error paths, or company catalog fetch failures. Development-only diagnostics SHALL be gated so they execute only in development mode.

#### Scenario: Production homepage executes

- **WHEN** the production homepage runs in a browser
- **THEN** the browser console SHALL NOT contain GA4 initialization messages
- **THEN** the browser console SHALL NOT contain IndustryEps data scanning messages
- **THEN** the browser console SHALL NOT contain AdSense retry diagnostics
- **THEN** the browser console SHALL NOT contain AdSense unexpected error diagnostics

#### Scenario: Dynamic API mode runs in production

- **WHEN** the frontend runs in production with NUXT_PUBLIC_DATA_MODE set to dynamic
- **THEN** the browser console SHALL NOT contain the dynamic API base URL diagnostic

#### Scenario: Static API fetch fails in production

- **WHEN** a production static API data request fails
- **THEN** the user-facing static data error handling SHALL remain active
- **THEN** the browser console SHALL NOT contain StaticApi or useStaticApi fetch fallback diagnostics

#### Scenario: Company catalog fetch fails in production

- **WHEN** a production company catalog fetch fails in the company store
- **THEN** the store SHALL finish its loading state
- **THEN** the browser console SHALL NOT contain a company catalog fetch failure diagnostic

## ADDED Requirements

### Requirement: External blank-target footer links SHALL prevent opener access

Footer links that navigate to external origins in a new browsing context SHALL include rel="noopener noreferrer".

#### Scenario: Footer external links are rendered

- **WHEN** the production footer renders an external link with target="_blank"
- **THEN** the link SHALL include rel="noopener noreferrer"

---

### Requirement: JSON-LD structured data SHALL escape script breakout characters

Structured data injected as application/ld+json SHALL serialize schema objects through a JSON-LD serializer that escapes every literal < character as \u003c before passing the string to the head manager. The escaped output MUST remain valid JSON.

#### Scenario: Company structured data contains a less-than character

- **WHEN** company structured data is serialized with a name value containing <script>
- **THEN** the serialized JSON-LD SHALL contain \u003cscript>
- **THEN** the serialized JSON-LD SHALL NOT contain the literal substring <script>
- **THEN** JSON.parse SHALL parse the serialized JSON-LD successfully

##### Example: less-than escaping

- **GIVEN** a company name value of Alpha <script>alert(1)</script>
- **WHEN** the company schema is serialized for application/ld+json
- **THEN** the output contains Alpha \u003cscript>alert(1)\u003c/script>
