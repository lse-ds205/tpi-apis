## Usage and API Endpoints

This project is built with **FastAPI**, a modern web framework designed for high performance, data validation, and automatic documentation.

The API follows a **modular architecture** for clarity and maintainability. The main application (`main.py`) initializes the FastAPI app and integrates three functional route modules:

### 1. Company Routes (`company_routes.py`)

Handles endpoints related to company-level data:

- Dynamically loads the latest dataset on startup.
- Endpoints include:
  - List all companies
  - Retrieve company details
  - Access historical assessments
  - Compare recent company performance

### 2. Management Quality (MQ) Routes (`mq_routes.py`)

Provides access to Management Quality assessment data:

- Loads the most recent MQ dataset.
- Endpoints support:
  - Retrieving latest MQ assessments
  - Filtering historical assessments by methodology cycle
  - Viewing sector-level MQ trends

### 3. Carbon Performance (CP) Routes (`cp_routes.py`)

Focuses on Carbon Performance evaluation:

- Consolidates multiple CP datasets at runtime.
- Supports endpoints to:
  - Fetch the latest CP assessments
  - Retrieve CP history for specific companies
  - Evaluate alignment with future climate targets
  - Compare performance across cycles

### Schema Validation (`schemas.py`)

All request and response data is validated using **Pydantic** models:

- Models define strict schemas for companies, MQ, CP, and pagination.
- Ensures consistency, robustness, and clear API contracts.

### Routing and Data Flow

- `main.py` sets up the app and registers each route module.
- Requests are routed based on URL prefixes (`/company`, `/mq`, `/cp`).
- Each module dynamically loads the most recent data from CSV files.
- Responses are validated before being returned.

This design ensures modularity, reliability, and scalability, with automatic data updates and strong validation guarantees.

---

## Data Source and Format

All datasets come from the [Transition Pathway Initiative (TPI)](https://www.transitionpathwayinitiative.org/corporates), covering company assessments, Management Quality (MQ), and Carbon Performance (CP).

### Data Organization

- **Directory Naming**: `TPI sector data - All sectors - MMDDYYYY`
- **File Format**: CSV

### Key Datasets

| File | Description |
|------|-------------|
| `Company_Latest_Assessments_MMDDYYYY.csv` | Company info, MQ scores, CP alignment, sector, geography |
| `MQ_Assessments_Methodology_*.csv`        | MQ STAR ratings across methodology cycles |
| `CP_Assessments_*.csv`                    | CP alignment for 2025, 2027, 2035, and 2050 |

### Dynamic Data Handling

- The API automatically selects the latest directory and files.

### Benefits

- **Scalable**: No code changes needed for new data
- **Robust**: Consistent structure and naming
- **Flexible**: Easy integration with new TPI releases

This structure supports ESG analysis, investment decisions, policy tracking, and corporate benchmarking.

---

## Unit Testing

Unit tests are implemented using **pytest** and FastAPI’s testing tools to ensure component reliability and safe development.

### Test Coverage

### `test_main.py`

- Verifies core setup and root endpoint response.

### `test_company_routes.py`

- `/company/companies`: Checks pagination, field structure, and response integrity.
- `/company/{company_id}`: Confirms proper `404` handling for invalid company IDs.

### `test_mq_routes.py`

- `/mq/latest`: Validates paginated results and schema compliance.
- `/mq/methodology/{methodology_id}`: Ensures invalid IDs return `422` errors.
- `/mq/trends/sector/{sector_id}`: Checks for `404` responses on invalid sectors.

### `test_cp_routes.py`

- `/cp/latest`: Verifies data presence and key fields.
- `/cp/company/{company_id}`: Confirms error handling for missing companies.
- `/cp/company/{company_id}/alignment`: Ensures appropriate errors for missing data.
- `/cp/company/{company_id}/comparison`: Handles insufficient data gracefully with informative responses.

### `test_helpers.py`

- `get_latest_data_dir()`:
  - Validates correct date-based folder selection.
  - Confirms `FileNotFoundError` on missing directories.

## Running Tests

To run all tests:

```bash
pytest
