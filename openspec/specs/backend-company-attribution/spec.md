# backend-company-attribution Specification

## Purpose

TBD - created by archiving change 'backend-violation-attribution-correctness'. Update Purpose after archive.

## Requirements

### Requirement: Company code exact match takes highest priority

The matcher SHALL resolve a record to a listed company by exact company code when the source provides a company code (such as MOPS raw company code) that matches a company in the master list. This match SHALL take priority over tax ID and name-based matching.

#### Scenario: MOPS record with a known company code

- **WHEN** a MOPS record carries a raw company code that exists in the company master
- **THEN** the matcher SHALL link the record to that company code without consulting name-based rules


<!-- @trace
source: backend-violation-attribution-correctness
updated: 2026-06-14
code:
  - frontend/app/pages/data-sources.vue
  - backend/scripts/archive_recall_probe.py
  - frontend/DATA.md
  - backend/app/services/mops_scraper.py
  - backend/scripts/reattribute_cleanup.py
  - backend/app/services/violation_service.py
  - backend/scripts/analyze_attribution_impact.py
  - backend/app/services/company_matcher.py
tests:
  - backend/tests/test_mops_scraper.py
  - backend/tests/test_company_matcher.py
  - backend/tests/test_idempotent_upsert.py
  - backend/tests/test_company_attribution.py
  - backend/tests/test_environmental_attribution.py
-->

---
### Requirement: Tax ID exact match precedes name matching

The matcher SHALL resolve a record by exact unified business number (tax ID) when the tax ID is present and found in the master list, before attempting any name-based match.

#### Scenario: Environmental record with a known tax ID

- **WHEN** an environmental record carries a tax ID present in the company master
- **THEN** the matcher SHALL link to that company by tax ID


<!-- @trace
source: backend-violation-attribution-correctness
updated: 2026-06-14
code:
  - frontend/app/pages/data-sources.vue
  - backend/scripts/archive_recall_probe.py
  - frontend/DATA.md
  - backend/app/services/mops_scraper.py
  - backend/scripts/reattribute_cleanup.py
  - backend/app/services/violation_service.py
  - backend/scripts/analyze_attribution_impact.py
  - backend/app/services/company_matcher.py
tests:
  - backend/tests/test_mops_scraper.py
  - backend/tests/test_company_matcher.py
  - backend/tests/test_idempotent_upsert.py
  - backend/tests/test_company_attribution.py
  - backend/tests/test_environmental_attribution.py
-->

---
### Requirement: Deterministic longest-prefix branch matching

When no exact code, tax ID, or full-name match exists, the matcher SHALL evaluate branch-prefix candidates (companies whose full name is a prefix of the input) and SHALL select the candidate with the longest matching prefix. The result SHALL NOT depend on the order in which companies are loaded from the database; identical input SHALL yield identical attribution across runs and database rebuilds.

#### Scenario: Longest prefix wins deterministically

- **WHEN** an input name is a prefix-match of multiple companies of differing full-name length
- **THEN** the matcher SHALL link to the company with the longest matching full name
- **AND** the same input SHALL produce the same result regardless of database row order


<!-- @trace
source: backend-violation-attribution-correctness
updated: 2026-06-14
code:
  - frontend/app/pages/data-sources.vue
  - backend/scripts/archive_recall_probe.py
  - frontend/DATA.md
  - backend/app/services/mops_scraper.py
  - backend/scripts/reattribute_cleanup.py
  - backend/app/services/violation_service.py
  - backend/scripts/analyze_attribution_impact.py
  - backend/app/services/company_matcher.py
tests:
  - backend/tests/test_mops_scraper.py
  - backend/tests/test_company_matcher.py
  - backend/tests/test_idempotent_upsert.py
  - backend/tests/test_company_attribution.py
  - backend/tests/test_environmental_attribution.py
-->

---
### Requirement: Trailing annotations after a full-name prefix do not change attribution

