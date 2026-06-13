# frontend-company-list-pagination Specification

## Purpose

TBD - created by archiving change 'frontend-watchlist-static-profile-loading'. Update Purpose after archive.

## Requirements

### Requirement: Companies list page SHALL show 12 items per page in both data modes

The companies list page SHALL request pages of 12 items using the size parameter recognized by both the static and dynamic API implementations.

#### Scenario: First page of the companies list

- **WHEN** the companies list page loads without filters
- **THEN** at most 12 company cards SHALL be rendered for the page
- **THEN** the pagination total-pages value SHALL be computed from a page size of 12

#### Scenario: Static and dynamic modes agree

- **WHEN** the companies list page loads in static mode and in dynamic mode with the same dataset
- **THEN** both modes SHALL use a page size of 12

---
### Requirement: Company list API parameters SHALL be statically typed

The getCompanies and getYearlySummary functions of both API implementations SHALL declare typed parameter interfaces (CompanyListParams, YearlySummaryParams) instead of any. A call site passing a parameter name outside the declared contract SHALL fail TypeScript compilation.

#### Scenario: Wrong parameter name fails the type check

- **WHEN** a call site passes page_size or limit to getCompanies
- **THEN** the TypeScript type check SHALL report a compilation error for that call

#### Scenario: Both implementations share one contract

- **WHEN** the static and dynamic getCompanies implementations are inspected
- **THEN** both SHALL accept the same CompanyListParams interface
