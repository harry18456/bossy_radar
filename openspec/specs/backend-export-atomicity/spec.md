# backend-export-atomicity Specification

## Purpose

TBD - created by archiving change 'backend-atomic-static-export'. Update Purpose after archive.

## Requirements

### Requirement: Static export SHALL be all-or-nothing

The export service SHALL write all output into a temporary sibling directory and SHALL atomically swap it into place only after every export step succeeds. When any export step fails, the existing output directory SHALL remain byte-for-byte identical to its pre-export state, the temporary directory SHALL be removed, and the failure SHALL propagate to the caller so the CLI exits non-zero.

#### Scenario: An export step fails midway

- **WHEN** export_all runs against an existing output directory and one export step raises an exception
- **THEN** the output directory SHALL contain exactly the same files with the same content as before the export started
- **THEN** no temporary export directory SHALL remain next to the output directory
- **THEN** the exception SHALL propagate to the caller

#### Scenario: Export succeeds

- **WHEN** export_all completes every step successfully
- **THEN** the output directory SHALL contain only the newly exported files
- **THEN** no .tmp or .bak sibling directory of the output directory SHALL remain

#### Scenario: Leftover artifacts from a crashed export

- **WHEN** export_all starts while a leftover temporary or backup directory from a previous crashed run exists
- **THEN** the leftover SHALL be removed and the export SHALL complete normally


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
### Requirement: Single JSON file writes SHALL be atomic

The export service SHALL write each JSON file to a temporary file in the same directory and atomically replace the target path, so a crash can never leave a truncated or invalid JSON file at the target path.

#### Scenario: A JSON file is written

- **WHEN** the export service saves a JSON payload to a target path
- **THEN** the target path SHALL contain complete, parseable JSON
- **THEN** no temporary file for that target SHALL remain in the directory


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
### Requirement: Export deletions SHALL be restricted to service-owned paths

The export service SHALL only delete paths that resolve inside the output directory's parent and match the service's own temporary or backup naming pattern. The live output directory SHALL never be deleted recursively; it SHALL only be renamed during the swap. A deletion request for any other path SHALL raise an error without deleting anything.

#### Scenario: A non-conforming path is targeted for cleanup

- **WHEN** the export service is asked to clean a path that does not match its temporary or backup naming pattern
- **THEN** the service SHALL raise an error
- **THEN** nothing SHALL be deleted

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