When a company full name is a prefix of the input and the input is longer, the matcher SHALL link to that company regardless of what follows the prefix — a bracketed representative name, a site or branch descriptor, or a legal-entity suffix that the master name omits. The trailing remainder SHALL NOT be required to match any whitelist, and the remainder alone SHALL NOT cause rejection. Attribution is decided solely by the longest company-full-name prefix.

#### Scenario: Full name followed by a bracketed representative

- **WHEN** the input is a company full name immediately followed by a bracketed personal name
- **THEN** the matcher SHALL link to that company

#### Scenario: Master name omits a legal-entity suffix the input includes

- **WHEN** the master company name omits a legal-entity suffix that the input includes, yet the master name is still a prefix of the input
- **THEN** the matcher SHALL link to that company

##### Example: trailing annotations resolve to the same company

| Input | Master name (code) | Result |
| --- | --- | --- |
| 南山人壽保險股份有限公司(尹崇堯) | 南山人壽保險股份有限公司 (5874) | link 5874 |
| 臺灣土地銀行股份有限公司(何英明) | 臺灣土地銀行 (5857) | link 5857 |
| 台灣電力股份有限公司南區營業處 | 台灣電力股份有限公司 (9963) | link 9963 |


<!-- @trace
source: backend-violation-attribution-correctness
updated: 2026-06-14
code:
  - frontend/app/pages/data-sources.vue
  - backend/scripts/archive_recall_probe.py
  - frontend/DATA.md
  - backend/app/services/mops_scraper.py
  - backend/scripts/reattribute_cleanup.py
  - backend/app/services/violation_service.py
  - backend/scripts/analyze_attribution_impact.py
  - backend/app/services/company_matcher.py
tests:
  - backend/tests/test_mops_scraper.py
  - backend/tests/test_company_matcher.py
  - backend/tests/test_idempotent_upsert.py
  - backend/tests/test_company_attribution.py
  - backend/tests/test_environmental_attribution.py
-->

---
### Requirement: Reject ambiguous prefix matches when companies tie

The matcher SHALL NOT link when two or more distinct company codes share the longest matching prefix; such ambiguous inputs SHALL be archived rather than guessed. This keeps attribution deterministic and independent of database row order.

#### Scenario: Multiple companies share the longest prefix

- **WHEN** two or more distinct company codes tie for the longest matching prefix
- **THEN** the matcher SHALL NOT link and the record SHALL be archived


<!-- @trace
source: backend-violation-attribution-correctness
updated: 2026-06-14
code:
  - frontend/app/pages/data-sources.vue
  - backend/scripts/archive_recall_probe.py
  - frontend/DATA.md
  - backend/app/services/mops_scraper.py
  - backend/scripts/reattribute_cleanup.py
  - backend/app/services/violation_service.py
  - backend/scripts/analyze_attribution_impact.py
  - backend/app/services/company_matcher.py
tests:
  - backend/tests/test_mops_scraper.py
  - backend/tests/test_company_matcher.py
  - backend/tests/test_idempotent_upsert.py
  - backend/tests/test_company_attribution.py
  - backend/tests/test_environmental_attribution.py
-->

---
### Requirement: No automatic linkage from bare personal names

The matcher SHALL NOT automatically link a record to a listed company solely because the record company-name field equals that company chairman or representative name. Bare personal names without a company-full-name prefix SHALL be archived.

#### Scenario: Bare personal name equal to a chairman

- **WHEN** the input company-name field is a bare personal name that equals a listed company chairman
- **THEN** the matcher SHALL NOT link and the record SHALL be archived

##### Example: bare names archived, not mis-attributed

| Input | Note | Result |
| --- | --- | --- |
| 劉正忠 | chairman of 4171 | archive |
| 陳國寶 | chairman of 2354 | archive |


<!-- @trace
source: backend-violation-attribution-correctness
updated: 2026-06-14
code:
  - frontend/app/pages/data-sources.vue
  - backend/scripts/archive_recall_probe.py
  - frontend/DATA.md
  - backend/app/services/mops_scraper.py
  - backend/scripts/reattribute_cleanup.py
  - backend/app/services/violation_service.py
  - backend/scripts/analyze_attribution_impact.py
  - backend/app/services/company_matcher.py
