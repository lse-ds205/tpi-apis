# ASCOR Endpoints

The Transition Pathway Initiative’s ASCOR (Assessing Sovereign Climate-related Opportunities and Risks) framework evaluates how national governments plan, manage, and finance their transition to a low-carbon economy. ASCOR assessments cover three pillars:

- __Emissions Pledges (EP)__: The strength and clarity of a country’s formal emissions reduction targets.

- __Carbon Performance (CP)__: Progress against those targets, measuring actual emissions trajectories.

- __Climate Finance (CF)__: Public and private financing commitments supporting climate-related activities.

Assessment data is sourced directly from government documents, financial disclosures, and reputable climate reports. Each country-year combination yields a structured dataset showing high-level pillar scores and detailed sub-indicators, allowing comparisons across nations and over time.

These endpoints let you interact with that data in two ways: one to list all countries with available ASCOR results, and another to fetch the full pillar- and indicator-level assessment for a specific country and year (Emissions Pledges, Carbon Performance, and Climate Finance) for a specific country and assessment year.

---

## 1. List Available Countries

**HTTP Method:** GET

**Path:** `/v1/countries`

**Purpose:** Returns a list of all countries for which ASCOR data is available.

**Response Model:** Returns a JSON object where:

- `countries`: array of strings (country names)

**Example Request:**

```
curl -X GET "https://api.example.com/v1/countries"
```

**Example Response:**

```json
HTTP/1.1 200 OK
{
  "countries": [
    "United Kingdom",
    "France",
    "Germany",
    …
  ]
}
```

**Error Responses:**

* **500 Internal Server Error**: dataset missing or processing error.

    ```json
    { "detail": "<error message>" }
    ```

---

## 2. Retrieve Country Assessment Data

**HTTP Method:** GET

**Path:** `/v1/country-data/{country}/{assessment_year}`

**Purpose:** Fetch the detailed ASCOR assessment for a specific country and year, including all three pillars (EP, CP, CF) with nested areas, indicators, and metrics.

**Response Model:** This endpoint returns a JSON object defined by the `CountryDataResponse` [Pydantic](https://docs.pydantic.dev/latest/) model[^1], which includes:

- `country`: string
- `assessment_year`: integer
- `pillars`: array of objects, each with:
    - `name`: “EP” | “CP” | “CF”
    - `areas`: array of objects, each with:
        - `name`: string (e.g. “EP.1”)
        - `assessment`: string (“Good”, “Partial”, etc.)
        - `indicators`: array of objects, each with:
            - `name`: string (e.g. “EP.1.1”)
            - `assessment`: string
            - `metrics`: array of metric objects:
                - `name`: string (e.g. “EP.1.1.1”)
                - `value`: string (e.g. “45%”)
            - `source`:
                - `source_name`: string

| Parameter         | In   | Type   | Required | Description                            |
| ----------------- | ---- | ------ | -------- | -------------------------------------- |
| `country`         | path | string | Yes      | Country name (case-insensitive)        |
| `assessment_year` | path | int    | Yes      | Year of assessment (e.g. 2023 or 2024) |

**Example Request:**

```
curl -X GET "https://api.example.com/v1/country-data/France/2023"
```

**Example Response:**

```json
HTTP/1.1 200 OK
{
  "country": "france",
  "assessment_year": 2023,
  "pillars": [
    {
      "name": "EP",
      "areas": [
        {
          "name": "EP.1",
          "assessment": "Good",
          "indicators": [
            {
              "name": "EP.1.1",
              "assessment": "Good",
              "metrics": [
                { "name": "EP.1.1.1", "value": "45%", "source": { "source_name": "Report" } }
              ],
              "source": { "source_name": "Source 1" }
            },
            …
          ]
        },
        …
      ]
    },
    { "name": "CP", … },
    { "name": "CF", … }
  ]
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

### Design Notes

* Country names are matched case-insensitively and trimmed of whitespace.
* Assessment year must match the year of the `Assessment date` column after parsing.
* The endpoint always returns all three pillars in a single structured payload.
* The `/v1/country-data/{country}/{assessment_year}` route is decorated with `@limiter.limit("100/minute")` to ensure fairness.

--- 

## Try it out!
<swagger-ui
  src="http://127.0.0.1:8000/openapi.json"
  tags="Ascor Endpoints"
  tryItOutEnabled="true"
  docExpansion="none"
/>

[^1]: Pydantic is a Python library for data validation and settings management using Python type annotations. It ensures that all input and output data conform to the defined schema, reducing runtime errors and improving code clarity.