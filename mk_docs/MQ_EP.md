# MQ Endpoints

The Management Quality (MQ) endpoints deliver governance-focused climate ratings derived from successive assessment cycles. You can:

1. List the latest MQ scores across all companies, with pagination  
2. Retrieve MQ assessments for a specific research methodology cycle  
3. Fetch MQ score trends over time for all companies in a given sector  

All responses conform to [Pydantic](https://docs.pydantic.dev/latest/) models for strict validation and predictable JSON shapes[^1].

---

## 1. List Latest MQ Assessments

**HTTP Method:** GET  

**Path:** `/v1/mq/latest`  

**Purpose:** Return the most recent MQ assessment for each company, mapping STAR ratings (“0STAR”–“5STAR”) to numeric scores (0.0–5.0).

**Parameters:**

| Name                     | In    | Type                           | Required | Description                                                                                  |
| ------------------------ | ----- | ------------------------------ | -------- | -------------------------------------------------------------------------------------------- |
| `page`                   | query | integer                        | No       | Page number (1-based; default: 1)                                                            |
| `page_size`              | query | integer                        | No       | Items per page (1–100; default: 10)                                                          |
| `Company filters  `    | query | various                        | No       | `geography`, `geography_code`, `sector`, `ca100_focus_company`, `large_medium_classification`, `isins` (string or array), `sedol` (string or array) |
| ``MQ filters``           | query | various                        | No       | `assessment_year` (int), `mq_levels` (array[int]), `level` (array[int])                      |

> **MQ filters detailed:**  
>   **assessment_year**: integer, e.g. `2023`  
>   **mq_levels**: list of specific MQ Level IDs to include (e.g. `1,2,3`)  
>   **level**: list of Overall Management Levels to include  

**Response Format:**  

A `PaginatedMQResponse` object with:

- `total_records` (integer): total matching records  
- `page` (integer): current page number  
- `page_size` (integer): items per page  
- `results` (array of `MQAssessmentDetail`), each containing:  
  - `company_id` (string)  
  - `name` (string)  
  - `sector` (string or null)  
  - `geography` (string or null)  
  - `latest_assessment_year` (integer or null)  
  - `management_quality_score` (float or null)  

```json
{
  "total_records": 150,
  "page": 1,
  "page_size": 10,
  "results": [
    {
      "company_id": "acme_corp",
      "name": "Acme Corporation",
      "sector": "Energy",
      "geography": "United Kingdom",
      "latest_assessment_year": 2024,
      "management_quality_score": 4.0
    },
    ...
  ]
}
```
**Error Responses:**

* **503 Service Unavailable**

    ```json
    { "detail": "MQ dataset is not available." }
    ```

* **422 Unprocessable Entity**
    ```json
    { "detail": "MQ Levels are not valid: [6]" }
    ```

* **500 Internal Server Error**

    ```json
    { "detail": "<error message>" }
    ```  
---

## 2. Retrieve MQ by Methodology Cycle

**HTTP Method:** `GET`  

**Path:** `/v1/mq/methodology/{methodology_id}` 

**Purpose:** Fetch all MQ assessments from a specific research methodology cycle, allowing you to compare governance ratings across versions.

**Parameters:**

| Name              | In    | Type    | Required | Description                                                                     |
|-------------------|-------|---------|----------|---------------------------------------------------------------------------------|
| `methodology_id`  | path  | integer | Yes      | Methodology cycle number (1 to N, where N = number of MQ CSV files detected)   |
| `page`            | query | integer | No       | Page number (1-based; default: 1)                                               |
| `page_size`       | query | integer | No       | Items per page (1–100; default: 10)                                             |
| `Company filters`   | query | various | No       | (See “List Latest MQ Assessments”)                                              |
| `MQ filters`        | query | various | No       | (See above)                                                                     |

**Response Format:** Same `PaginatedMQResponse` schema as above, with `results` showing only records from the specified cycle:

```json
{
  "total_records": 75,
  "page": 1,
  "page_size": 10,
  "results": [
    {
      "company_id": "acme_corp",
      "name": "Acme Corporation",
      "sector": "Energy",
      "geography": "United Kingdom",
      "latest_assessment_year": 2023,
      "management_quality_score": 3.2
    },
    ...
  ]
}
```
**Error Responses:**

* **503 Service Unavailable**: MQ dataset is not available.

    ```json
    { "detail": "MQ dataset is not available." }
    ```

* **422 Unprocessable Entity**: MQ Levels are not valid: [6]

    ```json
    { "detail": "MQ Levels are not valid: [6]" }
    ```

* **500 Internal Server Error**: unexpected processing error.

    ```json
    { "detail": "<error message>" }
    ```  

---

## 3. Retrieve MQ Trends by Sector

**HTTP Method:** `GET`  

**Path:** `/v1/mq/trends/sector/{sector_id}`  

**Purpose:** Return management quality scores over time for all companies within a specific sector, enabling sector-wide trend analysis.

**Parameters:**

| Name            | In    | Type    | Required | Description                                     |
|-----------------|-------|---------|----------|-------------------------------------------------|
| `sector_id`     | path  | string  | Yes      | Sector name (case-insensitive; trimmed)         |
| `page`          | query | integer | No       | Page number (1-based; default: 1)               |
| `page_size`     | query | integer | No       | Items per page (1–100; default: 10)             |
| `Company filters` | query | various | No       | (See “List Latest MQ Assessments”)              |
| `MQ filters`      | query | various | No       | (See above)                                     |

**Response Format:** A `PaginatedMQResponse` with `results` sorted by assessment date for the given sector:

```json
{
  "total_records": 30,
  "page": 1,
  "page_size": 10,
  "results": [
    {
      "company_id": "cement_co",
      "name": "Cement Co",
      "sector": "Cement",
      "geography": "Germany",
      "latest_assessment_year": 2023,
      "management_quality_score": 2.8
    },
    ...
  ]
}
```
**Error Responses:**

- **404 Not Found**  

    ```json
    { "detail": "Company 'unknown_id' not found." }
    ```  

* **500 Internal Server Error**

    ```json
    { "detail": "<error message>" }
    ```  
---

### Design Notes

* STAR ratings are normalized via a fixed mapping (`0STAR` → 0.0, …, `5STAR` → 5.0).
* Each CSV input file maps to a `methodology_cycle`, enabling cycle-based queries.
* Underlying handler logic reuses pagination, filtering, and sanitization from `BaseDataHandler`.
* All MQ endpoints are rate-limited to 100 requests/minute per IP.

---

## Try it out!
<swagger-ui
  src="http://127.0.0.1:8000/openapi.json"
  tags="MQ Endpoints"
  tryItOutEnabled="true"
  docExpansion="none"
/>

[^1]: Pydantic is a Python library for data validation and settings management using Python type annotations. It ensures that all input and output data conform to the defined schema, reducing runtime errors and improving code clarity.