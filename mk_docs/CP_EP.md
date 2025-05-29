# CP Endpoints

The Carbon Performance (CP) endpoints expose company-level alignment against decadal emissions targets (2025, 2027, 2035, 2050). Use these routes to:

1. Retrieve the latest CP scores for every company in a paginated list
2. Fetch the full time-series of CP assessments for a single company
3. Get a simple year-to-alignment map for a company’s most recent assessment
4. Compare the two most recent CP assessments for a company

All responses conform to [Pydantic](https://docs.pydantic.dev/latest/) models for strict validation and predictable JSON shapes[^1].

---

## 1. List Companies

**HTTP Method:** GET

**Path:** /v1/cp/latest

**Purpose:** Return the most recent CP assessment for each company, with alignment status for key target years.

**Parameters:**

| Name            | In    | Type                      | Required | Description                                                                   |
| --------------- | ----- | ------------------------- | -------- | ----------------------------------------------------------------------------- |
| `page`          | query | integer                   | No       | Page number (1-based; default: 1)                                             |
| `page_size`     | query | integer                   | No       | Results per page (1–100; default: 10)                                         |
| *Company filters* (see below) | query | various | No       | Optional filters (geography, sector, CA100, ISIN, SEDOL, etc.) to narrow list |

> **Company filters:**  
>   `geography`, `geography_code`, `sector`, `ca100_focus_company`, `large_medium_classification`, `isins` (string or array), `sedol` (string or array)

**Response Format:** An array of `CPAssessmentDetail` objects, each with:

- `company_id` (string)  
- `name` (string)  
- `sector` (string or null)  
- `geography` (string or null)  
- `latest_assessment_year` (integer)  
- `carbon_performance_2025` (string)  
- `carbon_performance_2027` (string)  
- `carbon_performance_2035` (string)  
- `carbon_performance_2050` (string)  

```json
[
  {
    "company_id": "acme_corp",
    "name": "Acme Corporation",
    "sector": "Energy",
    "geography": "United Kingdom",
    "latest_assessment_year": 2024,
    "carbon_performance_2025": "Aligned",
    "carbon_performance_2027": "Partially Aligned",
    "carbon_performance_2035": "Aligned",
    "carbon_performance_2050": "Not Aligned"
  },
  ...
]
``` 

**Error Responses:**  

* **500 Internal Server Error**  

    ```json
    { "detail": "<error message>" }
    ```

---

## 2. Retrieve Company CP History

**HTTP Method:** `GET`  

**Path:** `/v1/cp/company/{company_id}`

**Purpose:** Return every CP assessment ever recorded for the given company, across all cycles.

**Parameters:**

| Name        | In   | Type   | Required | Description                                     |
|-------------|------|--------|----------|-------------------------------------------------|
| `company_id` | path | string | Yes      | Normalized company identifier (e.g. `acme_corp`) |

You may also apply the same Company filters as in the “List” endpoint to further narrow results.

**Response Format:** An array of `CPAssessmentDetail` objects (same fields as above), ordered by assessment date.

```json
[
  {
    "company_id": "acme_corp",
    "name": "Acme Corporation",
    "sector": "Energy",
    "geography": "United Kingdom",
    "latest_assessment_year": 2023,
    "carbon_performance_2025": "Partially Aligned",
    "carbon_performance_2027": "Not Aligned",
    "carbon_performance_2035": "Partially Aligned",
    "carbon_performance_2050": "Not Aligned"
  },
  {
    "company_id": "acme_corp",
    "name": "Acme Corporation",
    "sector": "Energy",
    "geography": "United Kingdom",
    "latest_assessment_year": 2024,
    "carbon_performance_2025": "Aligned",
    "carbon_performance_2027": "Partially Aligned",
    "carbon_performance_2035": "Aligned",
    "carbon_performance_2050": "Not Aligned"
  }
]
```

**Error Responses:**

* **404 Not Found**: no data for given country/year.

    ```json
    { "detail": "No data found for country=Belgium in year=2024" }
    ```

* **500 Internal Server Error**: unexpected processing error.

    ```json
    { "detail": "Unexpected server error." }
    ```

---

## 3. Retrieve Company CP Alignment

**HTTP Method:** `GET`  

**Path:** `/v1/cp/company/{company_id}/alignment`

**Purpose:** Fetch the company's latest alignment status for each target year as a simple key–value map.

**Parameters:**

| Name         | In   | Type   | Required | Description                                      |
|--------------|------|--------|----------|--------------------------------------------------|
| `company_id` | path | string | Yes      | Normalized company identifier (e.g. `acme_corp`) |

You may also apply the same Company filters as in the “List” endpoint to further narrow results.

**Response Format:** A JSON object with keys for each target year:

```json
{
  "2025": "Aligned",
  "2027": "Partially Aligned",
  "2035": "Aligned",
  "2050": "Not Aligned"
}
```

**Error Responses:**

* **404 Not Found**: no data for given country/year.

    ```json
    { "detail": "No data found for country=Belgium in year=2024" }
    ```

* **500 Internal Server Error**: unexpected processing error.

    ```json
    { "detail": "Unexpected server error." }
    ```
--- 

## 4. Compare Company CP Performance

**HTTP Method:** `GET`  

**Path:** `/v1/cp/company/{company_id}/comparison`

**Purpose:** Compare the two most recent CP assessments for a company and show changes in alignment.

**Parameters:** Same as [Retrieve Company CP History](#2-retrieve-company-cp-history).

| Name         | In   | Type   | Required | Description                                      |
|--------------|------|--------|----------|--------------------------------------------------|
| `company_id` | path | string | Yes      | Normalized company identifier (e.g. `acme_corp`) |

You may also apply the same Company filters as in the “List” endpoint to further narrow results.

**Response Format:** Returns one of two models:

* **CPComparisonResponse** when ≥2 records exist:

    ```json
    {
      "company_id": "acme_corp",
      "current_year": 2024,
      "previous_year": 2023,
      "latest_cp_2025": "Aligned",
      "previous_cp_2025": "Partially Aligned",
      "latest_cp_2035": "Aligned",
      "previous_cp_2035": "Partially Aligned"
    }
    ```

* **PerformanceComparisonInsufficientDataResponse** when <2 records:

    ```json
    {
      "company_id": "acme_corp",
      "message": "Only one record exists for 'acme_corp', so performance comparison is not available",
      "available_assessment_years": [2024]
    }
    ```

**Error Responses:**

* **404 Not Found**: company not found.

    ```json
    { "detail": "Company 'unknown_id' not found." }
    ```

* **500 Internal Server Error**: unexpected processing error.

    ```json
    { "detail": "<error message>" }
    ```
---

### Design Notes

* The latest endpoint is rate-limited more strictly (2 calls/minute) because it scans the full dataset for each company.
* All company filters (`geography`, `sector`, `isins`, etc.) apply to history and list endpoints.
* Paths use normalized company IDs (lowercase, underscores) to ensure URL safety.
* Responses rely on the `CPHandler` logic to combine multiple CSV cycles and always validate against Pydantic schemas.

---

<swagger-ui
  src="http://127.0.0.1:8000/openapi.json"
  tags="CP Endpoints"
  tryItOutEnabled="true"
  docExpansion="none"
/>

[^1]: Pydantic is a Python library for data validation and settings management using Python type annotations. It ensures that all input and output data conform to the defined schema, reducing runtime errors and improving code clarity.