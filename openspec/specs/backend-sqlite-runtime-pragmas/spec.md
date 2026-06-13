# backend-sqlite-runtime-pragmas Specification

## Purpose

TBD - created by archiving change 'backend-db-integrity-foundation'. Update Purpose after archive.

## Requirements

### Requirement: SQLite connections SHALL enforce runtime PRAGMAs

Every connection to the main and archive engines SHALL set journal_mode to WAL, busy_timeout to 5000 milliseconds, and foreign_keys to ON. These PRAGMAs SHALL be applied automatically on connect, for both engines.

#### Scenario: A new connection reports the PRAGMAs

- **WHEN** a connection to either engine is opened
- **THEN** PRAGMA journal_mode SHALL report wal
- **THEN** PRAGMA busy_timeout SHALL report 5000
- **THEN** PRAGMA foreign_keys SHALL report 1

#### Scenario: Foreign keys are enforced

- **WHEN** a row is inserted with a company_code that does not exist in the company table
- **THEN** the insert SHALL be rejected by the database

#### Scenario: Null foreign keys remain allowed

- **WHEN** a row is inserted with a null company_code
- **THEN** the insert SHALL be accepted

<!-- @trace
source: backend-db-integrity-foundation
updated: 2026-06-13
code:
  - backend/app/models/non_manager_salary.py
  - backend/app/services/violation_service.py
  - backend/app/models/salary_adjustment.py
  - backend/app/models/environmental_violation.py
  - backend/uv.lock
  - backend/migrations/versions/0002_unique_constraints_and_dedup_keys.py
  - backend/migrations/script.py.mako
  - docs/BACKEND_AUDIT.md
  - backend/migrations/versions/0001_baseline.py
  - backend/pyproject.toml
  - backend/app/services/db_upsert.py
  - backend/app/services/dedup.py
  - backend/app/services/environmental_service.py
  - backend/CLAUDE.md
  - backend/migrations/env.py
  - backend/app/models/welfare_policy.py
  - docs/REMEDIATION_PLAN.md
  - backend/alembic.ini
  - backend/app/models/violation.py
  - backend/app/services/company_service.py
  - backend/app/services/mops_scraper.py
  - backend/app/db/session.py
  - backend/app/models/employee_benefit.py
tests:
  - backend/tests/test_migrations.py
  - backend/tests/test_idempotent_upsert.py
  - backend/tests/test_db_pragmas.py
-->