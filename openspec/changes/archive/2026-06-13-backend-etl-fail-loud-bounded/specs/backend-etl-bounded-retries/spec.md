## ADDED Requirements

### Requirement: Retry loops SHALL have an absolute attempt ceiling

The detail-scraper fetch retry SHALL terminate within a bounded number of attempts even when configured for infinite retries. With retries set to a negative value, the total attempts SHALL NOT exceed 50; with a non-negative retries value, behavior SHALL remain retries plus one attempts.

#### Scenario: Infinite retries against a permanently failing host

- **WHEN** _fetch_with_retry runs with retries -1 and every request fails
- **THEN** the function SHALL stop after at most 50 attempts
- **THEN** the function SHALL return a failure result instead of looping forever

##### Example: attempt ceiling

| retries | outcome on permanent failure |
| ------- | ---------------------------- |
| 3       | stops after 4 attempts       |
| 0       | stops after 1 attempt        |
| -1      | stops after at most 50 attempts |

### Requirement: Consecutive maintenance pages SHALL trip a circuit breaker

The company detail sync SHALL stop issuing new requests after 5 consecutive maintenance-page detections and SHALL report the run as circuit-broken. The CLI SHALL exit non-zero when the circuit breaker trips.

#### Scenario: Sustained rate limiting

- **WHEN** 5 consecutive companies in a row return MOPS maintenance pages
- **THEN** the sync SHALL NOT issue further requests in this run
- **THEN** the run summary SHALL state that the circuit breaker tripped
- **THEN** the CLI SHALL exit with a non-zero code

### Requirement: Documentation SHALL NOT recommend unbounded retries

Project documentation SHALL NOT present a negative retries value as the recommended invocation; it SHALL note that negative values are clamped by the attempt ceiling.

#### Scenario: Reading the backend usage docs

- **WHEN** the backend usage documentation shows the sync-company-details example
- **THEN** the example SHALL use a finite retries value
