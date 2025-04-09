# Data Dictionary

## Overview
This document provides detailed information about the data structures and fields used in the Corporate Carbon Performance and Assessment API. The API provides endpoints for accessing company data, management quality (MQ) assessments, carbon performance (CP) assessments, and ASCOR data.

## Data Categories

### Company Data
*Core company information and assessment results.*
Basic company attributes and performance metrics, including identifiers, sector, and assessment scores. Data is loaded from the latest company assessment CSV files.

### Management Quality (MQ) Assessments
*Climate management practice evaluations.*
Scoring system (0-5 stars) and methodology for assessing companies' climate risk management and opportunities. Data is loaded from MQ_Assessments_Methodology_*.csv files and includes methodology cycle tracking.

### Carbon Performance (CP) Assessments
*Climate target alignment evaluations.*
Company emissions trajectories and their alignment with various climate scenarios (2025, 2027, 2035, 2050). Data is loaded from CP_Assessments_*.csv files.

### ASCOR Data
*Assessment framework structure.*
Hierarchical evaluation system from country-level down to individual metrics. Data is loaded from ASCOR_assessments_results.xlsx.

### API Response Models
*API response formats.*
Structured data delivery formats including pagination and metadata. All endpoints support pagination with a maximum of 100 items per page.

## Company Data

### Company Base Information
| Field Name | Type | Description | Possible Values | Example |
|------------|------|-------------|-----------------|---------|
| company_id | string | Unique identifier for the company | Alphanumeric string | "exxon_mobil" |
| name | string | Company name | Any valid company name | "Exxon Mobil" |
| sector | string | Industry sector of the company | Any valid sector name | "Oil & Gas" |
| geography | string | Geographical region | Any valid region | "North America" |
| latest_assessment_year | integer | Year of latest assessment | 2023-2024 | 2024 |

### Company Assessment Details
| Field Name | Type | Description | Possible Values | Example |
|------------|------|-------------|-----------------|---------|
| management_quality_score | float | Management Quality Score | 1.0-5.0 | 3.5 |
| carbon_performance_alignment_2035 | string | Alignment with 2035 carbon targets | See Alignment Categories | "Below 2 Degrees" |
| emissions_trend | string | Performance compared to previous year | "Improved", "Declined", "Stable", "Unknown" | "Improved" |

## Management Quality (MQ) Assessments

### MQ Assessment Details
| Field Name | Type | Description | Possible Values | Example |
|------------|------|-------------|-----------------|---------|
| methodology_cycle | integer | Assessment methodology cycle | Positive integer | 5 |
| indicators | object | Scores for individual MQ indicators | Key-value pairs of indicator names and scores | {"governance": 4.2, "targets": 3.8} |

### MQ Trends
| Field Name | Type | Description | Possible Values | Example |
|------------|------|-------------|-----------------|---------|
| sector | string | Sector name | Any valid sector | "Oil & Gas" |
| trends | object | MQ trend scores over time | Key-value pairs of years and scores | {"2023": 3.2, "2024": 3.5} |

## Carbon Performance (CP) Assessments

### CP Assessment Details
| Field Name | Type | Description | Possible Values | Example |
|------------|------|-------------|-----------------|---------|
| carbon_performance_2025 | string | Alignment with 2025 target | See Alignment Categories | "1.5 Degrees" |
| carbon_performance_2027 | string | Alignment with 2027 target | See Alignment Categories | "Below 2 Degrees" |
| carbon_performance_2035 | string | Alignment with 2035 target | See Alignment Categories | "Below 2 Degrees" |
| carbon_performance_2050 | string | Alignment with 2050 target | See Alignment Categories | "Not Aligned" |

### Alignment Categories
- **1.5 Degrees**: Aligned with 1.5°C warming scenario
- **Below 2 Degrees**: Aligned with below 2°C warming scenario
- **Not Aligned**: Not aligned with Paris Agreement goals
- **Paris Pledges**: Aligned with Paris Agreement pledges
- **No or unsuitable disclosure**: Insufficient data for assessment

## ASCOR Data

### Country Data
| Field Name | Type | Description | Possible Values | Example |
|------------|------|-------------|-----------------|---------|
| country | string | Country name | Any valid country name | "United States" |
| assessment_year | integer | Year of assessment | 2023-2024 | 2024 |
| pillars | array | List of assessment pillars | Array of Pillar objects | See Pillar Structure |

### Pillar Structure
| Field Name | Type | Description | Possible Values | Example |
|------------|------|-------------|-----------------|---------|
| name | string | Pillar identifier | "EP", "CP", "CF" | "EP" |
| areas | array | List of assessment areas | Array of Area objects | See Area Structure |

### Area Structure
| Field Name | Type | Description | Possible Values | Example |
|------------|------|-------------|-----------------|---------|
| name | string | Area name | Any valid area name | "Governance" |
| assessment | string | Area assessment | "Exempt", "No", "Not applicable", "Partial", "Yes", "" | "Yes" |
| indicators | array | List of indicators | Array of Indicator objects | See Indicator Structure |

### Indicator Structure
| Field Name | Type | Description | Possible Values | Example |
|------------|------|-------------|-----------------|---------|
| name | string | Indicator name | Any valid indicator name | "Board Oversight" |
| assessment | string | Indicator assessment | "Not Applicable", "No Data", "Not applicable", "Yes", "No", "No data", "Exempt" | "Yes" |
| metrics | array | List of metrics | Array of Metric objects | See Metric Structure |

### Metric Structure
| Field Name | Type | Description | Possible Values | Example |
|------------|------|-------------|-----------------|---------|
| name | string | Metric name | Any valid metric name | "GHG Emissions" |
| value | string | Metric value | Any valid value | "1000 tCO2e" |
| source | object | Source information | Source object | {"source_name": "Company Disclosure"} |

## API Response Models

### CompanyListResponse
| Field | Type | Description | Example |
|-------|------|-------------|---------|
| total | integer | Total number of companies | 100 |
| page | integer | Current page number | 1 |
| per_page | integer | Number of items per page | 10 |
| companies | array | List of company objects | See Company Base Information |

### CompanyHistoryResponse
| Field | Type | Description | Example |
|-------|------|-------------|---------|
| company_id | string | Company identifier | "exxon_mobil" |
| history | array | List of historical assessments | See Company Assessment Details |

### PerformanceComparisonResponse
| Field | Type | Description | Example |
|-------|------|-------------|---------|
| company_id | string | Company identifier | "exxon_mobil" |
| current_year | integer | Current assessment year | 2024 |
| previous_year | integer | Previous assessment year | 2023 |
| latest_mq_score | float | Latest MQ score | 3.5 |
| previous_mq_score | float | Previous MQ score | 3.2 |
| latest_cp_alignment | string | Latest CP alignment | "Below 2 Degrees" |
| previous_cp_alignment | string | Previous CP alignment | "Not Aligned" |

## Usage Notes
- All company IDs are normalized (lowercase, spaces replaced with underscores)
- Assessment years are limited to 2023-2024
- MQ scores range from 1.0 to 5.0
- CP alignment categories are standardized across all target years
- Missing or invalid data points are handled as null values
- All string comparisons are case-insensitive
