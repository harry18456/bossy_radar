## ADDED Requirements

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
