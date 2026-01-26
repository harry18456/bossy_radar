# Backend Architecture

## Architecture Principles

### 1. Data Ingestion / ETL (CLI)
*   **Role**: Dedicated to "Preparing Data".
*   **Location**: `app/cli`
*   **Responsibilities**:
    *   Fetching external data (Web Scraping, API Calls).
    *   Parsing and Cleaning data.
    *   Saving/Updating the Database.
*   **Characteristics**:
    *   **Long-running**: Tasks that take time and shouldn't block HTTP requests.
    *   **Active/Scheduled**: Triggered by admin commands or cron jobs.
    *   **Write-Heavy**: Focus on data persistence.

### 2. Data Serving (FastAPI)
*   **Role**: Dedicated to "Consuming/Serving Data".
*   **Location**: `app/api`
*   **Responsibilities**:
    *   API Endpoints for Frontend/Clients.
    *   Handling Request/Response cycles.
    *   Query parameters validation (Filter, Sort).
*   **Characteristics**:
    *   **Real-time**: Must respond quickly to avoid timeouts.
    *   **Passive**: Triggered by user actions.
    *   **Read-Heavy**: Focus on querying efficient data views.

### 3. Layered Design (Services)
*   **Role**: Shared Business Logic.
*   **Location**: `app/services`
*   **Principle**: Do not lock core logic inside CLI strings or API routes.
*   **Structure**:
    *   **Entry Points (CLI/API)**: Only handle input parsing and trigger services.
    *   **Service Layer**: Contains the actual logic (e.g., `crawler_service.py`, `company_service.py`).
    *   **Data Layer (DB/Models)**: Handles direct database interactions.

### 4. File Storage / Artifacts
*   **Role**: Temporary or persistent file storage for CLI operations.
*   **Location**: `backend/data`
*   **Structure**:
    *   `data/raw`: Raw HTML/JSON responses from crawlers.
    *   `data/processed`: Intermediate data structures (e.g., CSVs, Parquet) before DB insertion.
    *   `data/logs`: Execution logs.
*   **Policy**:
    *   **Gitignore**: **MUST** be ignored by git.
    *   **Retention**: Treated as temporary. The Database is the source of truth.

