# backend-etl-fail-loud Specification

## Purpose

TBD - created by archiving change 'backend-etl-fail-loud-bounded'. Update Purpose after archive.

## Requirements

### Requirement: Sync commands SHALL exit non-zero when any source fails

The sync-companies, sync-violations, and sync-mops CLI commands SHALL track per-source success and failure, including download failures and sync exceptions, and SHALL exit with a non-zero code when at least one source failed. Remaining sources SHALL still be attempted after one source fails.

#### Scenario: One violation source fails to download

- **WHEN** sync-violations runs and one source's download fails while others succeed
- **THEN** the command SHALL attempt every requested source
- **THEN** the command SHALL exit with code 1

#### Scenario: All sources succeed

- **WHEN** every requested source downloads and syncs successfully
- **THEN** the command SHALL exit with code 0


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
### Requirement: Sync commands SHALL print a per-source summary

After processing, sync commands SHALL print a summary listing every source with its written row count and skipped row count, and failed sources SHALL be marked with their error summary.

#### Scenario: Summary after a partial failure

- **WHEN** sync-violations finishes with one failed source and one successful source
- **THEN** the output SHALL contain one line per source
- **THEN** the failed source line SHALL include a failure marker and an error summary
- **THEN** the successful source line SHALL include its written and skipped row counts


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
### Requirement: Skipped parse rows SHALL be logged and counted

When a row is dropped during parsing or record construction, the system SHALL log a warning identifying the source and row, and the drop SHALL increment the skipped counter reported in the summary. Silent except-pass row handling SHALL NOT remain in the violation parsing loop.

#### Scenario: A malformed row is dropped

- **WHEN** one row in a violation source raises during record construction
- **THEN** a warning SHALL be logged for that row with the source name
- **THEN** the source's skipped count SHALL increase by one
- **THEN** the remaining rows SHALL still be processed

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