# backend-db-uniqueness Specification

## Purpose

TBD - created by archiving change 'backend-db-integrity-foundation'. Update Purpose after archive.

## Requirements

### Requirement: Natural keys SHALL be unique at the database layer

Each data table SHALL declare a UNIQUE constraint over its natural key: the MOPS tables over (raw_company_code, year, market_type); the violation table over its dedup key; the environmental violation table over its dedup key. Inserting a row whose natural key already exists SHALL update the existing row rather than create a duplicate.

#### Scenario: Re-upserting a MOPS row is idempotent

- **WHEN** the same (raw_company_code, year, market_type) record is upserted twice
- **THEN** the table SHALL contain exactly one row for that key
- **THEN** the second upsert SHALL update the existing row

#### Scenario: Re-upserting a violation is idempotent

- **WHEN** the same violation record is upserted twice
- **THEN** the violation table SHALL contain exactly one row for that record


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

---
### Requirement: Empty disposition numbers SHALL use a deterministic dedup key

A violation or environmental violation whose disposition number is empty or null SHALL be deduplicated by a deterministic synthetic key derived from its identifying fields, so repeated syncs do not re-insert it. The synthetic key SHALL be computed identically by the application upsert and by the migration backfill.

#### Scenario: Empty-disposition violations dedupe

- **WHEN** two violations with the same company name, penalty date, law article, fine amount, and data source but empty disposition numbers are upserted
- **THEN** the table SHALL contain exactly one row for them

##### Example: synthetic key reuse

- **GIVEN** a violation with an empty disposition number and fixed identifying fields
- **WHEN** its dedup key is computed by the application and by the migration backfill
- **THEN** both SHALL produce the same key value

#### Scenario: Non-empty disposition keeps natural key

- **WHEN** a violation has a non-empty disposition number
- **THEN** its dedup key SHALL be derived from data source and disposition number, not the synthetic hash

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