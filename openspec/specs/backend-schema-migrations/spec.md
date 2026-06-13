# backend-schema-migrations Specification

## Purpose

TBD - created by archiving change 'backend-db-integrity-foundation'. Update Purpose after archive.

## Requirements

### Requirement: Schema SHALL be managed by versioned migrations

The backend SHALL manage both the main and archive SQLite schemas through Alembic migrations rather than runtime create_all calls. A single migrations package SHALL apply the same migration scripts to both the main engine and the archive engine, each tracking its own version. Service code SHALL NOT call SQLModel.metadata.create_all to establish production schema.

#### Scenario: Upgrade a clean database

- **WHEN** alembic upgrade head runs against an empty SQLite database
- **THEN** the resulting schema SHALL contain every model table with its unique constraints

#### Scenario: Both engines are migrated

- **WHEN** the migration command runs without restricting the target
- **THEN** both the main and the archive database SHALL be upgraded to the same head revision
- **THEN** each database SHALL record the applied revision in its own alembic_version table

#### Scenario: Downgrade is reversible

- **WHEN** alembic downgrade is run from head to the baseline revision
- **THEN** the post-baseline schema changes SHALL be reverted without error


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
### Requirement: Existing databases SHALL migrate in place without data loss

Migrating an existing populated database SHALL preserve every row. The baseline revision SHALL be stampable on an already-populated database so that only post-baseline migrations execute against it.

#### Scenario: In-place migration preserves rows

- **WHEN** an existing database is stamped at the baseline revision and then upgraded to head
- **THEN** each table's row count after the upgrade SHALL equal its row count before the upgrade

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