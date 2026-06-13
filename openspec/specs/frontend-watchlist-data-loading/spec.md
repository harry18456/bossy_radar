# frontend-watchlist-data-loading Specification

## Purpose

TBD - created by archiving change 'frontend-watchlist-static-profile-loading'. Update Purpose after archive.

## Requirements

### Requirement: Watchlist data download SHALL scale with watchlist size

The watchlist page SHALL load comparison data by fetching one company profile per watched company (static mode: companies/{code}.json; dynamic mode: the company profile API). The watchlist page SHALL NOT request any yearly-summaries data file. Profile fetches SHALL be issued in parallel, not sequentially awaited in a loop.

#### Scenario: Watchlist page loads with watched companies

- **WHEN** the watchlist page loads with N watched company codes
- **THEN** the browser SHALL issue N company profile requests and one company catalog request for watchlist data
- **THEN** the browser SHALL NOT issue any request whose path contains yearly-summaries

##### Example: three watched companies in static mode

- **GIVEN** the watchlist contains codes 2330, 2317, 6510 in static data mode
- **WHEN** the watchlist page loads
- **THEN** data requests are companies/2330.json, companies/2317.json, companies/6510.json, and company-catalog.json
- **THEN** no request matches yearly-summaries/*.json

---
### Requirement: Watchlist SHALL display every watched company

The watchlist page SHALL render a company card and a comparison table row for every watched company. Display SHALL NOT be truncated by any pagination default or size cap.

#### Scenario: Watchlist exceeds the former default page size

- **WHEN** the watchlist contains 25 watched companies
- **THEN** the company card grid SHALL render 25 cards
- **THEN** the comparison table SHALL render 25 rows
- **THEN** the watched-company count in the header SHALL equal the number of rendered cards

---
### Requirement: Client-assembled yearly summary SHALL match exporter semantics

The frontend SHALL assemble YearlySummaryItem entries from a CompanyProfile using the same semantics as the backend yearly-summaries exporter: MOPS records keyed by their ROC year; violation and environmental-violation yearly buckets keyed by penalty_date AD year minus 1911; violations with null penalty_date excluded from yearly buckets; total counts and total fines computed across all years (not cumulative to the item year); a (company, year) item produced only when at least one of the six data sources has data for that year; items ordered by year descending.

#### Scenario: Violation year bucketing converts AD to ROC

- **WHEN** a profile contains a violation with penalty_date in AD year 2024
- **THEN** that violation SHALL count toward the item whose year is 113

##### Example: year conversion and totals

- **GIVEN** a profile with violations dated 2024-03-01 (fine 50000) and 2022-07-15 (fine 20000) and a non-manager salary record for ROC year 113
- **WHEN** yearly summary items are assembled
- **THEN** the year 113 item has violations_year_count 1, violations_year_fine 50000, violations_total_count 2, violations_total_fine 70000
- **THEN** the year 111 item has violations_year_count 1, violations_year_fine 20000, violations_total_count 2, violations_total_fine 70000

#### Scenario: Years without any data produce no item

- **WHEN** a company has no MOPS record, no violation, and no environmental violation for a given year
- **THEN** no yearly summary item SHALL be produced for that company and year

#### Scenario: Null penalty_date stays out of yearly buckets

- **WHEN** a profile contains a violation whose penalty_date is null
- **THEN** that violation SHALL NOT increase any violations_year_count
- **THEN** that violation SHALL increase violations_total_count

#### Scenario: Assembled values equal exported values

- **WHEN** items assembled from a real exported company profile are compared with the same company's entries in the exported yearly-summaries year files
- **THEN** every overlapping field value SHALL be equal

---
### Requirement: A failed profile fetch SHALL NOT blank the watchlist

When one company profile fetch fails, the watchlist page SHALL still render data for the companies whose fetches succeeded, and SHALL render the failed company using the existing zero-count fallback row.

#### Scenario: One profile fetch fails among several

- **WHEN** the watchlist loads 5 companies and one profile fetch rejects
- **THEN** the comparison data SHALL contain assembled items for the 4 successful companies
- **THEN** the page SHALL NOT surface an unhandled error state for the whole list
