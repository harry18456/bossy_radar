# backend-etl-bounded-retries Specification

## Purpose

TBD - created by archiving change 'backend-etl-fail-loud-bounded'. Update Purpose after archive.

## Requirements

### Requirement: Retry loops SHALL have an absolute attempt ceiling

The detail-scraper fetch retry SHALL terminate within a bounded number of attempts even when configured for infinite retries. With retries set to a negative value, the total attempts SHALL NOT exceed 50; with a non-negative retries value, behavior SHALL remain retries plus one attempts.

#### Scenario: Infinite retries against a permanently failing host

- **WHEN** _fetch_with_retry runs with retries -1 and every request fails
- **THEN** the function SHALL stop after at most 50 attempts
- **THEN** the function SHALL return a failure result instead of looping forever

##### Example: attempt ceiling

| retries | outcome on permanent failure |
| ------- | ---------------------------- |
| 3       | stops after 4 attempts       |
| 0       | stops after 1 attempt        |
| -1      | stops after at most 50 attempts |


<!-- @trace
source: backend-etl-fail-loud-bounded
updated: 2026-06-13
code:
  - backend/app/services/export_service.py
  - backend/app/services/company_detail_scraper.py
  - backend/app/services/mops_scraper.py
  - backend/app/services/sync_report.py
  - docs/REMEDIATION_PLAN.md
  - backend/app/services/company_service.py
  - backend/app/cli/main.py
  - backend/app/services/violation_service.py
  - backend/CLAUDE.md
  - docs/BACKEND_AUDIT.md
tests:
  - backend/tests/test_mops_scraper.py
  - backend/tests/test_sync_fail_loud.py
  - backend/tests/test_bounded_retries.py
-->

---
### Requirement: Consecutive maintenance pages SHALL trip a circuit breaker

The company detail sync SHALL stop issuing new requests after 5 consecutive maintenance-page detections and SHALL report the run as circuit-broken. The CLI SHALL exit non-zero when the circuit breaker trips.

#### Scenario: Sustained rate limiting

- **WHEN** 5 consecutive companies in a row return MOPS maintenance pages
- **THEN** the sync SHALL NOT issue further requests in this run
- **THEN** the run summary SHALL state that the circuit breaker tripped
- **THEN** the CLI SHALL exit with a non-zero code


<!-- @trace
source: backend-etl-fail-loud-bounded
updated: 2026-06-13
code:
  - backend/app/services/export_service.py
  - backend/app/services/company_detail_scraper.py
  - backend/app/services/mops_scraper.py
  - backend/app/services/sync_report.py
  - docs/REMEDIATION_PLAN.md
  - backend/app/services/company_service.py
  - backend/app/cli/main.py
  - backend/app/services/violation_service.py
  - backend/CLAUDE.md
  - docs/BACKEND_AUDIT.md
tests:
  - backend/tests/test_mops_scraper.py
  - backend/tests/test_sync_fail_loud.py
  - backend/tests/test_bounded_retries.py
-->

---
### Requirement: Documentation SHALL NOT recommend unbounded retries

Project documentation SHALL NOT present a negative retries value as the recommended invocation; it SHALL note that negative values are clamped by the attempt ceiling.

#### Scenario: Reading the backend usage docs

- **WHEN** the backend usage documentation shows the sync-company-details example
- **THEN** the example SHALL use a finite retries value

<!-- @trace
source: backend-etl-fail-loud-bounded
updated: 2026-06-13
code:
  - backend/app/services/export_service.py
  - backend/app/services/company_detail_scraper.py
  - backend/app/services/mops_scraper.py
  - backend/app/services/sync_report.py
  - docs/REMEDIATION_PLAN.md
  - backend/app/services/company_service.py
  - backend/app/cli/main.py
  - backend/app/services/violation_service.py
  - backend/CLAUDE.md
  - docs/BACKEND_AUDIT.md
tests:
  - backend/tests/test_mops_scraper.py
  - backend/tests/test_sync_fail_loud.py
  - backend/tests/test_bounded_retries.py
-->