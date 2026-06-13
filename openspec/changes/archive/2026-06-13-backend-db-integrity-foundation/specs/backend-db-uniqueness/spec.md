## ADDED Requirements

### Requirement: Natural keys SHALL be unique at the database layer

Each data table SHALL declare a UNIQUE constraint over its natural key: the MOPS tables over (raw_company_code, year, market_type); the violation table over its dedup key; the environmental violation table over its dedup key. Inserting a row whose natural key already exists SHALL update the existing row rather than create a duplicate.

#### Scenario: Re-upserting a MOPS row is idempotent

- **WHEN** the same (raw_company_code, year, market_type) record is upserted twice
- **THEN** the table SHALL contain exactly one row for that key
- **THEN** the second upsert SHALL update the existing row

#### Scenario: Re-upserting a violation is idempotent

- **WHEN** the same violation record is upserted twice
- **THEN** the violation table SHALL contain exactly one row for that record

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
