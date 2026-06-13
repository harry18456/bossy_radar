# backend-yearly-summary-parity Specification

## Purpose

TBD - created by archiving change 'backend-atomic-static-export'. Update Purpose after archive.

## Requirements

### Requirement: Yearly summary assembly SHALL have a single shared implementation

The yearly summary item assembly (year set derivation, violation and environmental-violation aggregation, MOPS record matching, skip-empty rule, include-set handling) SHALL exist in exactly one shared builder function. The aggregation route SHALL use the builder and apply only sorting and pagination on top. The exporter SHALL use the builder with the full include set.

#### Scenario: Route and exporter assemble items

- **WHEN** the aggregation route and the exporter assemble yearly summary items from the same database state
- **THEN** both SHALL obtain items from the same builder function
- **THEN** the exporter's per-year file items SHALL equal the route response items for include all with pagination covering the full result

#### Scenario: Include set controls assembled fields

- **WHEN** the builder is called without violations in the include set
- **THEN** returned items SHALL NOT carry violation statistics
- **WHEN** the builder is called with the all include value
- **THEN** returned items SHALL carry violation statistics, environmental violation statistics, and all four MOPS record types where data exists


<!-- @trace
source: backend-atomic-static-export
updated: 2026-06-13
code:
  - backend/app/api/routes/leaderboard.py
  - docs/REMEDIATION_PLAN.md
  - docs/BACKEND_AUDIT.md
  - backend/app/services/leaderboard_builder.py
  - backend/app/services/yearly_summary_builder.py
  - backend/app/api/routes/aggregation.py
  - backend/app/services/export_service.py
tests:
  - backend/tests/test_export_atomicity.py
  - backend/tests/test_api_leaderboard.py
  - backend/tests/test_leaderboard_builder.py
  - backend/tests/test_export_route_parity.py
-->

---
### Requirement: Exported yearly summary index SHALL be derived from builder output

The exported index file's years list, per-year counts, and total count SHALL be derived from the builder's returned items rather than from separate queries.

#### Scenario: Index file is generated

- **WHEN** the exporter writes the yearly summaries index file
- **THEN** the years list SHALL exactly match the set of per-year files written
- **THEN** each per-year count SHALL equal the number of items in that year's file
- **THEN** the total count SHALL equal the sum of all per-year counts

<!-- @trace
source: backend-atomic-static-export
updated: 2026-06-13
code:
  - backend/app/api/routes/leaderboard.py
  - docs/REMEDIATION_PLAN.md
  - docs/BACKEND_AUDIT.md
  - backend/app/services/leaderboard_builder.py
  - backend/app/services/yearly_summary_builder.py
  - backend/app/api/routes/aggregation.py
  - backend/app/services/export_service.py
tests:
  - backend/tests/test_export_atomicity.py
  - backend/tests/test_api_leaderboard.py
  - backend/tests/test_leaderboard_builder.py
  - backend/tests/test_export_route_parity.py
-->