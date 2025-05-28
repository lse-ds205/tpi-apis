# Company Endpoints

These endpoints provide corporate climate assessments combining Management Quality (MQ) and Carbon Performance (CP) metrics for publicly listed companies. You can:

1. List all companies with their latest assessment year and basic info  
2. Retrieve the latest MQ & CP scores for a single company  
3. Fetch the full historical record of MQ & CP assessments for one company  
4. Compare the two most recent assessment cycles for a company  

All responses are validated against [Pydantic](https://docs.pydantic.dev/latest/) models to ensure consistent data shapes and reduce integration errors[^1].

---

## 1. List Companies

**HTTP Method:** GET  

**Path:** `/v1/companies`  

**Purpose:** Return a paginated list of companies including their unique ID, name, sector, geography, and latest assessment year.

**Parameters:**

| Name                       | In    | Type    | Required | Description                                                                 |
| -------------------------- | ----- | ------- | -------- | --------------------------------------------------------------------------- |
| `page`                     | query | int     | No       | Page number (1-based; default: 1)                                           |
| `per_page`                 | query | int     | No       | Results per page (1–100; default: 10)                                       |
| `geography`                | query | string  | No       | Filter by country or region name                                            |
| `geography_code`           | query | string  | No       | Filter by ISO geography code (e.g. "USA")                                    |
| `sector`                   | query | string  | No       | Filter by industry sector (e.g. "Cement")                                    |
| `ca100_focus_company`      | query | boolean | No       | `true` to include only CA100 focus companies, `false` to exclude them       |
| `large_medium_classification` | query | string  | No       | Filter by size classification ("Large" or "Medium")                          |
| `isins`                    | query | string or array of strings | No | Filter by one or more ISIN identifiers                                       |
| `sedol`                    | query | string or array of strings | No | Filter by one or more SEDOL identifiers                                      |

**Response Format:** Returns a `CompanyListResponse` object:

- `total`: integer — total number of matching companies  
- `page`: integer — current page number  
- `per_page`: integer — items per page  
- `companies`: array of objects, each with:
    - `company_id`: string
    - `name`: string
    - `sector`: string or null
    - `geography`: string or null
    - `latest_assessment_year`: integer or null

```json
{
  "total": 234,
  "page": 1,
  "per_page": 10,
  "companies": [
    {
      "company_id": "acme_corp",
      "name": "Acme Corporation",
      "sector": "Energy",
      "geography": "United Kingdom",
      "latest_assessment_year": 2024
    },
    ...
  ]
}
```

**Error Responses:**  

* **503 Service Unavailable**  

    ```json
    { "detail": "Company dataset is not loaded. Please ensure the data file exists." }
    ```  

* **500 Internal Server Error**  

    ```json
    { "detail": "<error message>" }
    ```

---

## 2. Retrieve Company Details

**HTTP Method:** GET  

**Path:** `/v1/company/{company_id}`  

**Purpose:** Fetch the latest MQ score, 2035 CP alignment, and emissions trend for the specified company.

**Parameters:**

| Name         | In   | Type   | Required | Description                                    |
| ------------ | ---- | ------ | -------- | ---------------------------------------------- |
| `company_id` | path | string | Yes      | Normalized company identifier (e.g. "acme_corp") |

**Response Format:** Returns a `CompanyDetail` object:

- `company_id`: string  
- `name`: string  
- `sector`: string or null  
- `geography`: string or null  
- `latest_assessment_year`: integer or null  
- `management_quality_score`: float or null  
- `carbon_performance_alignment_2035`: string or null  
- `emissions_trend`: string or null

```json
{
  "company_id": "acme_corp",
  "name": "Acme Corporation",
  "sector": "Energy",
  "geography": "United Kingdom",
  "latest_assessment_year": 2024,
  "management_quality_score": 3.5,
  "carbon_performance_alignment_2035": "Aligned",
  "emissions_trend": "Improving"
}
```

**Error Responses:**  

* **404 Not Found**  

    ```json
    { "detail": "Company 'unknown_id' not found." }
    ```  

* **500 Internal Server Error**  

    ```json
    { "detail": "<error message>" }
    ```

---

## 3. Retrieve Company History

**HTTP Method:** GET  

**Path:** `/v1/company/{company_id}/history`  

**Purpose:** Return a chronological list of all past MQ and CP assessments for the company.

**Parameters:** Same as [Retrieve Company Details](#2-retrieve-company-details).

**Response Format:** Returns a `CompanyHistoryResponse` object:

- `company_id`: string  
- `history`: array of `CompanyDetail` objects (one per assessment cycle)

```json
{
  "company_id": "acme_corp",
  "history": [
    {
      "company_id": "acme_corp",
      "name": "Acme Corporation",
      "sector": "Energy",
      "geography": "United Kingdom",
      "latest_assessment_year": 2023,
      "management_quality_score": 3.2,
      "carbon_performance_alignment_2035": "Partially Aligned",
      "emissions_trend": "Stable"
    },
    {
      "company_id": "acme_corp",
      "name": "Acme Corporation",
      "sector": "Energy",
      "geography": "United Kingdom",
      "latest_assessment_year": 2024,
      "management_quality_score": 3.5,
      "carbon_performance_alignment_2035": "Aligned",
      "emissions_trend": "Improving"
    }
  ]
}
```

**Error Responses:**  

- **404 Not Found**  

    ```json
    { "detail": "No history found for company 'unknown_id'." }
    ```  

- **503 Service Unavailable**  

    ```json
    { "detail": "Column 'MQ Assessment Date' not found in dataset. Check CSV structure." }
    ```  

- **500 Internal Server Error**  

    ```json
    { "detail": "<error message>" }
    ```

---

## 4. Compare Company Performance

**HTTP Method:** GET  

**Path:** `/v1/company/{company_id}/performance-comparison`  

**Purpose:** Compare the two most recent MQ & CP assessments for the specified company to show year-over-year change.

**Parameters:** Same as **Retrieve Company Details**.

**Response Format:** Returns either:

- `PerformanceComparisonResponse` object when at least two records exist:

```json
    {
      "company_id": "acme_corp",
      "current_year": 2024,
      "previous_year": 2023,
      "latest_mq_score": 3.5,
      "previous_mq_score": 3.2,
      "latest_cp_alignment": "Aligned",
      "previous_cp_alignment": "Partially Aligned"
    }
```

or

- `PerformanceComparisonInsufficientDataResponse` when fewer than two assessments exist:

```json
  {
    "company_id": "acme_corp",
    "message": "Only one record exists for 'acme_corp', so performance comparison is not possible.",
    "available_assessment_years": [2024]
  }
```

**Error Responses:**  

- **404 Not Found**  

    ```json
    { "detail": "Company 'unknown_id' not found." }
    ```  

- **500 Internal Server Error**  

    ```json
    { "detail": "<error message>" }
    ```

---

### Design Notes

- All endpoints default to the latest available assessment unless you explicitly request history or comparison.  
- Company identifiers are normalized (lowercase, underscores) for URL safety.  
- Filtering on list routes uses the same Pydantic-based `CompanyFilters` model as other endpoints.  
- Rate-limited to 100 requests per minute per IP by default.

[^1]: Pydantic is a Python library for data validation and settings management using Python type annotations. It ensures that all input and output data conform to the defined schema, reducing runtime errors and improving code clarity.