tests:
  - backend/tests/test_mops_scraper.py
  - backend/tests/test_company_matcher.py
  - backend/tests/test_idempotent_upsert.py
  - backend/tests/test_company_attribution.py
  - backend/tests/test_environmental_attribution.py
-->

---
### Requirement: No fuzzy or normalized recall that risks mis-attribution

The matcher SHALL NOT link a non-listed entity to a listed company by normalizing both down to a shared short form. Inputs that only match a listed company after aggressive normalization SHALL remain archived.

#### Scenario: A different limited company must not map to a listed company

- **WHEN** a non-listed limited company would only match a listed company by reducing both names to a bare short name
- **THEN** the matcher SHALL NOT link and the record SHALL be archived

##### Example: tempting but wrong normalization

| Input | Tempting target | Result | Why |
| --- | --- | --- | --- |
| 廣達有限公司(曾坤升) | 廣達電腦 (2382) | archive | 曾坤升 is not the 2382 chairman; different entity |


<!-- @trace
source: backend-violation-attribution-correctness
updated: 2026-06-14
code:
  - frontend/app/pages/data-sources.vue
  - backend/scripts/archive_recall_probe.py
  - frontend/DATA.md
  - backend/app/services/mops_scraper.py
  - backend/scripts/reattribute_cleanup.py
  - backend/app/services/violation_service.py
  - backend/scripts/analyze_attribution_impact.py
  - backend/app/services/company_matcher.py
tests:
  - backend/tests/test_mops_scraper.py
  - backend/tests/test_company_matcher.py
  - backend/tests/test_idempotent_upsert.py
  - backend/tests/test_company_attribution.py
  - backend/tests/test_environmental_attribution.py
-->

---
### Requirement: Single shared matcher across all ETL sources

Labor violations, environmental violations, and MOPS ingestion SHALL all resolve company attribution through one shared matcher implementation. The codebase SHALL NOT contain duplicate inline matching logic per source.

#### Scenario: Labor and MOPS use the shared matcher

- **WHEN** labor or MOPS ingestion needs to attribute a record to a company
- **THEN** it SHALL call the shared matcher rather than an inline copy


<!-- @trace
source: backend-violation-attribution-correctness
updated: 2026-06-14
code:
  - frontend/app/pages/data-sources.vue
  - backend/scripts/archive_recall_probe.py
  - frontend/DATA.md
  - backend/app/services/mops_scraper.py
  - backend/scripts/reattribute_cleanup.py
  - backend/app/services/violation_service.py
  - backend/scripts/analyze_attribution_impact.py
  - backend/app/services/company_matcher.py
tests:
  - backend/tests/test_mops_scraper.py
  - backend/tests/test_company_matcher.py
  - backend/tests/test_idempotent_upsert.py
  - backend/tests/test_company_attribution.py
  - backend/tests/test_environmental_attribution.py
-->

---
### Requirement: Unmatched records are archived, not dropped

When the matcher returns no confident match, the ingesting service SHALL store the record in the archive database, preserving the raw record, rather than dropping it or attaching it to the main database.

#### Scenario: No confident match

- **WHEN** the matcher returns no match for a record
- **THEN** the record SHALL be written to the archive database

<!-- @trace
source: backend-violation-attribution-correctness
updated: 2026-06-14
code:
  - frontend/app/pages/data-sources.vue
  - backend/scripts/archive_recall_probe.py
  - frontend/DATA.md
  - backend/app/services/mops_scraper.py
  - backend/scripts/reattribute_cleanup.py
  - backend/app/services/violation_service.py
  - backend/scripts/analyze_attribution_impact.py
  - backend/app/services/company_matcher.py
tests:
  - backend/tests/test_mops_scraper.py
  - backend/tests/test_company_matcher.py
  - backend/tests/test_idempotent_upsert.py
  - backend/tests/test_company_attribution.py
  - backend/tests/test_environmental_attribution.py
-->