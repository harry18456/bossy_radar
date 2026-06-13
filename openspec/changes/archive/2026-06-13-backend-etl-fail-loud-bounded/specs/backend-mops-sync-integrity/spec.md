## ADDED Requirements

### Requirement: A failing MOPS row SHALL NOT abort its batch

During MOPS upsert, a row that raises during record construction or persistence SHALL be logged with its identifying fields, counted as skipped, and skipped over; the remaining rows of the same (year, market) batch SHALL be written normally.

#### Scenario: One bad row among many

- **WHEN** a (year, market) batch contains one record that raises during model construction
- **THEN** every other record in the batch SHALL be persisted
- **THEN** the skipped count for the source SHALL increase by one
- **THEN** a warning SHALL identify the bad row's raw company code, year, and market

### Requirement: A failed MOPS batch SHALL roll back both sessions

When processing of a (year, market) unit raises, the main session and the archive session SHALL both be rolled back before the next unit is processed, and the failed unit SHALL be recorded. Subsequent units SHALL commit successfully without session-state errors.

#### Scenario: Failure in the first unit does not poison the second

- **WHEN** the first (year, market) unit raises after partially flushing rows
- **THEN** both sessions SHALL be rolled back
- **THEN** the second (year, market) unit SHALL be processed and committed without a PendingRollbackError
- **THEN** the failed unit SHALL appear in the source's failure record

### Requirement: MOPS commits SHALL align with (year, market) boundaries

The upsert path SHALL NOT commit mid-batch on row-count intervals; each (year, market) unit SHALL be committed once after it is fully processed.

#### Scenario: Batch commit boundary

- **WHEN** a (year, market) unit with more than 500 rows is processed successfully
- **THEN** its rows SHALL be committed as one unit after processing completes

### Requirement: MOPS cache SHALL only store validated content

Fetched MOPS HTML SHALL be validated before caching: non-empty, containing a table marker, and free of maintenance-page markers. Invalid content SHALL NOT be written to cache and SHALL count the (year, market) unit as failed. A cache hit that parses to zero records SHALL invalidate that cache file and refetch once; a refetched response that still parses to zero records SHALL be accepted as a legitimately empty unit.

#### Scenario: Maintenance page is returned

- **WHEN** the MOPS response body contains the maintenance marker 服務暫時無法提供
- **THEN** no cache file SHALL be written for that (year, market)
- **THEN** that unit SHALL be recorded as failed

#### Scenario: Stale zero-record cache

- **WHEN** a cached file parses to zero records
- **THEN** the cache file SHALL be deleted and the unit SHALL be fetched again
- **THEN** a refetched body that still parses to zero records SHALL be treated as empty, not failed
