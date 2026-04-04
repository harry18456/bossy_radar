## ADDED Requirements

### Requirement: Interceptor SHALL only scan 104 API responses

The interceptor SHALL only process response bodies from requests whose URL hostname ends with `.104.com.tw`. Response bodies from all other domains (analytics, tracking, ads CDN, etc.) SHALL NOT be scanned for custNo patterns.

#### Scenario: 104 API response contains custNo

- **WHEN** a fetch or XHR response is received from `www.104.com.tw`
- **THEN** the interceptor SHALL scan the response body for custNo patterns

#### Scenario: Third-party response contains custNo-like pattern

- **WHEN** a fetch or XHR response is received from a non-104 domain (e.g., `scarabresearch.com`, `emarsys.net`, `googletagmanager.com`)
- **THEN** the interceptor SHALL NOT scan the response body, even if it contains patterns matching custNo format

### Requirement: CustNo extraction SHALL use confidence-based priority

The interceptor SHALL assign a confidence level to each discovered custNo and allow higher-confidence sources to override lower-confidence ones. The confidence levels are:

- Priority 3 (highest): custNo extracted from a URL query parameter (`custno=`)
- Priority 2: custNo extracted from a structured JSON field in a response body (key matching `custNo` or `custno`)
- Priority 1 (lowest): custNo extracted from HTML scan or generic regex match

The interceptor SHALL NOT use a permanent lock (`dispatched` flag). A newly discovered custNo with equal or higher confidence SHALL override the current value.

#### Scenario: URL parameter overrides HTML scan

- **WHEN** the interceptor first discovers custNo `11111111` from an HTML scan (priority 1)
- **AND** later discovers custNo `22222222` from a URL parameter (priority 3)
- **THEN** the dispatched custNo SHALL be updated to `22222222`

#### Scenario: Same priority does not override

- **WHEN** the interceptor discovers custNo `11111111` from a URL parameter (priority 3)
- **AND** later discovers custNo `22222222` from another URL parameter (priority 3)
- **THEN** the dispatched custNo SHALL remain `11111111`

#### Scenario: Lower priority does not override higher

- **WHEN** the interceptor discovers custNo `11111111` from a URL parameter (priority 3)
- **AND** later discovers custNo `22222222` from an HTML scan (priority 1)
- **THEN** the dispatched custNo SHALL remain `11111111`

### Requirement: Invalid tax ID prefixes SHALL be rejected

The interceptor SHALL validate extracted tax IDs using the Taiwan Unified Business Number (UBN) check digit algorithm. A custNo whose first 8 digits fail the UBN validation SHALL NOT be dispatched as a tax ID.

#### Scenario: Valid UBN passes validation

- **WHEN** the interceptor extracts custNo `23225712xxx` (first 8 digits `23225712`)
- **THEN** `23225712` SHALL pass UBN validation and be dispatched as the tax ID

#### Scenario: Internal 104 prefix fails validation

- **WHEN** the interceptor extracts custNo `130000000116973` (first 8 digits `13000000`)
- **THEN** `13000000` SHALL fail UBN validation and SHALL NOT be dispatched as a tax ID

### Requirement: Tax ID match SHALL be cross-validated against page company name

When `main.js` matches a company via tax ID, it SHALL compare the matched catalog company name against the company name visible in the DOM. If neither name is a substring of the other, the tax ID match SHALL be discarded and the system SHALL fall back to name matching.

#### Scenario: Tax ID match consistent with DOM company name

- **WHEN** the tax ID matches catalog entry "元富證券股份有限公司"
- **AND** the DOM displays company name "元富證券股份有限公司"
- **THEN** the tax ID match SHALL be accepted

#### Scenario: Tax ID match inconsistent with DOM company name

- **WHEN** the tax ID matches catalog entry "元富證券股份有限公司"
- **AND** the DOM displays company name "新技術供應鏈與物流股份有限公司"
- **THEN** the tax ID match SHALL be discarded
- **AND** the system SHALL attempt name matching instead

#### Scenario: DOM company name not yet available

- **WHEN** the tax ID matches a catalog entry
- **AND** the DOM does not yet contain a company name (page still loading)
- **THEN** the tax ID match SHALL be accepted provisionally
- **AND** SHALL be re-validated when the company name becomes available
