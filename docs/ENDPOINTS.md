
## Usage and API Endpoints 
The project uses a modular and structured approach built around FastAPI, a modern, efficient Python web framework designed for high performance, easy validation, and clear documentation.

At the core, we have the main application (`main.py`), which serves as the entry point. Its primary role is to initialize the FastAPI application and integrate the various route modules into a unified API. This modular architecture improves maintainability and clarity, allowing each component to handle distinct functionalities without unnecessary dependencies or complexity.

There are three main functional modules integrated into the application: 
1. **Company Routes (`company_routes.py`)**: 
  - This module manages endpoints related specifically to companies and their assessments.
  - It dynamically loads the most recent dataset available, ensuring the application consistently accesses updated information without manual intervention.
  - It provides endpoints to list companies, retrieve detailed information, historical assessment records, and compare recent performances.
2. **Management Quanlity (MQ) Routes (`mq_routes.py`)**: 
  - Dedicated specifically to Management Quality assessments, this module similarly dynamically selects and loads the latest MQ datasets.
  - It includes specialized endpoints for retrieving current MQ assessments, historical assessments filtered by methodology cycle, and sector-wide trends.
  - This design enables easy tracking and comparative analysis of MQ trends over time and across sectors.
3. **Carbon Performance (CP) Routes (`cp_routes.py`)**:
  - Focused explicitly on Carbon Performance assessments, this module consolidates multiple CP assessment files dynamically into a unified data structure.
  - It provides endpoints to fetch the latest CP assessments, detailed historical CP data for individual companies, assess alignment with future carbon reduction targets, and perform comparisons between different assessment cycles.

Central to ensuring the correctness and consistency of data across the entire API is the `schemas.py` module. This module contains Pydantic models used to validate and serialize data sent to and from the API. These models define clear and strict data structures for companies, MQ assessments, CP assessments, and various response formats, including pagination and performance comparisons. Leveraging Pydantic’s automatic data validation ensures robustness and significantly reduces errors due to data inconsistencies.

The entire setup integrates seamlessly as follows:
- Upon launching the application, the main script (`main.py`) initializes the FastAPI application.
- It integrates each of the three dedicated route modules (`company_routes.py`, `mq_routes.py`, and `cp_routes.py`) through FastAPI routers. Each router encapsulates functionality relevant to its area, ensuring clear separation of concerns.
- Requests arriving at the API are directed to the appropriate route module based on URL structure (e.g., `/company`, `/mq`, or `/cp`).
- Each route module accesses its own specialized dataset, which is dynamically selected and loaded at runtime from the most recent available data.
- Responses from these endpoints are strictly validated against defined schemas to ensure data accuracy and consistency before being returned to the user.

In essence, this structured setup ensures high reliability, maintainability, clarity, and scalability. The clear separation of modules combined with robust schema validation and dynamic data handling creates an efficient, adaptable, and user-friendly API ecosystem.

