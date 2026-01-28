# Backend Architecture

## Architecture Principles

### 1. Data Ingestion / ETL (CLI)

- **Role**: Dedicated to "Preparing Data".
- **Location**: `app/cli`
- **Responsibilities**:
  - Fetching external data (Web Scraping, API Calls).
  - Parsing and Cleaning data.
  - Saving/Updating the Database.
- **Characteristics**:
  - **Long-running**: Tasks that take time and shouldn't block HTTP requests.
  - **Active/Scheduled**: Triggered by admin commands or cron jobs.
  - **Write-Heavy**: Focus on data persistence.

### 2. Data Serving (FastAPI)

- **Role**: Dedicated to "Consuming/Serving Data".
- **Location**: `app/api`
- **Responsibilities**:
  - API Endpoints for Frontend/Clients.
  - Handling Request/Response cycles.
  - Query parameters validation (Filter, Sort).
- **Characteristics**:
  - **Real-time**: Must respond quickly to avoid timeouts.
  - **Passive**: Triggered by user actions.
  - **Read-Heavy**: Focus on querying efficient data views.

### 3. Layered Design (Services)

- **Role**: Shared Business Logic.
- **Location**: `app/services`
- **Principle**: Do not lock core logic inside CLI strings or API routes.
- **Structure**:
  - **Entry Points (CLI/API)**: Only handle input parsing and trigger services.
  - **Service Layer**: Contains the actual logic (e.g., `crawler_service.py`, `company_service.py`).
  - **Data Layer (DB/Models)**: Handles direct database interactions.

### 4. File Storage / Artifacts

- **Role**: Temporary or persistent file storage for CLI operations.
- **Location**: `backend/data`
- **Structure**:
  - `data/raw`: Raw HTML/JSON responses from crawlers.
  - `data/processed`: Intermediate data structures (e.g., CSVs, Parquet) before DB insertion.
  - `data/logs`: Execution logs.
- **Policy**:
  - **Gitignore**: **MUST** be ignored by git.
  - **Retention**: Treated as temporary. The Database is the source of truth.

## Features & Modules

### 1. Company Data (Listing Info)

Syncs company basic information from TWSE (Listed/OTC/Emerging).

- **CLI Command**:
  ```bash
  # Sync all market types
  uv run python -m app.cli.main sync-companies --type all
  ```
- **API**: `GET /api/v1/companies`
  - Supports filtering by `market_type`, `industry`, `code`, `name`.
  - Supports multi-sort (e.g., `sort=-capital`).

### 2. Labor Violation Data

Syncs labor violation records from 8 Ministry of Labor Open Data sources (Labor Standards, Gender Equality, Occupational Safety, etc.).

- **Architecture**:
  - **Main DB (`bossy_radar.db`)**: Stores violations linked to **Listed/OTC Companies**.
  - **Archive DB (`archive.db`)**: Stores unmatched violations (Small businesses, individuals) to keep the main DB clean.
- **Linking Strategy**:
  1. **Exact Match**: Matches company name or abbreviation directly (e.g., "Generic Corp").
  2. **Branch Match**: Matches if violation name starts with company name (e.g., "Generic Corp Kaohsiung Branch").
  3. **Chairman Match**: Matches if the responsible person is unique to a listed company.
- **CLI Command**:

  ```bash
  # Sync all violation sources
  uv run python -m app.cli.main sync-violations --source all
  ```

  3. **Chairman Match**: Matches if the responsible person is unique to a listed company.

- **Data Stats (2026-01-27)**:
  - **Matched**: 9,591 records (Main DB).
  - **Unmatched**: 165,661 records (Archive DB).
- **API**: `GET /api/v1/violations`
  - **Global Search**: Query violations across all companies.
  - **Key Filters**:
    - `data_source`: Filter by law type (e.g., `LaborStandards`).
    - `min_fine` / `max_fine`: Filter by fine amount.
    - `start_date` / `end_date`: Filter by penalty timeframe.

### 3. MOPS Employee Salary/Benefit Data

Syncs employee salary and benefit data from MOPS (公開資訊觀測站) for Listed/OTC companies.

- **Data Sources**:
  | Source | Description |
  |--------|-------------|
  | t100sb14 | 財務報告附註揭露之員工福利(薪資)資訊 |
  | t100sb15 | 非擔任主管職務之全時員工薪資資訊 |
  | t100sb13 | 員工福利政策及權益維護措施揭露 |
  | t222sb01 | 基層員工調整薪資或分派酬勞 |

- **CLI Command**:

  ```bash
  # Sync all data types (default: last 5 years)
  uv run python -m app.cli.main sync-mops

  # Sync specific year range
  uv run python -m app.cli.main sync-mops --start-year 113 --end-year 113

  # Sync specific data type
  uv run python -m app.cli.main sync-mops --data-type employee_benefit
  ```

- **API Endpoints**:
  | Endpoint | Description |
  |----------|-------------|
  | `GET /api/v1/mops/employee-benefits` | 員工福利(薪資)資訊 |
  | `GET /api/v1/mops/non-manager-salaries` | 非主管全時員工薪資 |
  | `GET /api/v1/mops/welfare-policies` | 福利政策揭露 |
  | `GET /api/v1/mops/salary-adjustments` | 基層員工調薪/分派酬勞 |

- **Common Query Parameters**:
  - `page`, `size`: Pagination (max 100 per page).
  - `sort`: Multi-sort (e.g., `-year`, `company_code`).
  - `company_code`, `year`, `market_type`: Multi-value filters.

## Local Development

### Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) (Package Manager)

### Setup

```bash
# Install dependencies
uv sync
```

### Running the Server

```bash
# Start development server (Auto-reload)
uv run fastapi dev app/main.py
```

- **API Docs**: `http://127.0.0.1:8000/docs`
- **API Root**: `http://127.0.0.1:8000/api/v1`
