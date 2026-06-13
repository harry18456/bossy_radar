## ADDED Requirements

### Requirement: Sync commands SHALL exit non-zero when any source fails

The sync-companies, sync-violations, and sync-mops CLI commands SHALL track per-source success and failure, including download failures and sync exceptions, and SHALL exit with a non-zero code when at least one source failed. Remaining sources SHALL still be attempted after one source fails.

#### Scenario: One violation source fails to download

- **WHEN** sync-violations runs and one source's download fails while others succeed
- **THEN** the command SHALL attempt every requested source
- **THEN** the command SHALL exit with code 1

#### Scenario: All sources succeed

- **WHEN** every requested source downloads and syncs successfully
- **THEN** the command SHALL exit with code 0

### Requirement: Sync commands SHALL print a per-source summary

After processing, sync commands SHALL print a summary listing every source with its written row count and skipped row count, and failed sources SHALL be marked with their error summary.

#### Scenario: Summary after a partial failure

- **WHEN** sync-violations finishes with one failed source and one successful source
- **THEN** the output SHALL contain one line per source
- **THEN** the failed source line SHALL include a failure marker and an error summary
- **THEN** the successful source line SHALL include its written and skipped row counts

### Requirement: Skipped parse rows SHALL be logged and counted

When a row is dropped during parsing or record construction, the system SHALL log a warning identifying the source and row, and the drop SHALL increment the skipped counter reported in the summary. Silent except-pass row handling SHALL NOT remain in the violation parsing loop.

#### Scenario: A malformed row is dropped

- **WHEN** one row in a violation source raises during record construction
- **THEN** a warning SHALL be logged for that row with the source name
- **THEN** the source's skipped count SHALL increase by one
- **THEN** the remaining rows SHALL still be processed