## Data Source and Format
This project uses datasets sourced from the [Transition Pathway Initiative (TPI)](https://www.transitionpathwayinitiative.org/corporates)
, specifically focusing on company assessments, Management Quality (MQ), and Carbon Performance (CP) evaluations.

The data structure is as follows: 
- **Data Source**: The datasets originate directly from the TPI's publicly available assessment data, regularly updated and organised in date-stamped directories following the naming convention: `TPI sector data - All sectors - MMDDYYYY`
- **Data Format**: The assessment files are stored as CSV files within these directories. There are three main types of CSV datasets used:
  - Company Assessments: `Company_Latest_Assessments_MMDDYYYY.csv`
    - Contains general details about each company's latest assessment, such as company name, sector, geography, latest assessment year, Management Quality (MQ) score, and Carbon Performance (CP) alignment details.
  - Management Quality (MQ) Assessments: `MQ_Assessments_Methodology_*.csv`
    - Contains detailed Management Quality assessments across multiple methodology cycles. Each record includes the MQ STAR rating, assessment dates, and sector-specific information.
  - Carbon Performance (CP) Assessments: `CP_Assessments_*.csv`
    - Contains detailed Carbon Performance evaluations, with alignment targets for different future years (2025, 2027, 2035, and 2050).
- **Automated Data Handling**: The project automatically selects the latest data folder and CSV files, extracting and processing them dynamically without manual intervention. This ensures:
  - Scalability: Data updates don't require changes in the code.
  - Robustness: Consistent handling of data formats and dates.
  - Flexibility: Easy maintenance and continuous integration with new datasets.

These structured CSV files serve as the backbone for the API, powering all endpoints and responses. The data provided by this API can be particularly valuable to sustainability researchers, policymakers, financial analysts, and corporate sustainability officers. Users might leverage this data for ESG (Environmental, Social, and Governance) reporting, investment decision-making, sector benchmarking, and evaluating corporate transitions towards low-carbon economies.

## Unit Testing
Unit tests are automated tests designed to verify individual units or components of a software application. The primary goal is to ensure each piece of code operates correctly in isolation, catching potential bugs early in the development process. Unit testing is essential for:
- **Ensuring Reliability**: Confirming that code behaves as intended.
- **Facilitating Refactoring**: Allowing developers to confidently update or optimize code without fear of unintended side effects.
- **Enhancing Maintainability**: Clearly documenting expected behavior, which aids future developers in understanding and safely extending the application.
- **Early Bug Detection**: Quickly identifying and resolving issues before they propagate or affect users.

This project incorporates structured and well-organised unit tests using FastAPI's built-in testing client and `pytest`. The tests have been clearly segmented based on functional modules and core logic:
- `test_main.py`: This test file includes simple yet essential tests to verify the fundamental functioning and setup of the application itself. It helps confirm the application’s root endpoint consistently returns the expected welcome message, ensuring the basic infrastructure and server configuration are correct and functioning as intended.
- `test_company_routes.py`: This test suite verifies the correctness and reliability of endpoints related to company data retrieval and operations. It specifically checks:
  - Listing Companies (`/company/companies` endpoint): 
    - Ensures correct pagination functionality. 
    - Validates the structure of responses, checking essential fields like total company count, current page, results per page, and the list of companies.
  - Company Details Retrieval (`/company/{company_id}` endpoint): 
    - Verifies appropriate error handling by checking if requesting details for a non-existent company correctly returns a `404 Not Found` response, safeguarding against incorrect data handling.
- `test_mq_routes.py`: This test module focuses on validating Management Quality (MQ) assessment endpoints, ensuring robust retrieval, correct pagination, accurate sector-specific filtering, and rigorous input validation:
  - Latest MQ Assessments (`/mq/latest` endpoint):
    - Checks that the endpoint correctly returns paginated MQ assessment data, verifying the structure, including total records, pagination details, and individual assessment results.
  - MQ Methodology Cycle Validation (`/mq/methodology/{methodology_id}` endpoint):
    - Verifies endpoint robustness by testing the handling of invalid methodology IDs, confirming that the API returns clear validation errors (`422 Unprocessable Entity`) for out-of-range inputs.
  - Sector Trends in MQ (`/mq/trends/sector/{sector_id}` endpoint):
    - Ensures accurate error handling by checking that the endpoint returns a meaningful `404 Not Found` when a non-existent or incorrectly specified sector is requested.
- `test_cp_routes.py`: This file contains unit tests for Carbon Performance (CP) endpoints, ensuring the reliability of CP data retrieval, alignment assessments, and comparative analysis functionalities. It specifically tests:
  - Latest CP Assessments (`/cp/latest` endpoint):
    - Validates successful retrieval and correct structure of paginated CP assessment data, ensuring all essential keys (e.g., `company_id`, `latest_assessment_year`) are present.
  - CP History for Specific Company (`/cp/company/{company_id}` endpoint):
    - Checks robust error handling when requesting CP history for companies that do not exist, ensuring proper `404` responses.
  - CP Alignment Checks (`/cp/company/{company_id}/alignment` endpoint):
    - Confirms accurate and user-friendly error responses when alignment data for non-existent companies is requested.
  - Performance Comparison (`/cp/company/{company_id}/comparison` endpoint):
    - Ensures the system gracefully handles scenarios where insufficient historical data prevents meaningful CP comparisons. It verifies a clear and informative response is provided in such cases, including the years for which data is available.
- `test_helpers.py`: This testing module ensures the correct behavior of auxiliary helper functions used across the application, such as dynamic dataset selection and data folder handling:
  - Dynamic Data Directory Selection (`get_latest_data_dir`):
    - Validates that the helper correctly identifies and returns the latest data directory based on naming conventions involving date stamps.
    - Ensures robust handling of scenarios where no matching directories exist, explicitly checking that a `FileNotFoundError` is correctly raised to prevent unexpected behavior or incorrect data loading.

To run the tests, follow the given command in the terminal: `pytest`. 