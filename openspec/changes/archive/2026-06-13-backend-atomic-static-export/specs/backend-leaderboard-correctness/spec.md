## ADDED Requirements

### Requirement: Leaderboard assembly SHALL have a single shared implementation

The leaderboard response assembly (violation aggregation, salary boards, industry salary boards) SHALL exist in exactly one shared builder function used by both the leaderboard route and the exporter.

#### Scenario: Route and exporter build leaderboards

- **WHEN** the leaderboard route and the exporter build leaderboards from the same database state
- **THEN** the exported leaderboards JSON SHALL equal the route response serialized with model_dump mode json

### Requirement: Violation bottom leaderboards SHALL reflect the true ascending order over all companies

The violation leaderboard bottom_by_count SHALL contain the N companies with the smallest combined labor plus environmental violation count among all companies whose combined count is greater than zero, ordered ascending. bottom_by_fine SHALL apply the same rule to combined fines. Top boards SHALL be the corresponding descending top N over the full aggregation, not a truncated pool. This SHALL hold for the all-time board and for every yearly board.

#### Scenario: Bottom board over 25 companies

- **WHEN** 25 companies have combined violation counts 1 through 25
- **THEN** bottom_by_count SHALL contain the companies with counts 1 through 10 in ascending order
- **THEN** top_by_count SHALL contain the companies with counts 25 down to 16 in descending order

##### Example: ascending bottom slice

- **GIVEN** companies C1..C25 where Ck has k total violations
- **WHEN** the leaderboard is built with limit 10
- **THEN** bottom_by_count is C1, C2, C3, C4, C5, C6, C7, C8, C9, C10
- **THEN** top_by_count is C25, C24, C23, C22, C21, C20, C19, C18, C17, C16

#### Scenario: Combined labor and environmental totals

- **WHEN** a company has 2 labor violations and 3 environmental violations
- **THEN** its total_count used for ranking SHALL be 5
- **THEN** its labor_count SHALL be 2 and env_count SHALL be 3 in the leaderboard item
